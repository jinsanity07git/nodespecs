import os
import re
import subprocess
from typing import Dict, List, Optional


class GitCollector:
    def __init__(self, base_tag: str = "v1.1.1", exclude_branches: Optional[List[str]] = None,
                 repo_dir: Optional[str] = None):
        self.base_tag = base_tag
        self.exclude_branches = exclude_branches or []
        self.repo_dir = repo_dir or os.getcwd()
        self.commits = []
        self.branches = []
        self.merge_commits = {}

        if not os.path.exists(self.repo_dir):
            raise ValueError(f"Repository directory does not exist: {self.repo_dir}")

        if not os.path.isdir(self.repo_dir):
            raise ValueError(f"Repository path is not a directory: {self.repo_dir}")

    def run_git_command(self, command: List[str]) -> str:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.repo_dir,
                encoding="utf-8",
                errors="replace",
            )
            return result.stdout.strip() if result.stdout else ""
        except subprocess.CalledProcessError as e:
            print(f"Git command failed in {self.repo_dir}: {' '.join(command)}")
            print(f"Error: {e.stderr if e.stderr else 'Unknown error'}")
            raise

    def verify_git_repository(self) -> bool:
        try:
            self.run_git_command(["git", "rev-parse", "--git-dir"])
            return True
        except subprocess.CalledProcessError:
            return False

    def verify_tag_exists(self) -> bool:
        try:
            tags = self.run_git_command(["git", "tag", "--list"])
            return self.base_tag in tags.split("\n")
        except subprocess.CalledProcessError:
            return False

    def get_all_branches(self) -> List[str]:
        output = self.run_git_command(["git", "branch", "-a"])
        branches = []

        for line in output.split("\n"):
            branch = line.strip().lstrip("* ").strip()
            if not branch:
                continue

            if any(exclude in branch for exclude in self.exclude_branches):
                continue

            if branch.startswith("remotes/origin/"):
                branch_name = branch.replace("remotes/origin/", "")
                if branch_name not in ["HEAD", "main", "master"] or branch_name == "main":
                    branches.append(branch_name)
            elif not branch.startswith("remotes/"):
                branches.append(branch)

        return list(set(branches))

    def get_commits_since_tag(self) -> List[Dict]:
        self.run_git_command(
            ["git", "log", "--all", "--oneline", "--graph", "--decorate",
             f"{self.base_tag}..HEAD"]
        )

        detailed_output = self.run_git_command(
            [
                "git",
                "log",
                "--all",
                "--format=%H|%P|%s|%an|%ad|%D",
                "--date=iso",
                f"{self.base_tag}..HEAD",
            ]
        )

        commits = []
        for line in detailed_output.split("\n"):
            if not line.strip():
                continue

            parts = line.split("|")
            if len(parts) >= 6:
                commit_hash = parts[0]
                parents = parts[1].split() if parts[1] else []
                subject = parts[2]
                author = parts[3]
                date = parts[4]
                refs = parts[5] if len(parts) > 5 else ""

                commits.append(
                    {
                        "hash": commit_hash,
                        "short_hash": commit_hash[:7],
                        "parents": parents,
                        "subject": subject,
                        "author": author,
                        "date": date,
                        "refs": refs,
                        "is_merge": len(parents) > 1,
                    }
                )

        return commits

    def get_merge_commits(self) -> Dict[str, Dict]:
        merge_output = self.run_git_command(
            ["git", "log", "--all", "--merges", "--format=%H %P %s", f"{self.base_tag}..HEAD"]
        )

        merges = {}
        for line in merge_output.split("\n"):
            if not line.strip():
                continue

            parts = line.split(" ", 2)
            if len(parts) >= 3:
                commit_hash = parts[0]
                parents = parts[1].split()
                subject = parts[2]

                pr_match = re.search(r"#(\d+)", subject)
                pr_number = pr_match.group(1) if pr_match else None

                merges[commit_hash] = {
                    "parents": parents,
                    "subject": subject,
                    "pr_number": pr_number,
                }

        return merges

    @staticmethod
    def extract_branch_from_subject(subject: str) -> Optional[str]:
        patterns = [
            r"from CTPSSTAFF/([^\)\s]+)",
            r"Merge pull request #\d+ from CTPSSTAFF/([^\)\s]+)",
            r"Merge branch '([^']+)'",
            r"into ([^\)\s]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, subject)
            if match:
                return match.group(1)

        return None
