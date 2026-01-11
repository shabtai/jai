"""File handling with smart reading for large files."""

import re
from pathlib import Path
from typing import Optional


class FileReader:
    """Smart file reader that handles both small and large files."""

    # Size threshold: files larger than this use search tool
    DEFAULT_THRESHOLD = 100 * 1024  # 100KB

    def __init__(self, file_path: str, threshold: int = DEFAULT_THRESHOLD):
        """
        Initialize FileReader.

        Args:
            file_path: Path to file
            threshold: Size threshold in bytes (files larger use search tool)
        """
        self.file_path = file_path
        self.threshold = threshold
        self.content: Optional[str] = None
        self.size = 0
        self.is_large = False
        self.line_count = 0

        self._initialize()

    def _initialize(self):
        """Initialize file: detect if large/small and load content for small files."""
        path = Path(self.file_path)
        self.size = path.stat().st_size
        self.is_large = self.size > self.threshold

        # For small files, load content immediately
        if not self.is_large:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.content = f.read()
                    self.line_count = len(self.content.splitlines())
            except Exception as e:
                raise IOError(f"Failed to read file {self.file_path}: {e}")
        else:
            # For large files, count lines without loading full content
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.line_count = sum(1 for _ in f)
            except Exception as e:
                raise IOError(f"Failed to count lines in {self.file_path}: {e}")

    def get_content(self) -> str:
        """
        Get full file content.

        Returns:
            File content (for small files)

        Raises:
            ValueError: If file is too large, must use search_in_file()
        """
        if self.is_large:
            raise ValueError(
                f"File is too large ({self.size} bytes). "
                "Use search_in_file() instead."
            )
        return self.content

    def search_in_file(self, pattern: str, context_lines: int = 2) -> list[dict]:
        """
        Search for regex pattern in file without loading full content.

        Args:
            pattern: Regex pattern to search for
            context_lines: Number of context lines to include

        Returns:
            List of matches with context
        """
        matches = []
        max_matches = 50

        try:
            regex = re.compile(pattern, re.MULTILINE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                if regex.search(line):
                    # Get context lines
                    start = max(0, line_num - 1 - context_lines)
                    end = min(len(lines), line_num + context_lines)

                    match = {
                        "line_num": line_num,
                        "content": line.rstrip("\n"),
                        "context_before": [
                            l.rstrip("\n") for l in lines[start : line_num - 1]
                        ],
                        "context_after": [
                            l.rstrip("\n") for l in lines[line_num : end]
                        ],
                    }
                    matches.append(match)

                    # Limit results to prevent overwhelming output
                    if len(matches) >= max_matches:
                        break

            return matches

        except Exception as e:
            raise IOError(f"Error searching file: {e}")
