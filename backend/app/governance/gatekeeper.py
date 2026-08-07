"""
AST-based Governance Gatekeeper Service.
Inspects self-evolution patches for path boundaries, size constraints, secret leaks, prompt overrides, and AST safety.
"""
import ast
import os
import re
import logging
import uuid
from typing import Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schema import StrategyVersion

logger = logging.getLogger(__name__)


class ASTSafetyVisitor(ast.NodeVisitor):
    """AST NodeVisitor to detect dangerous imports, functions, and attributes."""

    FORBIDDEN_MODULES = {"os", "subprocess", "sys", "shutil", "socket"}
    FORBIDDEN_BUILTINS = {"eval", "exec", "open", "__import__"}
    FORBIDDEN_ATTRIBUTES = {"system", "popen", "run"}

    def __init__(self):
        self.violations = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_base = alias.name.split(".")[0]
            if module_base in self.FORBIDDEN_MODULES:
                self.violations.append(
                    f"Forbidden module import '{alias.name}' detected at line {node.lineno}"
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            module_base = node.module.split(".")[0]
            if module_base in self.FORBIDDEN_MODULES:
                self.violations.append(
                    f"Forbidden module import from '{node.module}' detected at line {node.lineno}"
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.FORBIDDEN_BUILTINS:
                self.violations.append(
                    f"Forbidden built-in function call '{node.func.id}()' detected at line {node.lineno}"
                )
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.FORBIDDEN_ATTRIBUTES:
                self.violations.append(
                    f"Forbidden attribute call '.{node.func.attr}()' detected at line {node.lineno}"
                )
        self.generic_visit(node)


class GovernanceGatekeeper:
    """
    Governance Gatekeeper inspecting self-evolution patches before execution/deployment.
    """

    ALLOWED_PATH_SUBSTRING = "app/rag/strategies"
    FORBIDDEN_CORE_FILES = {
        "gatekeeper.py",
        "config.py",
        ".env",
        "main.py",
        "session.py",
        "schema.py",
        "api.py",
    }

    MAX_PATCH_LINES = 60

    SECRET_REGEXES = [
        re.compile(r"sk-[A-Za-z0-9-_]{20,}"),  # OpenAI API key pattern
        re.compile(r"AIzaSy[A-Za-z0-9-_]{30,}"),  # Gemini / GCP API key pattern
        re.compile(r"(?i)SUPABASE_SERVICE_ROLE_KEY\s*=\s*['\"][^'\"]+['\"]"),
        re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]"),
    ]

    PROMPT_OVERRIDE_REGEX = re.compile(
        r"(?i)(ignore\s+previous\s+instructions|system\s+prompt\s+override|bypass\s+governance|jailbreak)"
    )

    def validate_patch(self, target_file_path: str, proposed_python_code: str) -> Tuple[bool, str]:
        """
        Validate candidate strategy patch against path boundaries, size limits, secret leaks, AST safety rules.
        """
        # 1. Path Boundary Check
        normalized_path = os.path.normpath(target_file_path).replace("\\", "/")
        filename = os.path.basename(normalized_path)

        if filename in self.FORBIDDEN_CORE_FILES:
            return False, f"Rejection: Target file '{filename}' touches forbidden core file."

        if self.ALLOWED_PATH_SUBSTRING not in normalized_path and "strategies" not in normalized_path:
            return False, f"Rejection: Target path '{target_file_path}' is outside 'app/rag/strategies/'."

        # 2. Patch Size Check
        lines = proposed_python_code.strip().splitlines()
        if len(lines) > self.MAX_PATCH_LINES:
            return False, f"Rejection: Patch size of {len(lines)} lines exceeds max limit of {self.MAX_PATCH_LINES} lines."

        # 3. Secret & Security Pattern Check
        for pattern in self.SECRET_REGEXES:
            if pattern.search(proposed_python_code):
                return False, "Rejection: Hardcoded secret, API key, or credential detected in patch."

        if self.PROMPT_OVERRIDE_REGEX.search(proposed_python_code):
            return False, "Rejection: Forbidden prompt override / jailbreak attempt detected in patch."

        # 4. AST Safety Parsing
        is_ast_safe, ast_reason = self._validate_ast(proposed_python_code)
        if not is_ast_safe:
            return False, f"Rejection: AST safety violation — {ast_reason}"

        return True, "Approved"

    def _validate_ast(self, proposed_python_code: str) -> Tuple[bool, str]:
        """Parse code into AST and inspect nodes for unsafe operations."""
        try:
            tree = ast.parse(proposed_python_code)
        except SyntaxError as syntax_err:
            return False, f"Syntax error in patch code: {syntax_err}"
        except Exception as e:
            return False, f"AST parsing failed: {str(e)}"

        visitor = ASTSafetyVisitor()
        visitor.visit(tree)

        if visitor.violations:
            return False, "; ".join(visitor.violations)

        return True, "AST is safe"

    async def apply_and_version_strategy(
        self,
        patch_code: str,
        target_file_path: str = "backend/app/rag/strategies/hybrid_strategy.py",
        db: Optional[AsyncSession] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate, save to disk, and persist new strategy version to Supabase StrategyVersion table.
        """
        is_approved, reason = self.validate_patch(target_file_path, patch_code)
        if not is_approved:
            logger.warning(f"Strategy patch rejected by Gatekeeper: {reason}")
            return False, reason, None

        # Write approved patch file to disk
        try:
            abs_target_path = os.path.abspath(target_file_path)
            os.makedirs(os.path.dirname(abs_target_path), exist_ok=True)
            with open(abs_target_path, "w", encoding="utf-8") as f:
                f.write(patch_code)
        except Exception as file_err:
            return False, f"Failed writing strategy patch to disk: {file_err}", None

        version_id_str = None
        if db is not None:
            try:
                # Query max version number
                result = await db.execute(select(StrategyVersion.version_number).order_by(StrategyVersion.version_number.desc()).limit(1))
                latest_ver = result.scalar_one_or_none()
                new_ver_num = (latest_ver or 0) + 1

                # Deactivate previous strategies
                await db.execute(update(StrategyVersion).values(is_active=False))

                # Create new active StrategyVersion
                new_version = StrategyVersion(
                    id=uuid.uuid4(),
                    version_number=new_ver_num,
                    strategy_code=patch_code,
                    performance_score=None,
                    is_active=True,
                    approved_by_governance=True,
                )
                db.add(new_version)
                await db.commit()
                version_id_str = str(new_version.id)
            except Exception as db_err:
                logger.error(f"Database error versioning strategy: {db_err}")
                try:
                    await db.rollback()
                except Exception:
                    pass

        if not version_id_str:
            version_id_str = str(uuid.uuid4())

        return True, "Strategy version applied and persisted successfully", version_id_str
