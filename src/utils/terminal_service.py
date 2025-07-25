import subprocess
import datetime
import os
from typing import List, Optional
from src.structs.terminal import ExecuteCommandRequest, CommandResponse, CommandHistory


class TerminalService:
    def __init__(self):
        self.command_history: List[CommandHistory] = []
        self.allowed_commands = [
            "ls",
            "cd",
            "pwd",
            "whoami",
            "date",
            "echo",
            "cat",
            "head",
            "tail",
            "grep",
            "find",
            "ps",
            "top",
            "df",
            "du",
            "free",
            "uptime",
            "git",
            "npm",
            "yarn",
            "node",
            "python",
            "pip",
            "docker",
            "docker-compose",
            "docker-compose.yml",
            "docker-compose.yaml",
        ]

    def is_command_allowed(self, command: str) -> bool:
        """Check if command is in the allowed whitelist"""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
        base_command = cmd_parts[0].lower()
        return base_command in self.allowed_commands

    def execute_command(self, request: ExecuteCommandRequest) -> CommandResponse:
        """Execute a command and return the result"""
        try:
            # Validate command
            if not self.is_command_allowed(request.command):
                raise ValueError(f"Command '{request.command}' is not allowed")

            # Set working directory (default to current directory)
            working_dir = (
                request.working_directory or os.getcwd()
            )  # Use current working directory

            # Execute command with timeout
            result = subprocess.run(
                request.command.split(),
                capture_output=True,
                text=True,
                cwd=working_dir,
                timeout=30,  # 30 second timeout
                env=os.environ.copy(),  # Pass current environment
            )

            # Create response
            response = CommandResponse(
                output=result.stdout + result.stderr,
                exit_code=result.returncode,
                timestamp=datetime.datetime.now().isoformat(),
            )

            # Store in history
            history_entry = CommandHistory(
                command=request.command,
                output=response.output,
                timestamp=response.timestamp,
                exit_code=response.exit_code,
            )
            self.command_history.append(history_entry)

            # Keep only last 100 commands
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]

            return response

        except subprocess.TimeoutExpired:
            raise ValueError("Command execution timed out")
        except FileNotFoundError:
            raise ValueError(f"Command not found: {request.command}")
        except Exception as e:
            raise ValueError(f"Command execution failed: {str(e)}")

    def get_history(self) -> List[CommandHistory]:
        """Get command history"""
        return self.command_history.copy()

    def clear_history(self) -> None:
        """Clear command history"""
        self.command_history.clear()
