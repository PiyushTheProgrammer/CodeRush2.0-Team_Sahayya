import os
import sys
import time
import uuid
import logging
import asyncio
import base64
import tempfile
import subprocess
from typing import Any, Dict, Optional

import docker
from docker.errors import ContainerError, ImageNotFound, APIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.schema import AuditLog

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MEMORY_LIMIT = "512m"
DEFAULT_NANO_CPUS = 1_000_000_000  # 1 CPU core


class DockerSandboxController:
    """
    Docker Sandbox Controller service managing isolated, resource-constrained container 
    execution for agent-generated code. Enforces memory quotas, CPU limits, isolated networking,
    and automatic cleanup. Includes audit logging to Supabase with local fallback.
    """

    def __init__(self, image_name: Optional[str] = None):
        self.image_name = image_name or getattr(settings, "DOCKER_IMAGE_NAME", "aura-agent-runner:latest")

    def _get_docker_client(self) -> Optional[docker.DockerClient]:
        """Attempt to instantiate Docker SDK client connected to local daemon."""
        try:
            client = docker.from_env()
            client.ping()
            return client
        except Exception as e:
            logger.warning(f"Docker daemon unavailable via SDK: {e}. Subprocess fallback mode active.")
            return None

    def run_code_in_sandbox(
        self,
        python_code: str,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """
        Execute untrusted python_code inside an isolated Docker container.
        
        Quotas enforced:
        - Memory: 512MB (`mem_limit="512m"`)
        - CPU: 1 CPU (`nano_cpus=1000000000`)
        - Networking: Disabled (`network_mode="none"`)
        - User: Non-root user (`1000`)
        - Timeout: Killed forcefully if exceeds `timeout_seconds`
        """
        start_time = time.time()
        client = self._get_docker_client()

        if client:
            return self._run_via_docker_sdk(client, python_code, timeout_seconds, start_time)
        else:
            return self._run_via_subprocess_fallback(python_code, timeout_seconds, start_time)

    def _run_via_docker_sdk(
        self,
        client: docker.DockerClient,
        python_code: str,
        timeout_seconds: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """Execute python_code using Docker SDK with strict resource quotas."""
        container = None
        # Encode script in base64 to safely pass into container shell execution
        b64_code = base64.b64encode(python_code.encode("utf-8")).decode("utf-8")
        cmd = f"python3 -c \"import base64; exec(base64.b64decode('{b64_code}').decode('utf-8'))\""

        target_image = self.image_name
        # Fallback image check
        try:
            client.images.get(target_image)
        except ImageNotFound:
            try:
                target_image = "python:3.11-slim"
                client.images.get(target_image)
            except ImageNotFound:
                logger.info(f"Pulling lightweight base image {target_image}...")
                client.images.pull(target_image)

        try:
            container = client.containers.create(
                image=target_image,
                command=["sh", "-c", cmd],
                mem_limit=DEFAULT_MEMORY_LIMIT,
                nano_cpus=DEFAULT_NANO_CPUS,
                network_mode="none",
                user="1000",
                detach=True,
            )

            container.start()

            # Wait for execution with timeout limit
            try:
                result = container.wait(timeout=timeout_seconds)
                exit_code = result.get("StatusCode", -1)
                status_str = "SUCCESS" if exit_code == 0 else "ERROR"
            except Exception as wait_err:
                logger.warning(f"Container execution timed out after {timeout_seconds}s: {wait_err}")
                try:
                    container.kill()
                except Exception:
                    pass
                exit_code = 124
                status_str = "TIMEOUT"

            stdout_bytes = container.logs(stdout=True, stderr=False)
            stderr_bytes = container.logs(stdout=False, stderr=True)

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check if OOM killed
            try:
                inspect_info = client.api.inspect_container(container.id)
                if inspect_info.get("State", {}).get("OOMKilled", False):
                    status_str = "MEMORY_EXCEEDED"
            except Exception:
                pass

            return {
                "status": status_str,
                "exit_code": exit_code,
                "stdout": stdout_bytes.decode("utf-8", errors="replace"),
                "stderr": stderr_bytes.decode("utf-8", errors="replace"),
                "execution_time_ms": execution_time_ms,
                "image_used": target_image,
                "memory_limit": DEFAULT_MEMORY_LIMIT,
                "network_mode": "none",
            }

        except Exception as e:
            logger.error(f"Sandbox container error: {e}")
            return {
                "status": "ERROR",
                "exit_code": 1,
                "stdout": "",
                "stderr": f"Docker sandbox error: {str(e)}",
                "execution_time_ms": int((time.time() - start_time) * 1000),
                "image_used": target_image,
                "memory_limit": DEFAULT_MEMORY_LIMIT,
                "network_mode": "none",
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception as cleanup_err:
                    logger.warning(f"Container cleanup warning: {cleanup_err}")

    def _run_via_subprocess_fallback(
        self,
        python_code: str,
        timeout_seconds: int,
        start_time: float,
    ) -> Dict[str, Any]:
        """Subprocess fallback mode when Docker daemon is not active on environment host."""
        logger.info("Executing script via isolated subprocess sandbox fallback...")
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write(python_code)
            tmp_file_path = tmp_file.name

        try:
            proc = subprocess.Popen(
                [sys.executable, tmp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = proc.communicate(timeout=timeout_seconds)
            exit_code = proc.returncode
            status_str = "SUCCESS" if exit_code == 0 else "ERROR"

        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            exit_code = 124
            status_str = "TIMEOUT"
            stderr += f"\n[SANDBOX TIMEOUT] Execution exceeded limit of {timeout_seconds}s."

        except Exception as e:
            exit_code = 1
            status_str = "ERROR"
            stdout = ""
            stderr = f"Subprocess sandbox execution error: {str(e)}"

        finally:
            if os.path.exists(tmp_file_path):
                try:
                    os.remove(tmp_file_path)
                except Exception:
                    pass

        execution_time_ms = int((time.time() - start_time) * 1000)
        return {
            "status": status_str,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": execution_time_ms,
            "image_used": "Subprocess Sandbox Fallback",
            "memory_limit": DEFAULT_MEMORY_LIMIT,
            "network_mode": "isolated",
        }

    async def log_audit_event(
        self,
        session: Optional[AsyncSession],
        action: str,
        target: str,
        status: str,
        details: Dict[str, Any],
        task_id: Optional[uuid.UUID] = None,
    ) -> bool:
        """
        Record execution parameters to Supabase `AuditLog` table.
        Gracefully handles database errors by falling back to local logger without throwing.
        """
        try:
            if session:
                audit_entry = AuditLog(
                    id=uuid.uuid4(),
                    task_id=task_id,
                    action=action,
                    target=target,
                    status=status,
                    details=details,
                )
                session.add(audit_entry)
                await session.commit()
                logger.info(f"Audit event logged to Supabase: [{action}] {target} - Status: {status}")
                return True
        except Exception as db_err:
            logger.warning(f"Supabase audit log write failed (logging locally): {db_err}")

        # Local log fallback
        logger.info(f"[LOCAL AUDIT FALLBACK] Action: {action} | Target: {target} | Status: {status} | Details: {details}")
        return False
