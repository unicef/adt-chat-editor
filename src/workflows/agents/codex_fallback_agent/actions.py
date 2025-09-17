import os
import shlex
import subprocess
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from src.prompts import CODEX_FALLBACK_SYSTEM_PROMPT
from src.settings import (
    OUTPUT_DIR,
    TAILWIND_CSS_IN_DIR,
    TAILWIND_CSS_OUT_DIR,
    custom_logger,
    settings,
)
from src.structs import StepStatus, TranslatedHTMLStatus
from src.utils import (
    get_message,
    to_single_line,
    update_tailwind,
)
from src.workflows.state import ADTState

logger = custom_logger("Create Activity Agent")


async def fallback_agent(state: ADTState, config: RunnableConfig) -> ADTState:
    """Codex Fallback agent to edit HTML files based on the instruction."""
    # Define current state step
    current_step = state.steps[state.current_step_index]

    # command flags & contents
    working_dir = OUTPUT_DIR
    context = to_single_line(CODEX_FALLBACK_SYSTEM_PROMPT)
    user_prompt = (
        to_single_line(current_step.step)
        .replace('"', "'")
        .replace(OUTPUT_DIR + "/", "")
    )

    # Use list of arguments instead of shell string to avoid escaping issues
    codex_args = [
        "codex",
        context,
        "exec",
        "-m",
        settings.OPENAI_CODEX_MODEL,
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        user_prompt,
    ]

    logger.info(f"Codex command: {' '.join(shlex.quote(arg) for arg in codex_args)}")

    try:
        codex_result = subprocess.run(
            codex_args,
            shell=False,  # Changed from shell=True to avoid shell escaping issues
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=600,
            env=os.environ.copy(),
        )
        if codex_result.returncode != 0:
            logger.warning(f"Codex command failed:\n{codex_result.stderr}")
        else:
            logger.info("Codex command run successfully.")

        message = f"The following files have been updated by codex based on based on the instruction: '{current_step.step}'\n"
    except subprocess.TimeoutExpired:
        logger.warning("Codex execution timed out")
        message = f"Codex command failed based on based on the instruction: '{current_step.step}'\n"
    except FileNotFoundError:
        logger.warning("Codex CLI not found")
        message = f"Codex command failed based on based on the instruction: '{current_step.step}'\n"
    except Exception as e:
        logger.warning(f"Codex execution failed: {str(e)}")
        message = f"Codex command failed based on based on the instruction: '{current_step.step}'\n"

    # Command to update the tailwind.css
    updated_tailwind = await update_tailwind(
        OUTPUT_DIR, TAILWIND_CSS_IN_DIR, TAILWIND_CSS_OUT_DIR
    )
    logger.info(f"Updated_tailwind: {updated_tailwind}")

    # Add message
    state.add_message(SystemMessage(content=message))
    state.add_message(
        AIMessage(content=get_message(state.user_language.value, "final_response"))
    )

    # Set translated_html_status to not installed
    state.translated_html_status = TranslatedHTMLStatus.NOT_INSTALLED

    # Update step status
    if 0 <= state.current_step_index < len(state.steps):
        state.steps[state.current_step_index].status = StepStatus.SUCCESS

    return state
