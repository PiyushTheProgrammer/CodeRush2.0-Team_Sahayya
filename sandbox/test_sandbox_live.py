import httpx
import json

def test_sandbox_execution():
    url = "http://localhost:8000/api/v1/sandbox/run"
    
    python_code = """import time
import getpass
import platform

print("=== AURA SANDBOX LIVE EXECUTION TEST ===")
print(f"User: {getpass.getuser()}")
print(f"OS Platform: {platform.platform()}")
print(f"Python Version: {platform.python_version()}")

numbers = [x**2 for x in range(1, 10)]
print(f"Calculated Squares inside Sandbox: {numbers}")
"""

    payload = {
        "code": python_code,
        "timeout_seconds": 10
    }

    print("Sending code execution request to AURA Sandbox Endpoint...")
    response = httpx.post(url, json=payload, timeout=15)
    print(f"Response Status Code: {response.status_code}\n")
    print("=== SANDBOX EXECUTION OUTPUT ===")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_sandbox_execution()
