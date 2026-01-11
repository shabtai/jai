#!/usr/bin/env python3
"""
CLI tool for generating and testing Dockerfiles using AI agents.

Uses DockerfileAgent which automatically:
- Includes full file content for small files
- Uses search_in_file tool for large files to find dependencies
- Tests Docker images with test_dockerfile tool
- Iterates internally through agentic loop until success
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

from docker_wrapper_agent import DockerfileAgent
from file_handler import FileReader
from security import validate_file_path, check_file_size, detect_prompt_injection


def save_dockerfile(dockerfile_content: str, script_path: str) -> str:
    """
    Save generated Dockerfile to generated_dockerfiles directory.

    Args:
        dockerfile_content: The Dockerfile content to save
        script_path: Path to the script file (used for naming)

    Returns:
        Path to the saved Dockerfile
    """
    # Create generated_dockerfiles directory if it doesn't exist
    output_dir = Path("generated_dockerfiles")
    output_dir.mkdir(exist_ok=True)

    # Generate filename based on script name and timestamp
    script_name = Path(script_path).stem  # e.g., "word_reverser" from "word_reverser.py"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{script_name}_{timestamp}.Dockerfile"
    output_path = output_dir / output_filename

    # Write Dockerfile
    with open(output_path, 'w') as f:
        f.write(dockerfile_content)

    return str(output_path)


def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Generate and test Dockerfiles using AI with autonomous tool-based iteration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using OpenAI with a Python script
  export OPENAI_API_KEY="sk-..."
  python3 docker_wrapper.py scripts/word_reverser.py examples/word_reverser_example.txt

  # Using Gemini with a Bash script
  export GOOGLE_API_KEY="AIzaSy..."
  python3 docker_wrapper.py scripts/line_counter.sh examples/line_counter_example.txt --provider gemini
        """
    )
    parser.add_argument(
        'script_path',
        help='Path to the script file to wrap'
    )
    parser.add_argument(
        'example_usage_file',
        help='Path to file containing example usage (input and expected output)'
    )
    parser.add_argument(
        '--provider',
        choices=['openai', 'gemini'],
        default='openai',
        help='LLM provider to use (default: openai)'
    )

    args = parser.parse_args()

    # Validate files with security checks
    try:
        script_path = validate_file_path(args.script_path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        example_usage_file = validate_file_path(args.example_usage_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Check file size
    is_valid, size = check_file_size(script_path, max_size_bytes=500 * 1024)
    if not is_valid:
        print(f"Error: Script too large ({size} bytes). Maximum: 500KB")
        sys.exit(1)

    # Load script with FileReader
    print(f"Reading script: {script_path}")
    try:
        file_reader = FileReader(script_path, threshold=100 * 1024)  # 100KB threshold
        print(f"✓ Script loaded ({file_reader.size} bytes, {file_reader.line_count} lines)")
        file_size_str = "LARGE" if file_reader.is_large else "SMALL"
        print(f"  File type: {file_size_str}")

        # Check for prompt injection in script content (if small enough to check)
        if not file_reader.is_large:
            try:
                with open(script_path, 'r') as f:
                    script_content = f.read()
                if detect_prompt_injection(script_content):
                    print(f"⚠️  Warning: Script contains potential prompt injection patterns")
            except Exception:
                pass  # Silently skip if detection fails
    except Exception as e:
        print(f"✗ Error loading script: {e}")
        sys.exit(1)

    # Validate example usage file exists
    print(f"\nReading example usage: {example_usage_file}")
    if not os.path.exists(example_usage_file):
        print(f"✗ Error: Example usage file not found: {example_usage_file}")
        sys.exit(1)
    print(f"✓ Example usage file found")

    # Check for prompt injection in example usage file
    try:
        with open(example_usage_file, 'r') as f:
            example_content = f.read()
        if detect_prompt_injection(example_content):
            print(f"⚠️  Warning: Example file contains potential prompt injection patterns")
    except Exception:
        pass  # Silently skip if detection fails

    # Get API key from environment
    if args.provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("Error: OPENAI_API_KEY environment variable required")
            sys.exit(1)
    elif args.provider == 'gemini':
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("Error: GOOGLE_API_KEY environment variable required")
            sys.exit(1)

    # Verify and display summary before starting
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    print(f"Script: {Path(script_path).name}")
    print(f"  Size: {file_reader.size} bytes ({file_size_str})")
    print(f"  Lines: {file_reader.line_count}")
    print(f"\nExample usage file: {Path(example_usage_file).name}")
    print(f"\nProvider: {args.provider.upper()}")
    from docker_ops import check_docker_available
    docker_status = "Available" if check_docker_available() else "Not available"
    print(f"Docker: {docker_status}")
    print(f"{'='*70}\n")

    # Create and run agent with tool-based testing
    print(f"Starting DockerfileAgent ({args.provider.upper()})")
    agent_type = "with search_in_file tool" if file_reader.is_large else "with full file content"
    print(f"Agent mode: {agent_type}")
    print(f"Agent will: generate → test (via tools) → iterate\n")

    try:
        agent = DockerfileAgent(
            provider=args.provider,
            api_key=api_key,
            file_reader=file_reader,
            script_path=script_path,
            example_usage_file=example_usage_file,
        )
        result = agent.generate()

        if result.success and result.dockerfile:
            print("\n" + "="*70)
            print("✓ SUCCESS! Agent generated working Dockerfile")
            print("="*70)
            print("\nGenerated Dockerfile:")
            print("-" * 70)
            print(result.dockerfile)
            print("-" * 70)

            # Save Dockerfile to file
            saved_path = save_dockerfile(result.dockerfile, script_path)
            print(f"\n✓ Dockerfile saved to: {saved_path}")
            print(f"  Lines: {len(result.dockerfile.split(chr(10)))}")
            print(f"  Size: {len(result.dockerfile)} bytes")
            sys.exit(0)
        else:
            print("\n" + "="*70)
            print("✗ FAILED: Agent could not generate working Dockerfile")
            print("="*70)
            if result.reasoning:
                print(f"Reason: {result.reasoning}")
            sys.exit(1)

    except Exception as e:
        print(f"\n✗ Agent error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
