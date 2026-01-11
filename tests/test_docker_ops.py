"""Tests for docker_ops module."""

import os
import tempfile
import pytest
from unittest.mock import patch, Mock

from docker_ops import (
    check_docker_available,
    build_image,
    run_container,
    normalize_output,
    test_dockerfile,
    TestResult,
)


class TestCheckDockerAvailable:
    """Tests for Docker availability check."""

    @patch('docker_ops.subprocess.run')
    def test_check_docker_available_running(self, mock_run):
        """Should return True when Docker is available."""
        mock_run.return_value = Mock(returncode=0)
        assert check_docker_available() is True

    @patch('docker_ops.subprocess.run')
    def test_check_docker_available_not_running(self, mock_run):
        """Should return False when Docker is not available."""
        mock_run.return_value = Mock(returncode=1)
        assert check_docker_available() is False

    @patch('docker_ops.subprocess.run')
    def test_check_docker_available_error(self, mock_run):
        """Should return False on exception."""
        mock_run.side_effect = Exception("Connection error")
        assert check_docker_available() is False


class TestNormalizeOutput:
    """Tests for output normalization."""

    def test_normalize_output_strips_whitespace(self):
        """Should strip leading/trailing whitespace."""
        output = "  hello world  \n"
        assert normalize_output(output) == "hello world"

    def test_normalize_output_handles_crlf(self):
        """Should normalize CRLF to LF."""
        output = "line1\r\nline2\r\nline3"
        result = normalize_output(output)
        assert result == "line1\nline2\nline3"

    def test_normalize_output_handles_cr(self):
        """Should normalize CR to LF."""
        output = "line1\rline2\rline3"
        result = normalize_output(output)
        assert result == "line1\nline2\nline3"

    def test_normalize_output_mixed_newlines(self):
        """Should handle mixed newline styles."""
        output = "line1\r\nline2\rline3\nline4"
        result = normalize_output(output)
        assert result == "line1\nline2\nline3\nline4"


class TestBuildImage:
    """Tests for Docker image building."""

    @patch('docker_ops.subprocess.run')
    @patch('docker_ops.shutil.copy2')
    def test_build_image_success(self, mock_copy, mock_run):
        """Should return success on successful build."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            script_path = f.name

        with tempfile.NamedTemporaryFile(suffix='Dockerfile', delete=False) as f:
            dockerfile_path = f.name

        try:
            success, error = build_image(dockerfile_path, script_path, 'test-image')
            assert success is True
            assert error is None
        finally:
            os.unlink(script_path)
            os.unlink(dockerfile_path)

    @patch('docker_ops.subprocess.run')
    @patch('docker_ops.shutil.copy2')
    def test_build_image_failure(self, mock_copy, mock_run):
        """Should return error on build failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="Building...",
            stderr="Error: invalid Dockerfile"
        )

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            script_path = f.name

        with tempfile.NamedTemporaryFile(suffix='Dockerfile', delete=False) as f:
            dockerfile_path = f.name

        try:
            success, error = build_image(dockerfile_path, script_path, 'test-image')
            assert success is False
            assert error is not None
            assert "Error: invalid Dockerfile" in error
        finally:
            os.unlink(script_path)
            os.unlink(dockerfile_path)

    @patch('docker_ops.subprocess.run')
    @patch('docker_ops.shutil.copy2')
    def test_build_image_timeout(self, mock_copy, mock_run):
        """Should handle build timeout."""
        mock_run.side_effect = __import__('subprocess').TimeoutExpired('docker', 120)

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            script_path = f.name

        with tempfile.NamedTemporaryFile(suffix='Dockerfile', delete=False) as f:
            dockerfile_path = f.name

        try:
            success, error = build_image(dockerfile_path, script_path, 'test-image')
            assert success is False
            assert "timed out" in error
        finally:
            os.unlink(script_path)
            os.unlink(dockerfile_path)


class TestRunContainer:
    """Tests for running Docker containers."""

    @patch('docker_ops.subprocess.run')
    def test_run_container_success(self, mock_run):
        """Should return success on successful run."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Hello World",
            stderr=""
        )

        success, output, error = run_container('test-image', 'input data')
        assert success is True
        assert output == "Hello World"
        assert error is None

    @patch('docker_ops.subprocess.run')
    def test_run_container_failure(self, mock_run):
        """Should return error on container failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error in script"
        )

        success, output, error = run_container('test-image', 'input data')
        assert success is False
        assert error is not None
        assert "Error in script" in error

    @patch('docker_ops.subprocess.run')
    def test_run_container_timeout(self, mock_run):
        """Should handle container timeout."""
        mock_run.side_effect = __import__('subprocess').TimeoutExpired('docker', 30)

        success, output, error = run_container('test-image', 'input data')
        assert success is False
        assert "timed out" in error

    @patch('docker_ops.subprocess.run')
    def test_run_container_resource_limits(self, mock_run):
        """Should apply resource limits in docker run command."""
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        run_container('test-image', 'input')

        # Check that resource limits were included in command
        cmd = mock_run.call_args[0][0]
        assert '--memory=512m' in cmd
        assert '--cpus=1.0' in cmd
        assert '--network=none' in cmd
        assert '--pids-limit=100' in cmd


class TestTestDockerfile:
    """Tests for Dockerfile testing."""

    @patch('docker_ops.check_docker_available')
    def test_test_dockerfile_docker_unavailable(self, mock_check):
        """Should fail if Docker is not available."""
        mock_check.return_value = False

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='output'
        )

        assert result.success is False
        assert "Docker daemon" in result.build_errors

    @patch('docker_ops.check_docker_available')
    @patch('docker_ops.build_image')
    def test_test_dockerfile_build_failure(self, mock_build, mock_check):
        """Should fail if build fails."""
        mock_check.return_value = True
        mock_build.return_value = (False, "Build error")

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='output'
        )

        assert result.success is False
        assert result.build_errors == "Build error"

    @patch('docker_ops.check_docker_available')
    @patch('docker_ops.build_image')
    @patch('docker_ops.run_container')
    @patch('docker_ops._cleanup_image')
    def test_test_dockerfile_run_failure(self, mock_cleanup, mock_run, mock_build, mock_check):
        """Should fail if container run fails."""
        mock_check.return_value = True
        mock_build.return_value = (True, None)
        mock_run.return_value = (False, None, "Runtime error")

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='output'
        )

        assert result.success is False
        assert result.runtime_errors == "Runtime error"
        assert mock_cleanup.called

    @patch('docker_ops.check_docker_available')
    @patch('docker_ops.build_image')
    @patch('docker_ops.run_container')
    @patch('docker_ops._cleanup_image')
    def test_test_dockerfile_output_mismatch(self, mock_cleanup, mock_run, mock_build, mock_check):
        """Should fail if output doesn't match."""
        mock_check.return_value = True
        mock_build.return_value = (True, None)
        mock_run.return_value = (True, "actual output", None)

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='expected output'
        )

        assert result.success is False
        assert result.output_diff is not None
        assert "expected output" in result.output_diff
        assert "actual output" in result.output_diff
        assert mock_cleanup.called

    @patch('docker_ops.check_docker_available')
    @patch('docker_ops.build_image')
    @patch('docker_ops.run_container')
    @patch('docker_ops._cleanup_image')
    def test_test_dockerfile_success(self, mock_cleanup, mock_run, mock_build, mock_check):
        """Should succeed when output matches."""
        mock_check.return_value = True
        mock_build.return_value = (True, None)
        mock_run.return_value = (True, "expected output", None)

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='expected output'
        )

        assert result.success is True
        assert mock_cleanup.called

    @patch('docker_ops.check_docker_available')
    @patch('docker_ops.build_image')
    @patch('docker_ops.run_container')
    @patch('docker_ops._cleanup_image')
    def test_test_dockerfile_normalizes_output(self, mock_cleanup, mock_run, mock_build, mock_check):
        """Should normalize output before comparison."""
        mock_check.return_value = True
        mock_build.return_value = (True, None)
        # Note the extra whitespace and CRLF
        mock_run.return_value = (True, "expected output\r\n  ", None)

        result = test_dockerfile(
            dockerfile_path='Dockerfile',
            script_path='script.py',
            example_input='input',
            expected_output='expected output'
        )

        assert result.success is True


class TestTestResult:
    """Tests for TestResult dataclass."""

    def test_test_result_success(self):
        """Should create success result."""
        result = TestResult(success=True)
        assert result.success is True
        assert result.build_errors is None

    def test_test_result_with_errors(self):
        """Should create result with error details."""
        result = TestResult(
            success=False,
            build_errors="Build failed",
            runtime_errors="Runtime error"
        )
        assert result.success is False
        assert result.build_errors == "Build failed"
        assert result.runtime_errors == "Runtime error"
