import os
import base64
from github import Github, Auth
from dotenv import load_dotenv
from fastmcp import FastMCP  #

load_dotenv()

# 1. Create the server instance with a descriptive name
mcp = FastMCP(name="DevSecOps-Context-Server")


def get_github_client():
    """Helper function to authenticate with GitHub."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("❌ GITHUB_TOKEN is missing in the .env file!")
    auth = Auth.Token(token)
    return Github(auth=auth)


# 2. Add a tool using the @mcp.tool decorator
@mcp.tool
def fetch_full_file(repo_name: str, file_path: str) -> str:
    """
    Fetches the complete, raw text content of a specific file from a GitHub repository.
    Use this tool when the PR diff does not provide enough context to verify a security flaw.
    """
    print(f"🛠️  MCP Tool Triggered: Fetching {file_path} from {repo_name}...")

    try:
        client = get_github_client()
        repo = client.get_repo(repo_name)

        # Fetch the file contents from the repository
        file_content = repo.get_contents(file_path)

        # GitHub returns file contents as base64 encoded bytes, so we decode it to a string
        if file_content.encoding == "base64":
            decoded_bytes = base64.b64decode(file_content.content)
            return decoded_bytes.decode("utf-8")
        else:
            return file_content.content

    except Exception as e:
        return f"Error fetching file: {str(e)}"


if __name__ == "__main__":
    # 3. Make the server executable
    print("🚀 Starting FastMCP Context Server...")
    mcp.run()  #
