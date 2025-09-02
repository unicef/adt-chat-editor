"""Aggregate prompt templates for public export."""

from src.prompts.asset_transferring_agent import (  # noqa: F401
    ASSET_TRANSFER_SYSTEM_PROMPT,
    ASSET_TRANSFER_USER_PROMPT,
)
from src.prompts.codex_fallback_agent import CODEX_FALLBACK_SYSTEM_PROMPT  # noqa: F401
from src.prompts.layout_editing_agent import (  # noqa: F401
    LAYOUT_EDIT_SYSTEM_PROMPT,
    LAYOUT_EDIT_USER_PROMPT,
)
from src.prompts.layout_mirroring_agent import (  # noqa: F401
    LAYOUT_MIRRORING_SYSTEM_PROMPT,
    LAYOUT_MIRRORING_USER_PROMPT,
)
from src.prompts.planner import (  # noqa: F401
    ORCHESTRATOR_PLANNING_PROMPT,
    ORCHESTRATOR_SYSTEM_PROMPT,
)
from src.prompts.text_editing_agent import (  # noqa: F401
    TEXT_EDIT_SYSTEM_PROMPT,
    TEXT_EDIT_USER_PROMPT,
)
from src.prompts.web_merging_agent import (  # noqa: F401
    WEB_MERGE_SYSTEM_PROMPT,
    WEB_MERGE_USER_PROMPT,
)
from src.prompts.web_splitting_agent import (  # noqa: F401
    WEB_SPLIT_SYSTEM_PROMPT,
    WEB_SPLIT_USER_PROMPT,
)

__all__ = [
    "ORCHESTRATOR_PLANNING_PROMPT",
    "ORCHESTRATOR_SYSTEM_PROMPT",
    "TEXT_EDIT_SYSTEM_PROMPT",
    "TEXT_EDIT_USER_PROMPT",
    "LAYOUT_EDIT_SYSTEM_PROMPT",
    "LAYOUT_EDIT_USER_PROMPT",
    "LAYOUT_MIRRORING_SYSTEM_PROMPT",
    "LAYOUT_MIRRORING_USER_PROMPT",
    "WEB_MERGE_SYSTEM_PROMPT",
    "WEB_MERGE_USER_PROMPT",
    "WEB_SPLIT_SYSTEM_PROMPT",
    "WEB_SPLIT_USER_PROMPT",
    "CODEX_FALLBACK_SYSTEM_PROMPT",
]
