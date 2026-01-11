"""Tests for file_handler module."""

import os
import tempfile
import pytest

from file_handler import FileReader


class TestFileReader:
    """Tests for FileReader class."""

    def test_file_reader_small_file(self):
        """Small file should load content immediately."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import numpy\nprint('hello')")
            f.flush()
            try:
                reader = FileReader(f.name, threshold=1000)
                assert reader.is_large is False
                assert reader.content is not None
                assert "import numpy" in reader.content
            finally:
                os.unlink(f.name)

    def test_file_reader_large_file_threshold(self):
        """File exceeding threshold should not load content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            # Create file larger than threshold
            f.write("x" * 200)
            f.flush()
            try:
                reader = FileReader(f.name, threshold=100)
                assert reader.is_large is True
                assert reader.content is None
            finally:
                os.unlink(f.name)

    def test_file_reader_get_content_small_file(self):
        """get_content() should return content for small files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write("#!/bin/bash\necho hello")
            f.flush()
            try:
                reader = FileReader(f.name, threshold=1000)
                content = reader.get_content()
                assert "echo hello" in content
            finally:
                os.unlink(f.name)

    def test_file_reader_get_content_large_file_fails(self):
        """get_content() should raise error for large files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x" * 200)
            f.flush()
            try:
                reader = FileReader(f.name, threshold=100)
                with pytest.raises(ValueError, match="too large"):
                    reader.get_content()
            finally:
                os.unlink(f.name)

    def test_file_reader_search_in_file(self):
        """search_in_file should find matching lines."""
        content = """def hello():
    print('hello')

def world():
    print('world')
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                reader = FileReader(f.name, threshold=10000)
                matches = reader.search_in_file(r"^def ")
                assert len(matches) == 2
                assert matches[0]['line_num'] == 1
                assert matches[0]['content'] == "def hello():"
                assert matches[1]['line_num'] == 4
                assert matches[1]['content'] == "def world():"
            finally:
                os.unlink(f.name)

    def test_file_reader_search_with_context(self):
        """search_in_file should include context lines."""
        content = """line1
import numpy as np
line3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                reader = FileReader(f.name, threshold=10000)
                matches = reader.search_in_file(r"import", context_lines=1)
                assert len(matches) == 1
                assert matches[0]['line_num'] == 2
                assert len(matches[0]['context_before']) > 0
                assert len(matches[0]['context_after']) > 0
            finally:
                os.unlink(f.name)

    def test_file_reader_search_no_matches(self):
        """search_in_file should return empty list when no matches."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            try:
                reader = FileReader(f.name, threshold=10000)
                matches = reader.search_in_file(r"^import ")
                assert matches == []
            finally:
                os.unlink(f.name)

    def test_file_reader_search_invalid_regex(self):
        """search_in_file should handle invalid regex."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("test")
            f.flush()
            try:
                reader = FileReader(f.name, threshold=10000)
                with pytest.raises(ValueError, match="Invalid regex"):
                    reader.search_in_file(r"[invalid(")
            finally:
                os.unlink(f.name)

    def test_file_reader_line_count_small_file(self):
        """line_count should be accurate for small files."""
        content = "line1\nline2\nline3\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                reader = FileReader(f.name, threshold=1000)
                assert reader.line_count == 3
            finally:
                os.unlink(f.name)

    def test_file_reader_line_count_large_file(self):
        """line_count should work for large files too."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write 200 lines
            for i in range(200):
                f.write(f"line {i}\n")
            f.flush()
            try:
                reader = FileReader(f.name, threshold=100)  # Small threshold to make it large
                assert reader.line_count == 200
            finally:
                os.unlink(f.name)

