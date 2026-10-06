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
    # 1. Read event header and raw body
    event_type = request.headers.get("x-github-event", "unknown")
    signature_header = request.headers.get("x-hub-signature-256")
    payload_body = await request.body()

    print(f"\n📡 Incoming GitHub Event: [{event_type}]")

    # 2. Cryptographic verification
    verify_signature(payload_body, signature_header)

    # 3. Parse JSON
    payload = await request.json()

    # 4. Handle Pull Request events
    if event_type == "pull_request":
        action = payload.get("action")
        pr_number = payload["pull_request"]["number"]
        repo_name = payload["repository"]["full_name"]
        commit_id = payload["pull_request"]["head"]["sha"]

        print(f"📦 Repository: {repo_name} | PR #{pr_number}")
        print(f"⚡ PR Action: {action}")

        if action in ["opened", "synchronize", "reopened"]:
            print("🚀 Queuing background AI code review task...")
            background_tasks.add_task(
                trigger_ai_review, repo_name, pr_number, commit_id
            )
            return {"status": "success", "message": "AI review queued"}
        else:
            print(
                f"ℹ️ Skipping action '{action}' (only review on opened/synchronize/reopened)"
            )
            return {"status": "ignored", "message": f"Action {action} ignored"}

    print(f"ℹ️ Event '{event_type}' received and acknowledged.")
    return {"status": "ignored", "message": f"Unhandled event {event_type}"}

