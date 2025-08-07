import os
import subprocess
import datetime
from typing import List, Optional
from src.prompts import CODEX_CONTEXT
from src.settings import (
    OUTPUT_DIR,
    TAILWIND_CSS_IN_DIR,
    TAILWIND_CSS_OUT_DIR,
    custom_logger,
    settings
)
from src.structs.terminal import ExecuteCommandRequest, CommandResponse, CommandHistory
from src.utils import to_single_line

# Initialize logger
logger = custom_logger("Terminal Service")


class TerminalService:
    def __init__(self):
        self.command_history: List[CommandHistory] = []
        self.allowed_commands = [
            "ls", "pwd", "cd", "mkdir", "rm", "echo", "touch",
            "cat", "cp", "mv", "git", "python", "pip",
        ]

    def is_command_allowed(self, command: str) -> bool:
        base_command = command.split()[0]
        return base_command in self.allowed_commands

    def execute_command(self, request: ExecuteCommandRequest) -> CommandResponse:
        if self.is_command_allowed(request.command):
            return self._run_shell_command(request.command, request.working_directory)
        else:
            # Fallback to Codex
            return self._run_codex_instruction(request.command, OUTPUT_DIR)

    def _run_shell_command(self, command: str, working_dir: Optional[str]) -> CommandResponse:
        working_dir = working_dir or os.getcwd()
        timestamp = datetime.datetime.now().isoformat()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=60
            )

            output = result.stdout + result.stderr
            exit_code = result.returncode

            response = CommandResponse(
                output=output.strip(),
                exit_code=exit_code,
                timestamp=timestamp,
            )

            self.command_history.append(CommandHistory(
                command=command,
                output=output.strip()[:],
                timestamp=timestamp,
                exit_code=exit_code,
            ))

            return response

        except subprocess.TimeoutExpired:
            raise ValueError("Command execution timed out")
        except Exception as e:
            raise ValueError(f"Command execution failed: {str(e)}")

    def _run_codex_instruction(self, prompt: str, working_dir: Optional[str]) -> CommandResponse:
        """Use Codex CLI to process natural-language instructions"""
        working_dir = working_dir or os.getcwd()
        timestamp = datetime.datetime.now().isoformat()
        context = to_single_line(CODEX_CONTEXT)
        
        codex_cmd = f'codex "{context}" exec -m {settings.OPENAI_MODEL} --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check "{prompt}"'

        logger.info(f"Codex command: {codex_cmd}")

        try:
            result = subprocess.run(
                codex_cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=600,
                env=os.environ.copy(),
            )

            output = result.stdout + result.stderr
            exit_code = result.returncode

            response = CommandResponse(
                output=f"[codex] {output.strip()}",
                exit_code=exit_code,
                timestamp=timestamp,
            )

            self.command_history.append(CommandHistory(
                command=f"[codex] {prompt}",
                output=output.strip()[:],
                timestamp=timestamp,
                exit_code=exit_code,
            ))

            # Run Tailwind CSS build in same working directory
            cmd = f"npx tailwindcss -i {TAILWIND_CSS_IN_DIR} -o {TAILWIND_CSS_OUT_DIR}"
            tailwind_result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=60,
                env=os.environ.copy(),
            )
    
            if tailwind_result.returncode != 0:
                logger.warning(f"Tailwind build failed:\n{tailwind_result.stderr}")
            else:
                logger.info("Tailwind CSS updated successfully.")

            return response

        except subprocess.TimeoutExpired:
            raise ValueError("Codex execution timed out")
        except FileNotFoundError:
            raise ValueError("Codex CLI not found")
        except Exception as e:
            raise ValueError(f"Codex execution failed: {str(e)}")

    def get_history(self) -> List[CommandHistory]:
        return self.command_history

    def clear_history(self):
        self.command_history.clear()
