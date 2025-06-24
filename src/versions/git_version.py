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
    """
    Asynchronous manager for handling Git versioning workflows in a local GitHub repository.
    Designed to support AI agents modifying code in a project directory.
    
    Attributes:
        repo_path (Path): Path to the local git repository.
    """
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {self.repo_path}")

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
        """Create a new git branch."""
        try:
            await self._run_git('checkout', '-b', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {e}")

    async def commit_changes(self, message: str):
        """Stage all changes and commit with a message."""
        try:
            await self._run_git('add', '.')
            await self._run_git('commit', '-m', message)
        except Exception as e:
            raise RuntimeError(f"Failed to commit changes: {e}")

    async def get_branches(self) -> Dict[str, str]:
        """List all branches in the repository."""
        try:
            output = await self._run_git('branch', '--list')
            branches = [line.strip().lstrip('* ') for line in output.splitlines()]
            return {f'version_{i+1}': name for i, name in enumerate(branches)}
        except Exception as e:
            raise RuntimeError(f"Failed to list branches: {e}")

    async def checkout_branch(self, branch_name: str):
        """Switch to a specific branch."""
        try:
            await self._run_git('checkout', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to checkout branch '{branch_name}': {e}")

    async def push_branch(self, branch_name: str):
        """Push the branch to the remote repository."""
        try:
            await self._run_git('push', '--set-upstream', 'origin', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to push branch '{branch_name}': {e}")

    async def current_branch(self) -> str:
        """Return the name of the currently checked out branch."""
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
        """Save the list of branches as a JSON file."""
        try:
            branches = await self.get_branches()
            json_path = Path(file_path)
            json_path.write_text(json.dumps(branches, indent=2))
        except Exception as e:
            raise RuntimeError(f"Failed to save branches to JSON: {e}")

    async def remove_branch(self, branch_name: str, force: bool = False):
        """
        Remove a local git branch.

        Args:
            branch_name (str): Name of the branch to remove.
            force (bool): Whether to force deletion (use -D instead of -d).
        """
        try:
            current = await self.current_branch()
            if current == branch_name:
                raise RuntimeError("Cannot delete the branch currently checked out.")

            flag = '-D' if force else '-d'
            await self._run_git('branch', flag, branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to remove branch '{branch_name}': {e}")
