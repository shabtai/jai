"""Prompts and prompt generation for Dockerfile generation agents."""

from pathlib import Path


def build_file_metadata(file_reader, script_path: str) -> str:
    """Build file metadata string for prompts."""
    filename = Path(script_path).name
    size_str = (
        f"{file_reader.size / 1024:.1f}KB"
        if file_reader.size >= 1024
        else f"{file_reader.size}B"
    )
    return (
        f"File: {filename}\n"
        f"Size: {size_str}\n"
        f"Lines: {file_reader.line_count}"
    )


def build_content_section(file_reader, use_search_tool: bool) -> str:
    """Build content section for prompt based on file size and tool availability."""
    if use_search_tool:
        filename = Path(file_reader.file_path).name
        return f"File path available for search_in_file tool. File extension: {filename}"
    else:
        return f"""Script content:
```
{file_reader.get_content()}
```"""


def build_system_prompt(use_search_tool: bool, docker_available: bool, provider: str = None) -> str:
    """Build system prompt based on whether search tool and Docker are available."""
    base_instructions = """You are an expert Dockerfile generation assistant.

CRITICAL: Your response MUST contain ONLY a Dockerfile wrapped in a code block (```dockerfile ... ```). No explanations, no reasoning, no other text before or after.

Generate an optimal Dockerfile that:
1. Uses the appropriate base image for the language
2. Installs all required dependencies
3. Copies the script into the container and sets the correct entry point
4. Handles command-line arguments correctly
5. Follows Docker best practices (minimal layers, efficient caching)"""

    if docker_available:
        test_instructions = "\n\nYou have access to test_dockerfile tool to validate your Dockerfile. Use it to test and iterate until the test passes."
    else:
        test_instructions = "\n\nDocker client is not available. Generate the best Dockerfile you can based on the script analysis. Testing will not be possible."

    if use_search_tool:
        search_instructions = "\n\nYou have access to search_in_file tool to find imports, dependencies, and entry points in files. Use it to efficiently find what you need."
        return base_instructions + search_instructions + test_instructions
    else:
        return base_instructions + test_instructions


def extract_dockerfile(content: str) -> str:
    """Extract Dockerfile from LLM response, handling markdown code blocks."""
    if not isinstance(content, str):
        return content

    lines = content.split("\n")

    # Find the Dockerfile code block (between ``` markers)
    in_dockerfile_block = False
    dockerfile_lines = []
    found_block = False

    for line in lines:
        # Check for opening code block marker
        if line.strip().startswith("```"):
            if not found_block:  # First code block found
                in_dockerfile_block = True
                found_block = True
                # Skip the opening marker and any language specifier (e.g., ```dockerfile)
                continue
            else:
                # Closing code block marker
                in_dockerfile_block = False
                break

        # Collect lines within the code block
        if in_dockerfile_block:
            dockerfile_lines.append(line)

    # If we found a code block, return its content
    if dockerfile_lines:
        return "\n".join(dockerfile_lines).strip()

    # Fallback: if no code blocks found, try the old method
    if content.startswith("```"):
        lines = [l for l in lines if not l.startswith("```")]
        return "\n".join(lines).strip()

    return content


def clean_markdown(content: str) -> str:
    """Remove markdown code block markers from response. (Deprecated - use extract_dockerfile)"""
    return extract_dockerfile(content)
