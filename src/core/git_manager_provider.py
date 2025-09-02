"""Provide a lazily created shared Git manager instance."""

from typing import Optional

from src.core.git_version_manager import AsyncGitVersionManager
from src.settings import BASE_BRANCH_NAME, OUTPUT_DIR, custom_logger

logger = custom_logger("GitManagerProvider")

_git_manager: Optional[AsyncGitVersionManager] = None


async def get_git_manager() -> Optional[AsyncGitVersionManager]:
    """Lazily create and cache a Git manager (async setup).

    Returns None if initialisation fails (e.g., OUTPUT_DIR not a git repo),
    so callers can gracefully degrade in dev/test environments.
    """
    global _git_manager
    if _git_manager is None:
        try:
            _git_manager = await AsyncGitVersionManager.create(
                repo_path=OUTPUT_DIR,
                base_branch_name=BASE_BRANCH_NAME,
                init_working_branch=False,
            )
        except Exception as e:  # pragma: no cover - environment dependent
            logger.debug(f"Git manager unavailable: {e}")
            _git_manager = None
    return _git_manager

def get_cached_git_manager() -> Optional[AsyncGitVersionManager]:
    """Return the cached Git manager without creating it."""
    return _git_manager


def set_git_manager(manager: AsyncGitVersionManager) -> None:
    """Set the shared Git manager instance (used by app startup)."""
    global _git_manager
    _git_manager = manager
