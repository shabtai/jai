# AI-Powered Docker Wrapper Tool

An intelligent tool that uses AI to automatically generate, build, and test Docker containers for any script in any language.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up API Key

Choose your AI provider:

**OpenAI (Default)**:
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Gemini**:
```bash
export GOOGLE_API_KEY="AIzaSy-your-api-key-here"
```

### 3. Run the Tool

```bash
python docker_wrapper.py <script_path> <example_usage_file> [options]
```

## Usage Examples

### Example 1: Python Script with OpenAI
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt
```

### Example 2: Bash Script
```bash
python docker_wrapper.py line_counter.sh examples/line_counter_example.txt
```

### Example 3: Node.js Script
```bash
python docker_wrapper.py vowel_counter.js examples/vowel_counter_example.txt
```

### Example 4: Using Gemini Provider
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt --provider gemini
```

### Example 5: Custom Retry Attempts
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt --max-retries 5
```

## Command-Line Arguments

```
Usage: python docker_wrapper.py <script_path> <example_usage_file> [options]

Arguments:
  script_path              Path to the script file to wrap
  example_usage_file      Path to file with example input/output

Options:
  --provider {openai,gemini}  LLM provider to use (default: openai)
  --max-retries N          Maximum retry attempts if generation fails (default: 3)
  --help                   Show this help message
```

## Creating an Example Usage File

Create a `.txt` file with the following format:

```
INPUT: <test input>
EXPECTED_OUTPUT: <expected output>
```

**Example for `word_reverser_example.txt`:**
```
INPUT: Hello world
EXPECTED_OUTPUT: world Hello
```

**Example for `line_counter_example.txt`:**
```
INPUT: Hello
This is a test.
EXPECTED_OUTPUT: Line Count: 2
```

**Example for `vowel_counter_example.txt`:**
```
INPUT: Hello world
EXPECTED_OUTPUT: Vowel Count: 3
```

## How It Works

The tool follows this workflow:

1. **Validates Input**
   - Checks script exists and is readable
   - Validates example file format
   - Runs security checks for prompt injection

2. **Analyzes Script**
   - Detects programming language
   - For small files: reads full content
   - For large files (>100KB): uses smart search tool to find dependencies

3. **Generates Dockerfile**
   - AI analyzes script dependencies
   - Generates optimized Dockerfile
   - Tests generation immediately

4. **Tests & Iterates**
   - Builds Docker image
   - Runs container with example input
   - Compares output with expected result
   - If test fails: AI analyzes errors and fixes Dockerfile
   - Retries up to `--max-retries` times

5. **Saves Result**
   - Dockerfile saved to `generated_dockerfiles/` directory
   - Displays final Dockerfile content

## Output

### Success
```
✓ Dockerfile generation successful!
Saved to: generated_dockerfiles/word_reverser_20250111_120000.Dockerfile

FROM python:3.11-slim
...
```

### Failure
```
✗ Generation failed after 3 retries
Last error: ...
```

## Requirements

- **Python** 3.8+
- **Docker** (must be running)
- **API Key** for OpenAI or Gemini
- **Internet connection** for API calls

## Adding a New Script

To wrap a new script:

1. Create your script file (e.g., `my_tool.py`)

2. Create example file at `examples/my_tool_example.txt`:
   ```
   INPUT: test input
   EXPECTED_OUTPUT: expected output
   ```

3. Run:
   ```bash
   python docker_wrapper.py my_tool.py examples/my_tool_example.txt
   ```

That's it! The tool handles the rest.

## Troubleshooting

### "Docker daemon is not running"
```bash
# Start Docker
docker ps  # Should show "Cannot connect" then start Docker
# Or use: open -a Docker (on macOS)
```

### "API key not found"
```bash
# Verify environment variable is set
echo $OPENAI_API_KEY    # Should show your key (first 10 chars)
echo $GOOGLE_API_KEY    # For Gemini
```

### "Script contains prompt injection patterns"
This is a security warning. The script contains patterns that look suspicious. Review the script and try again if safe.

### Generation times out
Some scripts take longer. Increase retries:
```bash
python docker_wrapper.py script.py example.txt --max-retries 5
```

## Cost Considerations

- **OpenAI**: Uses `gpt-4o-mini` (very cost-efficient)
- **Gemini**: Uses free tier (if available)
- Typical cost: $0.01-0.05 per script
- First generation often succeeds on first try

## Features

✅ Multi-language support (Python, Bash, JavaScript, Go, Rust, Ruby, Perl, PHP)
✅ Automatic dependency detection
✅ Iterative fixing (retries if test fails)
✅ LLM vendor-agnostic (OpenAI or Gemini)
✅ Security hardening (prompt injection detection, path validation)
✅ Large file support (efficient handling of 100KB+ scripts)
✅ Comprehensive testing framework

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and implementation details
- **[Examples Guide](docs/EXAMPLES.md)** - Detailed usage examples for all scripts
- **[Testing Guide](docs/TESTING.md)** - How to run tests and verify functionality

## Original Challenge

This project implements the Jit-ai-challenge:
- ✅ AI-powered Dockerfile generation
- ✅ Automatic build and testing
- ✅ Multi-provider support (OpenAI, Gemini)
- ✅ Security hardening and input validation
- ✅ Comprehensive test suite (~80% code coverage)
