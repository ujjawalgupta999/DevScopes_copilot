from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import hmac
import hashlib
import os
from dotenv import load_dotenv
from agent import DevSecOpsAgent

load_dotenv()

app = FastAPI(title="DevSecOps Copilot")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")


def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature header")

    hash_object = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")


def trigger_ai_review(repo_name: str, pr_number: int, commit_id: str):
    try:
        agent = DevSecOpsAgent()
        agent.review_pull_request(repo_name, pr_number, commit_id)
    except Exception as e:
        print(f"❌ AI Review Failed: {e}")


@app.post("/webhook/pr-review")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_body = await request.body()
    signature_header = request.headers.get("x-hub-signature-256")

    # 1. Verify GitHub Signature
    verify_signature(payload_body, signature_header)

    # 2. Extract Data
    payload = await request.json()

    if "pull_request" in payload:
        action = payload.get("action")
        pr_number = payload["pull_request"]["number"]
        repo_name = payload["repository"]["full_name"]
        commit_id = payload["pull_request"]["head"]["sha"]

        # 3. Only review newly opened or updated PRs
        if action in ["opened", "synchronize"]:
            print(f"\n🔔 Webhook received! Action: {action} on PR #{pr_number}")
            background_tasks.add_task(
                trigger_ai_review, repo_name, pr_number, commit_id
            )
            return {"status": "success", "message": "AI review queued"}

    return {"status": "ignored", "message": "Not a valid PR action or ping event"}
