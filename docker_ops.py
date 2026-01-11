"""Docker operations for building, running, and testing Docker images."""

import subprocess
import tempfile
import shutil
import os
import uuid
import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


def check_docker_available() -> bool:
    """Check if Docker daemon is running and accessible."""
    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


@dataclass
class TestResult:
    """Result of testing a Dockerfile."""
    success: bool
    build_errors: Optional[str] = None
    runtime_errors: Optional[str] = None
    actual_output: Optional[str] = None
    output_diff: Optional[str] = None


def build_image(dockerfile_path: str, script_path: str, image_name: str) -> Tuple[bool, Optional[str]]:
    """
    Build a Docker image from a Dockerfile.
    
    Args:
        dockerfile_path: Path to the Dockerfile
        script_path: Path to the script file to copy into build context
        image_name: Name for the Docker image
        
    Returns:
        Tuple of (success: bool, error_log: Optional[str])
    """
    dockerfile_dir = os.path.dirname(dockerfile_path)
    script_filename = os.path.basename(script_path)
    script_dest = os.path.join(dockerfile_dir, script_filename)
    
    # Copy script to Dockerfile directory
    shutil.copy2(script_path, script_dest)
    
    try:
        result = subprocess.run(
            ['docker', 'build', '-t', image_name, '-f', dockerfile_path, dockerfile_dir],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_log = f"Build failed with exit code {result.returncode}\n"
            error_log += f"STDOUT:\n{result.stdout}\n"
            error_log += f"STDERR:\n{result.stderr}\n"
            return False, error_log
        
        return True, None
    except subprocess.TimeoutExpired:
        return False, "Docker build timed out after 120 seconds"
    except Exception as e:
        return False, f"Error during Docker build: {str(e)}"


def run_container(image_name: str, input_args: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Run a Docker container with the given input as command-line argument and resource limits.

    Args:
        image_name: Name of the Docker image to run
        input_args: Input to pass to the container as command-line argument

    Returns:
        Tuple of (success: bool, output: Optional[str], error_log: Optional[str])
    """
    try:
        # Build command with resource limits and input as argument
        cmd = [
            'docker', 'run',
            '--rm',
            '--memory=512m',            # Max 512MB RAM
            '--cpus=1.0',               # Max 1 CPU
            '--network=none',           # No network access
            '--pids-limit=100',         # Max 100 processes
            image_name,
            input_args                  # Pass input as command-line argument
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        stdout = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""

        if result.returncode != 0:
            error_log = f"Container exited with code {result.returncode}\n"
            if stderr:
                error_log += f"STDERR:\n{stderr}\n"
            if stdout:
                error_log += f"STDOUT:\n{stdout}\n"
            return False, stdout, error_log

        return True, stdout, None
    except subprocess.TimeoutExpired:
        return False, None, "Container execution timed out after 30 seconds"
    except Exception as e:
        return False, None, f"Error running container: {str(e)}"


def normalize_output(output: str) -> str:
    """Normalize output for comparison (strip whitespace, handle newlines)."""
    return output.strip().replace('\r\n', '\n').replace('\r', '\n')


def test_dockerfile(
    dockerfile_path: str,
    script_path: str,
    example_input: str,
    expected_output: str
) -> TestResult:
    """
    Test tool used by the agent to validate a generated Dockerfile.

    This function:
    1. Checks Docker daemon is available
    2. Builds the Docker image
    3. Runs the container with example input
    4. Validates the output matches expected output

    Args:
        dockerfile_path: Path to the Dockerfile
        script_path: Path to the script file
        example_input: Example input to test with (provided by LLM)
        expected_output: Expected output (provided by LLM)

    Returns:
        TestResult object with success status and error details
    """
    logger.info("\n" + "="*70)
    logger.info("📦 DOCKER TEST STARTED")
    logger.info("="*70)
    logger.info(f"  Dockerfile: {dockerfile_path}")
    logger.info(f"  Script: {script_path}")

    # Check Docker is available
    if not check_docker_available():
        logger.error("  ✗ Docker daemon not available")
        return TestResult(
            success=False,
            build_errors="Docker daemon is not running or not accessible"
        )

    logger.info("  ✓ Docker daemon available")

    # Generate unique image name
    image_name = f"test-{uuid.uuid4().hex[:8]}"
    logger.info(f"  Image name: {image_name}")

    # Step 1: Build the image
    logger.info("  Step 1: Building Docker image...")
    build_success, build_errors = build_image(dockerfile_path, script_path, image_name)
    if not build_success:
        logger.error(f"  ✗ Build failed: {build_errors[:100]}")
        return TestResult(
            success=False,
            build_errors=build_errors
        )
    logger.info("  ✓ Build successful")

    # Step 2: Run the container
    logger.info("  Step 2: Running container...")
    run_success, actual_output, runtime_errors = run_container(image_name, example_input)
    if not run_success:
        logger.error(f"  ✗ Runtime error: {runtime_errors[:100]}")
        # Cleanup image
        _cleanup_image(image_name)
        return TestResult(
            success=False,
            runtime_errors=runtime_errors
        )
    logger.info(f"  ✓ Container ran successfully")
    logger.info(f"  Output: {(actual_output or '')[:60]}")

    # Step 3: Validate output
    logger.info("  Step 3: Validating output...")
    normalized_actual = normalize_output(actual_output or "")
    normalized_expected = normalize_output(expected_output)

    # Check if expected output is contained in actual output (lenient check)
    # This allows for actual output to have more content than expected
    if normalized_expected and normalized_expected not in normalized_actual:
        output_diff = f"Expected:\n{normalized_expected}\n\nActual:\n{normalized_actual}"
        logger.error("  ✗ Output validation failed")
        logger.error(f"  Expected: {normalized_expected[:60]}")
        logger.error(f"  Actual: {normalized_actual[:60]}")
        # Cleanup image
        _cleanup_image(image_name)
        logger.info("="*70)
        return TestResult(
            success=False,
            actual_output=actual_output,
            output_diff=output_diff
        )

    # Success - cleanup image
    logger.info("  ✓ Output validation passed")
    _cleanup_image(image_name)
    logger.info("=" * 70)
    logger.info("✓ DOCKER TEST PASSED")
    logger.info("=" * 70)

    return TestResult(success=True)


def _cleanup_image(image_name: str):
    """Internal helper to cleanup Docker image with logging."""
    try:
        subprocess.run(
            ['docker', 'rmi', '-f', image_name],
            capture_output=True,
            timeout=10
        )
    except Exception as e:
        # Log but don't fail
        pass
