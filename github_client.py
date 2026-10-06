import os
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    def __init__(self):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("❌ GITHUB_TOKEN is missing in the .env file!")

        # Modern Authentication method to prevent deprecation warnings
        auth = Auth.Token(token)
        self.client = Github(auth=auth)

    def get_pr_diff(self, repo_name: str, pr_number: int) -> list:
        print(f"📥 Fetching diff for {repo_name} PR #{pr_number}...")
        repo = self.client.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)

        changed_files = []
        for file in pull_request.get_files():
            if file.patch:
                changed_files.append({"filename": file.filename, "patch": file.patch})
        return changed_files

    def post_inline_comment(
        self, repo_name: str, pr_number: int, commit_id: str, file_path: str, body: str
    ):
        repo = self.client.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)

        try:
            # Attempt to post comment exactly on the changed line
            pull_request.create_review_comment(
                body=body, commit=repo.get_commit(commit_id), path=file_path, position=1
            )
            print(f"✅ Inline review posted successfully on {file_path}!")

        except Exception as e:
            print(f"⚠️ Inline comment failed (likely diff mismatch): {e}")
            print("🔄 Falling back to a general PR comment...")

            # Fallback: Post as a normal comment at the bottom of the PR
            fallback_body = f"### 🛡️ AI Security Review for `{file_path}`\n\n{body}"
            pull_request.create_issue_comment(fallback_body)
            print("✅ General PR comment posted successfully!")
