"""Dockerfile generation agent with conditional tool registration."""

import os
import tempfile
import logging
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

from config import validate_provider, set_api_key
from file_handler import FileReader
from docker_ops import test_dockerfile as run_test_dockerfile, check_docker_available
from prompts import build_file_metadata, build_content_section, build_system_prompt, clean_markdown
from logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


class DockerfileOutput(BaseModel):
    """Output from Dockerfile generation."""
    dockerfile: str
    success: bool = True
    reasoning: Optional[str] = None


class DockerfileAgent:
    """
    Dockerfile generation agent with conditional tool registration.

    Automatically chooses between:
    - Full file content (small files) - simple generation
    - File path + search tool (large files) - efficient searching

    Both agents have test_dockerfile tool for validation.
    Docker testing is skipped if client is unavailable.
    """

    def __init__(
        self,
        provider: str,
        api_key: str,
        file_reader: FileReader,
        script_path: str,
        example_usage_file: str,
    ):
        """
        Initialize agent with conditional tool registration.

        Args:
            provider: LLM provider ('openai' or 'gemini')
            api_key: API key for the provider
            file_reader: FileReader instance
            script_path: Path to the script
            example_usage_file: Path to file containing example input and expected output
        """
        self.file_reader = file_reader
        self.script_path = script_path
        self.example_usage_file = example_usage_file

        # Use search tool for large files
        self.use_search_tool = file_reader.is_large

        # Check if Docker is available
        self.docker_available = check_docker_available()

        model = validate_provider(provider)
        set_api_key(provider, api_key)

        system_prompt = build_system_prompt(self.use_search_tool, self.docker_available)

        self.agent = Agent(
            model=model,
            system_prompt=system_prompt,
        )

        # Set max iterations to prevent infinite loops
        self.max_iterations = 5

        # Register tools conditionally
        self._register_tools()

    def _register_tools(self) -> None:
        """Register tools based on configuration."""

        # Always register test_dockerfile if Docker is available
        if check_docker_available():
            @self.agent.tool
            def test_dockerfile(
                ctx: RunContext[None],
                dockerfile_content: str,
                example_input: str,
                example_output: str,
            ) -> dict:
                """Test a generated Dockerfile by building and running it."""
                logger.info("=" * 70)
                logger.info("🔧 TOOL CALLED: test_dockerfile")
                logger.info("=" * 70)
                logger.info(f"  Input: {example_input[:100]}")
                logger.info(f"  Expected Output: {example_output[:100]}")
                logger.info(f"  Dockerfile length: {len(dockerfile_content)} chars")

                with tempfile.NamedTemporaryFile(mode='w', suffix='Dockerfile', delete=False) as f:
                    f.write(dockerfile_content)
                    dockerfile_path = f.name

                try:
                    logger.info(f"  Building Docker image...")
                    result = run_test_dockerfile(
                        dockerfile_path=dockerfile_path,
                        script_path=self.script_path,
                        example_input=example_input,
                        expected_output=example_output,
                    )

                    logger.info(f"  Build result: {'✓ SUCCESS' if result.success else '✗ FAILED'}")
                    if result.build_errors:
                        logger.info(f"  Build errors: {result.build_errors[:200]}")
                    if result.runtime_errors:
                        logger.info(f"  Runtime errors: {result.runtime_errors[:200]}")
                    logger.info("=" * 70)

                    return {
                        "success": result.success,
                        "build_errors": result.build_errors,
                        "runtime_errors": result.runtime_errors,
                        "output_diff": result.output_diff,
                        "actual_output": result.actual_output,
                    }
                finally:
                    try:
                        os.unlink(dockerfile_path)
                    except Exception:
                        pass

        # Conditionally register search_in_file for large files
        if self.use_search_tool:
            @self.agent.tool
            def search_in_file(
                ctx: RunContext[None],
                pattern: str,
                context_lines: int = 2,
            ) -> list[dict]:
                """Search for patterns in the script file without loading full content."""
                logger.info("=" * 70)
                logger.info("🔍 TOOL CALLED: search_in_file")
                logger.info("=" * 70)
                logger.info(f"  Pattern: {pattern}")
                logger.info(f"  Context lines: {context_lines}")

                results = self.file_reader.search_in_file(pattern, context_lines)

                logger.info(f"  Results: Found {len(results)} matches")
                for i, result in enumerate(results[:3], 1):  # Show first 3
                    logger.info(f"    {i}. Line {result['line_num']}: {result['content'][:60]}")
                if len(results) > 3:
                    logger.info(f"    ... and {len(results) - 3} more matches")
                logger.info("=" * 70)

                return results

    def generate(self) -> DockerfileOutput:
        """
        Generate Dockerfile with conditional tool usage.

        For small files: Uses full content
        For large files: Uses search_in_file tool to find dependencies

        Both agents have test_dockerfile tool for validation.

        Returns:
            DockerfileOutput with generated Dockerfile
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING DOCKERFILE GENERATION")
        logger.info("=" * 70)
        logger.info(f"  Script: {self.script_path}")
        logger.info(f"  File size: {self.file_reader.size / 1024:.1f}KB")
        logger.info(f"  File type: {'LARGE (uses search_in_file)' if self.use_search_tool else 'SMALL (full content)'}")
        logger.info(f"  Docker available: {self.docker_available}")

        # Read example file content for the prompt
        with open(self.example_usage_file, 'r', encoding='utf-8') as f:
            example_content = f.read()

        file_metadata = build_file_metadata(self.file_reader, self.script_path)
        content_section = build_content_section(self.file_reader, self.use_search_tool)

        if self.use_search_tool:
            # Large file prompt with search guidance
            prompt = f"""{file_metadata}

{content_section}

Search for:
1. All imports/dependencies (search for: ^import |^from |^require|package\\.json|requirements\\.txt|Gemfile|Cargo\\.toml)
2. System packages needed (search for: apt-get|apk|brew|yum)
3. Entry point/main function (search for: ^if __name__|def main|function main|^func main)

Example usage:
{example_content}

Generate a Dockerfile that allows running this script with the same command-line interface.
Search for dependencies first, then generate. Test using the test_dockerfile tool and iterate if needed."""
        else:
            # Small file prompt with full content
            prompt = f"""{file_metadata}

{content_section}

Example usage:
{example_content}

Generate a Dockerfile that allows running this script with the same command-line interface.
Test it using the test_dockerfile tool and iterate if needed."""

        try:
            logger.info(f"  Calling agent with prompt...")
            result = self.agent.run_sync(prompt)

            # Extract content
            if hasattr(result, "output"):
                dockerfile_content = str(result.output)
            elif hasattr(result, "data"):
                dockerfile_content = str(result.data)
            else:
                dockerfile_content = str(result)

            dockerfile_content = clean_markdown(dockerfile_content)

            logger.info("=" * 70)
            logger.info("✓ GENERATION COMPLETE")
            logger.info("=" * 70)
            logger.info(f"  Dockerfile lines: {len(dockerfile_content.splitlines())}")
            logger.info(f"  Dockerfile size: {len(dockerfile_content)} chars")

            # Add note if Docker testing was not available
            reasoning = None
            if not self.docker_available:
                reasoning = "Dockerfile generated successfully, but Docker client was not available for testing."
                logger.info("  ⚠️  Docker not available for testing")

            # Check if we hit max iterations
            # Note: This would be returned in result if available
            logger.info("=" * 70)
            return DockerfileOutput(
                dockerfile=dockerfile_content.strip(),
                success=True,
                reasoning=reasoning,
            )
        except Exception as e:
            logger.error("=" * 70)
            logger.error("✗ GENERATION FAILED")
            logger.error("=" * 70)
            logger.error(f"  Error: {str(e)}")
            logger.error("=" * 70)
            return DockerfileOutput(
                dockerfile="",
                success=False,
                reasoning=f"Generation error: {str(e)}",
            )
