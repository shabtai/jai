"""Security validation and sanitization module."""

import os
import re
from pathlib import Path


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


def validate_file_path(file_path: str, base_dir: str = None) -> str:
    """
    Validate file path to prevent traversal attacks.

    Args:
        file_path: Path to validate
        base_dir: Optional base directory to restrict to

    Returns:
        Absolute path if valid

    Raises:
        SecurityError: If path traversal detected or file not found
    """
    try:
        # Resolve to absolute path
        abs_path = Path(file_path).resolve()

        # Check if file exists
        if not abs_path.exists():
            raise SecurityError(f"File not found: {file_path}")

        # Check if it's a file (not directory)
        if not abs_path.is_file():
            raise SecurityError(f"Not a file: {file_path}")

        # If base_dir specified, ensure path is within it
        if base_dir:
            base_abs = Path(base_dir).resolve()
            try:
                abs_path.relative_to(base_abs)
            except ValueError:
                raise SecurityError(
                    f"Path {file_path} is outside allowed directory {base_dir}"
                )

        # Check for suspicious patterns in original path
        if ".." in str(file_path) or file_path.startswith("/"):
            # Warn but allow if resolved path is valid
            print(f"Warning: Using unusual path syntax: {file_path}")

        return str(abs_path)

    except SecurityError:
        raise
    except Exception as e:
        raise SecurityError(f"Invalid file path: {e}")


def check_file_size(
    file_path: str,
    max_size_bytes: int = 500 * 1024  # 500KB default
) -> tuple[bool, int]:
    """
    Check if file size is within limits.

    Args:
        file_path: Path to file
        max_size_bytes: Maximum allowed size in bytes

    Returns:
        Tuple of (is_within_limit, actual_size)
    """
    try:
        size = os.path.getsize(file_path)
        return size <= max_size_bytes, size
    except Exception as e:
        raise SecurityError(f"Cannot check file size: {e}")


def detect_prompt_injection(content: str) -> bool:
    """
    Detect suspicious patterns that could indicate prompt injection.

    Args:
        content: Content to check

    Returns:
        True if suspicious patterns detected, False otherwise
    """
    if not content or not isinstance(content, str):
        return False

    # Convert to lowercase for matching
    lower_content = content.lower()

    # Suspicious patterns
    patterns = [
        r"ignore\s+(?:all\s+)?(?:previous|prior|initial).*instructions",
        r"forget\s+(?:all\s+)?(?:previous|prior|initial|context)",
        r"new\s+instructions?:",
        r"override\s+(?:all\s+)?previous",
        r"disregard\s+(?:all\s+)?previous",
        r"execute\s+.*code",
        r"run\s+.*command",
        r"system\s+command",
    ]

    for pattern in patterns:
        if re.search(pattern, lower_content):
            return True

    # Check for excessive shell metacharacters (possible command injection)
    dangerous_chars = lower_content.count(";") + lower_content.count("|") + lower_content.count("&&")
    if dangerous_chars > 5:  # Arbitrary threshold
        return True

    return False


def sanitize_docker_input(content: str) -> str:
    """
    Sanitize content for use in Docker contexts.

    Args:
        content: Content to sanitize

    Returns:
        Sanitized content
    """
    if not content:
        return content

    # Remove null bytes
    content = content.replace("\x00", "")

    # Remove control characters except newline, tab, carriage return
    content = "".join(
        char for char in content
        if ord(char) >= 32 or char in "\n\t\r"
    )

    # Escape quotes for shell contexts
    content = content.replace("'", "'\\''")

    return content
