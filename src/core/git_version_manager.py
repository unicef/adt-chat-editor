import asyncio
import json
import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class AsyncGitVersionManager:
    """Asynchronous manager for handling Git versioning workflows in a local GitHub repository.
    Designed to support AI agents modifying code in a project directory.

    Attributes:
        repo_path (Path): Path to the local git repository.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {self.repo_path}")
        if not (self.repo_path / '.git').exists():
            raise FileNotFoundError(f"No git repository found at: {self.repo_path}")
        asyncio.create_task(self._configure_git_identity())
        asyncio.create_task(self._ensure_https_remote())

    async def _configure_git_identity(self):
        await self._run_git("config", "user.email", "bot@example.com")
        await self._run_git("config", "user.name", "AI Publisher Bot")

    async def _ensure_https_remote(self):
        token = GITHUB_TOKEN
        if not token:
            raise RuntimeError("Missing GITHUB_TOKEN in environment")

        remote_url = await self._run_git("remote", "get-url", "origin")

        if remote_url.startswith("git@github.com:"):
            path = remote_url.split("git@github.com:")[1].rstrip(".git")
            https_url = f"https://{token}:x-oauth-basic@github.com/{path}.git"
        elif remote_url.startswith("https://github.com/"):
            path = remote_url.split("https://github.com/")[1].rstrip(".git")
            https_url = f"https://{token}:x-oauth-basic@github.com/{path}.git"
        elif token not in remote_url:
            raise RuntimeError(f"Unrecognized or already rewritten remote URL: {remote_url}")
        else:
            return

        await self._run_git("remote", "set-url", "origin", https_url)

    async def _gh_auth_login(self):
        """Authenticates the GitHub CLI (`gh`) using the GitHub token provided in the GITHUB_TOKEN env var.
        """
        token = GITHUB_TOKEN
        if not token:
            raise RuntimeError("Missing GITHUB_TOKEN in environment for gh auth login")

        process = await asyncio.create_subprocess_exec(
            "gh", "auth", "login", "--with-token",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.repo_path
        )
        stdout, stderr = await process.communicate(input=f"{token}\n".encode())

        if process.returncode != 0:
            raise RuntimeError(f"`gh auth login` failed:\n{stderr.decode()}")

    async def _run_git(self, *args):
        process = await asyncio.create_subprocess_exec(
            'git', *args,
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Git error: {' '.join(args)}\n{stderr.decode()}")
        return stdout.decode().strip()

    async def _run_gh(self, *args):
        env = os.environ.copy()
        if GITHUB_TOKEN:
            env['GITHUB_TOKEN'] = GITHUB_TOKEN

        process = await asyncio.create_subprocess_exec(
            'gh', *args,
            cwd=self.repo_path,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"GitHub CLI error: {' '.join(args)}\n{stderr.decode()}")
        return stdout.decode().strip()

    async def create_branch(self, branch_name: str):
        try:
            await self._run_git('checkout', '-b', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {e}")

    async def commit_changes(self, message: str):
        try:
            await self._run_git('add', '.')
            await self._run_git('commit', '-m', message)
        except Exception as e:
            raise RuntimeError(f"Failed to commit changes: {e}")

    async def get_branches(self) -> Dict[str, str]:
        try:
            output = await self._run_git('branch', '--list')
            branches = [line.strip().lstrip('* ') for line in output.splitlines()]
            return {f'version_{i+1}': name for i, name in enumerate(branches)}
        except Exception as e:
            raise RuntimeError(f"Failed to list branches: {e}")

    async def checkout_branch(self, branch_name: str):
        try:
            await self._run_git('checkout', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to checkout branch '{branch_name}': {e}")

    async def push_branch(self, branch_name: str):
        try:
            await self._run_git('push', '--set-upstream', 'origin', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to push branch '{branch_name}': {e}")

    async def current_branch(self) -> str:
        try:
            return await self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
        except Exception as e:
            raise RuntimeError(f"Failed to get current branch: {e}")

    async def create_pull_request(self, title: str, body: str = "", base: str = "main") -> str:
        """Create a pull request from the current branch to the base branch."""
        try:
            head = await self.current_branch()
            return await self._run_gh(
                'pr', 'create',
                '--title', title,
                '--body', body,
                '--base', base,
                '--head', head
            )
        except Exception as e:
            raise RuntimeError(f"Failed to create pull request: {e}")

    async def save_branch_versions_as_json(self, file_path: str):
        try:
            branches = await self.get_branches()
            json_path = Path(file_path)
            json_path.write_text(json.dumps(branches, indent=2))
        except Exception as e:
            raise RuntimeError(f"Failed to save branches to JSON: {e}")

    async def remove_branch(self, branch_name: str, force: bool = False):
        try:
            current = await self.current_branch()
            if current == branch_name:
                raise RuntimeError("Cannot delete the branch currently checked out.")

            flag = '-D' if force else '-d'
            await self._run_git('branch', flag, branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to remove branch '{branch_name}': {e}")
