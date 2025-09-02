"""Asynchronous Git/GitHub version management utilities."""

import asyncio
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


class AsyncGitVersionManager:
    """Manage Git versioning workflows in a local GitHub repository.

    Designed to support AI agents modifying code in a project directory.

    Attributes:
        repo_path (Path): Path to the local git repository.
        base_branch_name (str): Name of the base branch to work from.
        init_working_branch (bool): Whether to initialise the working branch on creation.
    """
    def __init__(self, repo_path: str, base_branch_name: str, init_working_branch: bool = True):
        """Initialize with repository path and base branch name.

        Note: Call `await setup()` or use `await AsyncGitVersionManager.create(...)`
        to perform async initialization steps.
        """
        self.repo_path = Path(repo_path).resolve()
        self.base_branch_name = base_branch_name
        self.true_branch_name = None  
        self.init_working_branch = init_working_branch

        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path not found: {self.repo_path}")
        if not (self.repo_path / '.git').exists():
            raise FileNotFoundError(f"No git repository found at: {self.repo_path}")

    @classmethod
    async def create(
        cls, repo_path: str, base_branch_name: str, init_working_branch: bool = True
    ) -> "AsyncGitVersionManager":
        """Instantiate and asynchronously set up the manager."""
        self = cls(repo_path=repo_path, base_branch_name=base_branch_name, init_working_branch=init_working_branch)
        await self.setup()
        return self

    async def setup(self) -> None:
        """Run asynchronous initialization tasks."""
        await self._configure_git_identity()
        await self._ensure_https_remote()
        if self.init_working_branch:
            await self._initialise_working_branch()

    async def _configure_git_identity(self):
        await self._run_git("config", "user.email", "bot@example.com")
        await self._run_git("config", "user.name", "AI Publisher Bot")

    async def _ensure_https_remote(self):
        token = GITHUB_TOKEN
        if not token:
            raise RuntimeError("Missing GITHUB_TOKEN in environment")

        remote_url = await self._run_git("remote", "get-url", "origin")

        # Normalize to path "org/repo"
        path: str
        if remote_url.startswith("git@github.com:"):
            # SSH format: git@github.com:org/repo.git
            path = remote_url[len("git@github.com:"):]
        elif remote_url.startswith("https://github.com/"):
            # HTTPS without auth: https://github.com/org/repo.git
            path = remote_url[len("https://github.com/"):]
        elif "@github.com/" in remote_url:
            # HTTPS with embedded auth: https://token@github.com/org/repo.git
            path = remote_url.split("@github.com/")[-1]
        else:
            raise RuntimeError(f"Unrecognized remote format: {remote_url}")

        if path.endswith(".git"):
            path = path[:-4]

        https_url = f"https://{token}:x-oauth-basic@github.com/{path}.git"
        await self._run_git("remote", "set-url", "origin", https_url)

    async def _initialise_working_branch(self):
        """Initialize or select a working branch.

        • Ensures we are on (or create) a branch that begins with `base_branch_name`.
        • Tags HEAD as `last_published`.
        • Sets `self.true_branch_name` for later use.
        """
        try:
            current = await self.current_branch()

            if not current.startswith(self.base_branch_name):
                new_branch = f"{self.base_branch_name}_{uuid.uuid4().hex}"
                await self.create_branch(new_branch)
                self.true_branch_name = new_branch
            else:
                self.true_branch_name = current

            await self.tag_last_published_commit()
            await self.first_commit("First commit")

        except Exception as e:
            logging.getLogger(__name__).warning(
                "Startup branch initialisation failed: %s", e
            )

    async def _gh_auth_login(self):
        """Authenticate GitHub CLI (`gh`) using GITHUB_TOKEN."""
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
        """Create and checkout a new branch locally."""
        try:
            await self._run_git('checkout', '-b', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to create branch '{branch_name}': {e}")

    async def commit_changes(self, message: str) -> bool:
        """Stage all changes and commit if there is a diff against HEAD."""
        try:
            # Stage all files
            await self._run_git('add', '.')
    
            # Check if staged changes differ from HEAD (avoid empty commit)
            diff_process = await asyncio.create_subprocess_exec(
                'git', 'diff', '--cached', '--exit-code', '--quiet', 'HEAD',
                cwd=self.repo_path
            )
            await diff_process.wait()
    
            if diff_process.returncode == 0:
                # No actual content changes to commit
                return False
    
            # Perform the commit
            await self._run_git('commit', '-m', message)
            return True
    
        except Exception as e:
            raise RuntimeError(f"Failed to commit changes: {e}")

    async def first_commit(self, message: str) -> bool:
        """Create an empty initial commit with a message."""
        try:            
            # Perform the commit
            await self._run_git('commit', '--allow-empty', '-m', message)    
        except Exception as e:
            raise RuntimeError(f"Failed to create the first commit: {e}")

    async def checkout_commit(self, commit_hash: str):
        """Check out a specific commit in detached HEAD mode."""
        try:
            await self._run_git('checkout', '-f', commit_hash)
        except Exception as e:
            raise RuntimeError(f"Failed to checkout commit {commit_hash}: {e}")

    async def list_commits(
        self, 
        branch_name: str, 
        limit: int = 50, 
        author_email: str = "bot@example.com", 
        since_last_push: bool = True
    ) -> List[Dict[str, str]]:
        """List commits on a branch, optionally since last published tag."""
        try:
            await self.checkout_branch(branch_name)
    
            # If asking only for unpublished changes (since last push)
            if since_last_push:
                try:
                    # Check if the tag exists
                    _ = await self._run_git("rev-parse", "last_published")
                    range_arg = "last_published..HEAD"
                except Exception:
                    # Tag does not exist → no published point → return empty list
                    return []
    
            else:
                # Include all commits in branch
                range_arg = branch_name
    
            output = await self._run_git(
                "log",
                range_arg,
                f"--max-count={limit}",
                f"--author={author_email}",
                "--pretty=format:%H|%s"
            )
            commits = []
            for line in output.splitlines():
                if "|" in line:
                    commit_hash, message = line.split("|", 1)
                    commits.append({"hash": commit_hash, "message": message})
            return commits[::-1]
    
        except Exception as e:
            raise RuntimeError(f"Failed to list commits: {e}")

    async def commit_versions_dict(
        self, 
        branch_name: str, 
        limit: int = 50, 
        author_email: str = "bot@example.com", 
        since_last_push: bool = True
    ) -> Dict[str, str]:
        """Return a mapping version_N -> commit hash from recent commits."""
        commits = await self.list_commits(branch_name, limit, author_email, since_last_push)
        return {f"version_{i+1}": c["hash"] for i, c in enumerate(commits)}

    async def get_branches(self) -> Dict[str, str]:
        """Return mapping version_N -> branch name for all local branches."""
        try:
            output = await self._run_git('branch', '--list')
            branches = [line.strip().lstrip('* ') for line in output.splitlines()]
            return {f'version_{i+1}': name for i, name in enumerate(branches)}
        except Exception as e:
            raise RuntimeError(f"Failed to list branches: {e}")

    async def checkout_branch(self, branch_name: str):
        """Check out an existing local branch by name."""
        try:
            await self._run_git('checkout', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to checkout branch '{branch_name}': {e}")

    async def push_branch(self, branch_name: str):
        """Push a branch to origin, setting upstream if needed."""
        try:
            await self._run_git('push', '--set-upstream', 'origin', branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to push branch '{branch_name}': {e}")

    async def force_branch_to_current_commit(self, branch_name: str):
        """Move <branch_name> so it points at the currently checked out commit.

        (which may be a detached‑HEAD commit), then force‑push it to origin.

        Equivalent shell:
            COMMIT=$(git rev-parse HEAD)
            git checkout <branch_name>
            git reset --hard $COMMIT
            git push --force origin <branch_name>
        """
        try:
            # 1. Remember the detached‑HEAD commit we want
            current_commit = await self._run_git("rev-parse", "HEAD")

            # 2. Switch to the target branch
            await self._run_git("checkout", branch_name)

            # 3. Rewind the branch pointer to that commit
            await self._run_git("reset", "--hard", current_commit)

            # 4. Force‑push so remote matches local
            await self._run_git("push", "--force", "origin", branch_name)

        except Exception as e:
            raise RuntimeError(
                f"Failed to force branch '{branch_name}' to commit {current_commit}: {e}"
            )

    async def safe_push(self, branch_name: str):
        """Push to origin; handle detached HEAD via force move if necessary."""
        branch = await self.current_branch()
        if branch == "HEAD":
            await self.force_branch_to_current_commit(branch_name)
        else:
            await self.push_branch(branch_name)

    async def tag_last_published_commit(self, tag_name: str = "last_published"):
        """Tag the current HEAD as the last published commit (force update)."""
        commit_hash = await self._run_git("rev-parse", "HEAD")
        await self._run_git("tag", "-f", tag_name, commit_hash)  # -f to overwrite

    async def current_branch(self) -> str:
        """Return the current branch name or 'HEAD' if detached."""
        try:
            return await self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
        except Exception as e:
            raise RuntimeError(f"Failed to get current branch: {e}")

    async def create_pull_request(self, title: str, body: str = "", base: str = "main") -> str:
        """Create a pull request from the current branch to `base`."""
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

    async def pull_request_exists(self, branch_name: str) -> bool:
        """Check if a pull request exists for the given head branch."""
        try:
            output = await self._run_gh(
                "pr", "list",
                "--head", branch_name,
                "--json", "number",
                "--jq", ".[0].number"
            )
            return output.strip().isdigit()
        except Exception as e:
            raise RuntimeError(f"Failed to check pull request existence for '{branch_name}': {e}")

    async def save_branch_versions_as_json(self, file_path: str):
        """Save local branch names as a JSON mapping to the given file path."""
        try:
            branches = await self.get_branches()
            json_path = Path(file_path)
            json_path.write_text(json.dumps(branches, indent=2))
        except Exception as e:
            raise RuntimeError(f"Failed to save branches to JSON: {e}")

    async def remove_branch(self, branch_name: str, force: bool = False):
        """Remove a local branch by name; refuse if it's currently checked out."""
        try:
            current = await self.current_branch()
            if current == branch_name:
                raise RuntimeError("Cannot delete the branch currently checked out.")

            flag = '-D' if force else '-d'
            await self._run_git('branch', flag, branch_name)
        except Exception as e:
            raise RuntimeError(f"Failed to remove branch '{branch_name}': {e}")
