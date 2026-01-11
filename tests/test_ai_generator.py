"""Tests for docker_wrapper_agent module - DockerfileAgent with conditional tools."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock

from docker_wrapper_agent import DockerfileAgent, DockerfileOutput
from file_handler import FileReader


def _create_example_file(tmpdir, content="INPUT: test\nEXPECTED_OUTPUT: result"):
    """Helper to create example usage file."""
    example_file = tmpdir.join("example.txt")
    example_file.write(content)
    return str(example_file)


class TestDockerfileAgent:
    """Tests for DockerfileAgent initialization."""

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_agent_openai(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should create OpenAI agent with correct model."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)

                assert mock_agent_class.called
                call_args = mock_agent_class.call_args
                assert 'gpt-4o-mini' in str(call_args)
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_agent_gemini(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should create Gemini agent with correct model."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('gemini', 'test-key', file_reader, f.name, example_file)

                assert mock_agent_class.called
                call_args = mock_agent_class.call_args
                assert 'gemini-2.5-flash' in str(call_args)
            finally:
                os.unlink(f.name)

    def test_agent_invalid_provider(self, tmpdir):
        """Should raise ValueError for invalid provider."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                with pytest.raises(ValueError, match="Unsupported provider"):
                    DockerfileAgent('invalid', 'test-key', file_reader, f.name, example_file)
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_agent_system_prompt_small_file(self, mock_docker_check, mock_agent_class, tmpdir):
        """Small file agent should have test_dockerfile in system prompt when Docker available."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)

                call_kwargs = mock_agent_class.call_args.kwargs
                assert 'system_prompt' in call_kwargs
                assert 'Dockerfile' in call_kwargs['system_prompt']
                assert 'test_dockerfile' in call_kwargs['system_prompt']
                assert 'Docker client is not available' not in call_kwargs['system_prompt']
                # Small file should NOT have search_in_file
                assert 'search_in_file' not in call_kwargs['system_prompt']
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_agent_system_prompt_large_file(self, mock_docker_check, mock_agent_class, tmpdir):
        """Large file agent should have search_in_file and test_dockerfile in system prompt."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\n" + "x" * 200)
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=100)  # Force large
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)

                call_kwargs = mock_agent_class.call_args.kwargs
                assert 'system_prompt' in call_kwargs
                assert 'Dockerfile' in call_kwargs['system_prompt']
                assert 'test_dockerfile' in call_kwargs['system_prompt']
                # Large file should have search_in_file
                assert 'search_in_file' in call_kwargs['system_prompt']
            finally:
                os.unlink(f.name)


class TestDockerfileAgentGenerate:
    """Tests for DockerfileAgent.generate() method."""

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_generate_small_file(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should handle small files by including full content."""
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.output = "FROM python:3.11\nRUN pip install numpy"
        mock_agent.run_sync.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import numpy\nprint('hello')")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)
                result = agent.generate()

                assert result.success
                assert "FROM python" in result.dockerfile
                assert mock_agent.run_sync.called
                # Verify full content is in prompt
                call_args = mock_agent.run_sync.call_args
                prompt = call_args.args[0]
                assert "import numpy" in prompt
                assert "Script content:" in prompt
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_generate_large_file(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should handle large files with search guidance."""
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.output = "FROM python:3.11\nRUN pip install requests"
        mock_agent.run_sync.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import requests\n" + "x" * 200)
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=100)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)
                result = agent.generate()

                assert result.success
                assert "FROM python" in result.dockerfile
                # Verify search guidance is in prompt
                call_args = mock_agent.run_sync.call_args
                prompt = call_args.args[0]
                assert 'search_in_file' in prompt
                assert '^import |^from' in prompt
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_generate_markdown_removal(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should remove markdown code blocks from response."""
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.output = "```dockerfile\nFROM python:3.11\nRUN pip install numpy\n```"
        mock_agent.run_sync.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import numpy")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)
                result = agent.generate()

                assert not result.dockerfile.startswith("```")
                assert "FROM python" in result.dockerfile
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_generate_api_error(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should handle API errors gracefully."""
        mock_agent = Mock()
        mock_agent.run_sync.side_effect = Exception("API error")
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = True

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)
                result = agent.generate()

                assert not result.success
                assert "Generation error" in result.reasoning
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_agent_system_prompt_no_docker(self, mock_docker_check, mock_agent_class, tmpdir):
        """System prompt should indicate Docker is not available when client unavailable."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = False

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)

                call_kwargs = mock_agent_class.call_args.kwargs
                assert 'system_prompt' in call_kwargs
                assert 'Docker client is not available' in call_kwargs['system_prompt']
                assert 'test_dockerfile' not in call_kwargs['system_prompt']
            finally:
                os.unlink(f.name)

    @patch('docker_wrapper_agent.Agent')
    @patch('docker_wrapper_agent.check_docker_available')
    def test_generate_no_docker(self, mock_docker_check, mock_agent_class, tmpdir):
        """Should work without test_dockerfile if Docker unavailable and note it in result."""
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.output = "FROM python:3.11"
        mock_agent.run_sync.return_value = mock_result
        mock_agent_class.return_value = mock_agent
        mock_docker_check.return_value = False

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("print('hello')")
            f.flush()
            try:
                example_file = _create_example_file(tmpdir)
                file_reader = FileReader(f.name, threshold=1000)
                agent = DockerfileAgent('openai', 'test-key', file_reader, f.name, example_file)
                result = agent.generate()

                assert result.success
                assert "FROM python" in result.dockerfile
                assert result.reasoning is not None
                assert "Docker client was not available" in result.reasoning
            finally:
                os.unlink(f.name)
