import os
from github import Github, Auth
from dotenv import load_dotenv

load_dotenv()


class GitHubClient:
    def __init__(self):
        """
        Initializes the connection to GitHub using the modern Auth Token method.
        """
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("❌ GITHUB_TOKEN is missing in the .env file!")

        # MODERN AUTH FIX: Use the Auth.Token module to clear the deprecation warning
        auth = Auth.Token(token)
        self.client = Github(auth=auth)

    def get_pr_diff(self, repo_name: str, pr_number: int) -> list:
        """
        Fetches the exact lines of code that changed in a Pull Request.
        """
        print(f"📥 Fetching diff for {repo_name} PR #{pr_number}...")

        repo = self.client.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)

        changed_files = []

        for file in pull_request.get_files():
            if file.patch:
                changed_files.append(
                    {
                        "filename": file.filename,
                        "patch": file.patch,
                        "additions": file.additions,
                        "deletions": file.deletions,
                    }
                )

        return changed_files

    def post_inline_comment(
        self, repo_name: str, pr_number: int, commit_id: str, file_path: str, body: str
    ):
        """
        Posts a Markdown suggestion comment directly on the code.
        """
        repo = self.client.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)

        try:
            pull_request.create_review_comment(
                body=body, commit=repo.get_commit(commit_id), path=file_path, position=1
            )
            print("✅ Review posted successfully!")
        except Exception as e:
            print(f"❌ Failed to post comment: {e}")


# --- TEMPORARY TEST BLOCK ---
if __name__ == "__main__":
    client = GitHubClient()

    try:
        # Testing on a very old React PR that we know exists!
        test_diff = client.get_pr_diff("facebook/react", 10000)
        print(
            f"\n🎉 Success! Fetched {len(test_diff)} changed files from React PR #10000."
        )
        print(f"First file changed: {test_diff[0]['filename']}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
