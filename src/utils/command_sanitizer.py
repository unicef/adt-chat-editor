"""Command sanitizer for terminal execution.

This module provides security validation for terminal commands,
preventing command injection and other malicious patterns.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    """Result of command validation."""

    is_valid: bool
    sanitized_command: Optional[str]
    error: Optional[str]


class CommandSanitizer:
    """Validates and sanitizes terminal commands for secure execution."""

    # Dangerous command patterns that should be blocked
    DANGEROUS_COMMANDS = [
        r"\brm\s+(-rf|--recursive\s+--force|-fr)",  # rm -rf
        r"\bmkfs\b",  # Format filesystem
        r"\bdd\b.*if=/dev/",  # Disk destroyer
        r"\b:()\{\s*:\|:&\s*\};:",  # Fork bomb
        r"\bchmod\s+777",  # Overly permissive permissions
        r"\bchown\s+.*root",  # Change ownership to root
        r"\bsudo\b",  # Privilege escalation
        r"\bsu\b",  # Switch user
        r"\bpasswd\b",  # Password change command
        r"\bkill\s+-9\s+1\b",  # Kill init process
        r"\bshutdown\b",  # System shutdown
        r"\breboot\b",  # System reboot
        r"\binit\s+0",  # Halt system
        r"\bwget\b.*\|.*sh",  # Download and execute
        r"\bcurl\b.*\|.*sh",  # Download and execute
        r"\bnc\b.*-e",  # Netcat with command execution
        r"\b/dev/sd[a-z]",  # Direct disk access
        # Sensitive file and directory access
        r"~?/?\.ssh/",  # SSH directory
        r"id_rsa",  # SSH private keys
        r"\.pem\b",  # Certificate/key files
        r"~?/?\.aws/",  # AWS credentials directory
        r"\.kube/config",  # Kubernetes config
    ]

    # Shell metacharacters and operators that enable command injection
    # These are ALWAYS blocked, regardless of context
    SHELL_METACHARACTERS = [
        (";", "command chaining (;) not allowed"),
        ("&&", "command chaining (&&) not allowed"),
        ("||", "command chaining (||) not allowed"),
        ("|", "pipe operator (|) not allowed"),
        (">", "output redirection (>) not allowed"),
        ("<", "input redirection (<) not allowed"),
        (">>", "output redirection (>>) not allowed"),
        ("$(", "command substitution not allowed"),
        ("`", "command substitution (backtick) not allowed"),
        ("\n", "newline characters not allowed"),
        ("\r", "carriage return characters not allowed"),
    ]

    # Additional dangerous patterns for command injection
    INJECTION_PATTERNS = [
        r"`.*`",  # Command substitution (backticks) - additional check
        r"\$\(.*\)",  # Command substitution $(...) - additional check
    ]

    # Characters that could be used for injection
    SUSPICIOUS_CHARS = [
        r"\x00",  # Null byte
        r"\r",  # Carriage return (except in normal strings)
        r"&gt;&gt;",  # HTML encoded redirect
        r"&lt;&lt;",  # HTML encoded heredoc
    ]

    def __init__(self):
        """Initialize the sanitizer with compiled regex patterns."""
        self.dangerous_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_COMMANDS
        ]
        self.injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS
        ]
        self.suspicious_char_patterns = [
            re.compile(pattern) for pattern in self.SUSPICIOUS_CHARS
        ]

    def _check_for_metacharacters(self, command: str) -> Optional[str]:
        """
        Check if command contains dangerous shell metacharacters.

        Args:
            command: The command to check

        Returns:
            Error message if dangerous characters found, None otherwise
        """
        for char, message in self.SHELL_METACHARACTERS:
            if char in command:
                return f"Shell metacharacter detected: {message}"
        return None

    def sanitize(self, command: str) -> ValidationResult:
        """
        Validate and sanitize a terminal command.

        Args:
            command: The command string to validate

        Returns:
            ValidationResult with validation status, sanitized command, and error message
        """
        if not command or not command.strip():
            return ValidationResult(
                is_valid=False,
                sanitized_command=None,
                error="Command cannot be empty",
            )

        # Trim whitespace
        sanitized = command.strip()

        # Check for excessively long commands (potential buffer overflow or DOS)
        if len(sanitized) > 1000:
            return ValidationResult(
                is_valid=False,
                sanitized_command=None,
                error="Command is too long (max 1000 characters)",
            )

        # CRITICAL: Check for shell metacharacters FIRST (strictest check)
        # This prevents ALL forms of command chaining, redirection, and substitution
        metachar_error = self._check_for_metacharacters(sanitized)
        if metachar_error:
            return ValidationResult(
                is_valid=False,
                sanitized_command=None,
                error=metachar_error,
            )

        # Check for dangerous commands
        for pattern in self.dangerous_patterns:
            if pattern.search(sanitized):
                return ValidationResult(
                    is_valid=False,
                    sanitized_command=None,
                    error=f"Dangerous command pattern detected: {pattern.pattern}",
                )

        # Check for command injection patterns (additional patterns beyond metacharacters)
        for pattern in self.injection_patterns:
            if pattern.search(sanitized):
                return ValidationResult(
                    is_valid=False,
                    sanitized_command=None,
                    error=f"Command injection pattern detected: {pattern.pattern}",
                )

        # Check for suspicious characters
        for pattern in self.suspicious_char_patterns:
            if pattern.search(sanitized):
                return ValidationResult(
                    is_valid=False,
                    sanitized_command=None,
                    error=f"Suspicious character pattern detected",
                )

        # Check for path traversal attempts
        if self._contains_path_traversal(sanitized):
            return ValidationResult(
                is_valid=False,
                sanitized_command=None,
                error="Path traversal attempt detected",
            )

        # Command passed all validation checks
        return ValidationResult(
            is_valid=True,
            sanitized_command=sanitized,
            error=None,
        )

    def _contains_path_traversal(self, command: str) -> bool:
        """
        Check if command contains suspicious path traversal patterns.

        Args:
            command: The command to check

        Returns:
            True if path traversal is detected
        """
        # Look for multiple consecutive ../ or ..\\ patterns
        traversal_patterns = [
            r"\.\./.*\.\./.*\.\./",  # ../../../
            r"\.\./.*\.\./",  # ../../ (less strict)
            r"/etc/passwd",  # Common target
            r"/etc/shadow",  # Common target
            r"~root",  # Root home directory
            r"/root/",  # Root directory access
            r"\.\./.*root/",  # Path traversal to root
        ]

        # Sensitive file patterns
        sensitive_files = [
            r"auth\.json",  # Authentication files
            r"credentials\.json",  # Credential files
            r"\.env",  # Environment files
            r"id_rsa",  # SSH private keys
            r"\.pem",  # Certificate files
            r"config\.json",  # Config files in traversal context
            r"\.aws/credentials",  # AWS credentials
            r"\.ssh/",  # SSH directory
        ]

        for pattern in traversal_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True

        # Check for sensitive files combined with path traversal
        if re.search(r"\.\./", command):
            for sensitive in sensitive_files:
                if re.search(sensitive, command, re.IGNORECASE):
                    return True

        return False


# Global instance for easy import
_sanitizer = CommandSanitizer()


def sanitize_terminal_command(command: str) -> ValidationResult:
    """
    Convenience function to sanitize a terminal command.

    Args:
        command: The command string to validate

    Returns:
        ValidationResult with validation status, sanitized command, and error message
    """
    return _sanitizer.sanitize(command)
