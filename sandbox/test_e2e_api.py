import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_e2e():
    import time
    unique_email = f"sahayya_e2e_{int(time.time())}@aura.ai"
    print("=== AURA End-to-End API Integration Verification ===")
    async with httpx.AsyncClient(timeout=15.0) as client:
        # 1. Health Check
        res = await client.get(f"{BASE_URL}/health")
        print("1. Health Endpoint Response:", res.status_code, res.json())
        assert res.status_code == 200, "Health check failed"

        # 2. User Registration
        reg_payload = {
            "full_name": "Sahayya Tester",
            "email": unique_email,
            "password": "Password99",
            "tier_choice": "FREEMIUM"
        }
        res_reg = await client.post(f"{BASE_URL}/api/v1/auth/register", json=reg_payload)
        print("2. User Registration Response:", res_reg.status_code, res_reg.json())
        assert res_reg.status_code == 200, "Registration failed"
        token = res_reg.json()["token"]

        # 3. User Login
        login_payload = {
            "email": unique_email,
            "password": "Password99"
        }

        res_login = await client.post(f"{BASE_URL}/api/v1/auth/login", json=login_payload)
        print("3. User Login Response:", res_login.status_code, res_login.json())
        assert res_login.status_code == 200, "Login failed"

        # 4. Context File Upload Attachment
        files = {'file': ('research_spec.pdf', b'%PDF-1.4 Mock document content for RAG testing', 'application/pdf')}
        data = {'user_email': unique_email}
        res_upload = await client.post(f"{BASE_URL}/api/v1/context/upload", files=files, data=data)
        print("4. Context File Upload Response:", res_upload.status_code, res_upload.json())
        assert res_upload.status_code == 200, "Context upload failed"
        att_data = res_upload.json()

        # 5. Submit Research Task with Attachment
        task_payload = {
            "user_prompt": "Compare PostgreSQL pgvector HNSW vs Pinecone vector search for AI agents",
            "user_email": unique_email,
            "top_k": 5,
            "hybrid_search": True,
            "claim_verification": True,
            "attachments": [
                {
                    "file_id": att_data["file_id"],
                    "name": att_data["filename"],
                    "size": att_data["file_size_bytes"],
                    "type": "PDF Document"
                }
            ]
        }
        res_task = await client.post(f"{BASE_URL}/api/v1/task", json=task_payload)
        print("5. Research Task Dispatch Response:", res_task.status_code)
        assert res_task.status_code in (200, 201), f"Task dispatch failed with status {res_task.status_code}"
        task_res_json = res_task.json()

        task_id = task_res_json["task_id"]
        print("   Task ID Generated:", task_id)
        print("   Synthesized Answer Snippet:", task_res_json["synthesized_answer"][:120], "...")

        # 6. Bookmark / Save Chat Session in Database
        save_payload = {
            "task_id": task_id,
            "is_saved": True,
            "user_email": unique_email,
            "user_prompt": task_payload["user_prompt"],
            "synthesized_answer": task_res_json["synthesized_answer"]
        }
        res_save = await client.post(f"{BASE_URL}/api/v1/history/save", json=save_payload)
        print("6. Toggle Save Chat Session Response:", res_save.status_code, res_save.json())
        assert res_save.status_code == 200, "Save chat failed"

        # 7. Fetch Saved Research Chats from Database
        res_saved_chats = await client.get(f"{BASE_URL}/api/v1/history/saved?email={unique_email}")

        print("7. Fetch Saved Research Chats Response:", res_saved_chats.status_code, "Found Count:", len(res_saved_chats.json()))
        assert res_saved_chats.status_code == 200 and len(res_saved_chats.json()) > 0, "Fetch saved chats failed"

        print("=== ALL END-TO-END TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(test_e2e())
