from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="DevSecOps Copilot")


@app.get("/")
def health_check():
    return {"status": "Agent is running", "mcp_enabled": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
