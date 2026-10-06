import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from github_client import GitHubClient

load_dotenv()


class DevSecOpsAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ GROQ_API_KEY is missing in the .env file!")

        self.llm = ChatGroq(
            temperature=0,
            model_name="openai/gpt-oss-20b",
            api_key=api_key,
        )
        self.github = GitHubClient()

    def build_dynamic_prompt(self, filename: str) -> str:
        prompt = """
        You are an elite DevSecOps code reviewer.
        Your job is to review the provided Git diff for security vulnerabilities.
        
        CRITICAL RULES:
        1. If the code is secure, you MUST reply with exactly the word: SAFE
        2. Do NOT comment on formatting, styling, or minor typos.
        3. If there is a security vulnerability, explain it briefly and provide the fix inside a GitHub ```suggestion``` block.
        """

        if filename.endswith(".py"):
            prompt += "\nTECH STACK: Python. Look for insecure deserialization, SQL injection, and hardcoded secrets."
        elif filename.endswith((".js", ".ts", ".jsx")):
            prompt += "\nTECH STACK: Node.js/React. Look for unhashed passwords, NoSQL injection, and missing JWT validations."

        return prompt

    def review_pull_request(self, repo_name: str, pr_number: int, commit_id: str):
        print(f"\n🧠 Starting AI Review for {repo_name} PR #{pr_number}...")

        changed_files = self.github.get_pr_diff(repo_name, pr_number)

        if not changed_files:
            print("No code changes found to review.")
            return

        for file in changed_files:
            filename = file["filename"]
            patch = file["patch"]

            print(f"🔍 Analyzing {filename}...")
            system_prompt = self.build_dynamic_prompt(filename)

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Review this diff for {filename}:\n\n{patch}"),
            ]

            response = self.llm.invoke(messages)
            ai_review = response.content.strip()

            if ai_review == "SAFE":
                print(f"✅ {filename} is secure. No comment posted.")
            else:
                print(f"⚠️ Vulnerability found in {filename}! Posting comment...")
                self.github.post_inline_comment(
                    repo_name, pr_number, commit_id, filename, ai_review
                )

        print("\n🎉 AI PR Review Complete!")
