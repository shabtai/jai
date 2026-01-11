# Architecture & Implementation Guide

## Project Overview

This project implements an AI-powered tool that generates Dockerfiles for scripts using OpenAI/Gemini APIs, with comprehensive security hardening, multi-provider support, and large file handling capabilities.

## Core Components

### 1. **Security Module** (`security.py`)
Centralized security validation and sanitization:
- **`validate_file_path()`**: Prevents path traversal attacks, validates file existence
- **`check_file_size()`**: Enforces file size limits (default 500KB)
- **`detect_prompt_injection()`**: Detects malicious patterns in user input using regex
- **`sanitize_docker_input()`**: Escapes special characters for Docker contexts

### 2. **File Handler** (`file_handler.py`)
Smart file reading with support for large files:
- **`FileReader` class**: Intelligently loads small files (<100KB) completely, uses search tool for large files
- **`search_in_file(pattern)`**: Regex-based search that works without loading full file
- **Language detection**: Supports Python, JavaScript, Bash, Go, Rust, Ruby, Perl, PHP

### 3. **Docker Wrapper Agent** (`docker_wrapper_agent.py`)
Vendor-agnostic LLM integration using PydanticAI:
- **`create_agent(provider, api_key)`**: Creates agents for OpenAI or Gemini
- **`generate_dockerfile()`**: Orchestrates Dockerfile generation with tool use
- **Tool integration**: Registers `search_in_file` tool for LLM use
- **Adaptive prompts**: Different behavior for small vs large files

### 4. **Docker Operations** (`docker_ops.py`)
Docker interaction and testing:
- **`check_docker_available()`**: Verifies Docker daemon is running
- **`build_image()`**: Builds Docker image with error handling
- **`run_test()`**: Executes container with resource limits
- **Resource limits**: Memory (512MB), CPU (1 core), Network (disabled), PIDs (100 max)

### 5. **CLI Tools**
- **`docker_wrapper.py`**: Advanced CLI with file saving and detailed logging
- Includes security validation, provider selection, and API key handling via environment variables only

## Key Architectural Decisions

### Vendor-Agnostic LLM Support
**Decision**: Use PydanticAI instead of direct OpenAI SDK

**Benefits**:
- Single API for OpenAI and Gemini
- Easy to add more providers (Claude, etc.)
- Built-in tool calling support
- Automatic retry logic

### Smart File Handling Strategy
**Decision**: Use threshold-based approach with search tool

**Benefits**:
- Small files get full context (better generation)
- Large files use search tool (stays within token limits)
- Works for all file types without per-language parsing
- LLM controls what it needs to see

### Simple, Effective Security
**Decision**: Regex-based injection detection rather than ML models

**Benefits**:
- Minimalistic, no heavy dependencies
- Fast and deterministic
- Clear patterns to detect
- Easy to extend

## Large File Handling

### How It Works

1. **File Detection**
   - FileReader checks file size
   - Files > 100KB marked as "large"
   - Small files: Content loaded immediately
   - Large files: Only path stored

2. **Small Files**
   - Full content sent to LLM in prompt
   - LLM has complete context
   - Single API call per attempt

3. **Large Files**
   - File metadata sent to LLM
   - `search_in_file(pattern)` tool registered
   - LLM calls tool to search for imports, dependencies, entry points
   - Typically 2-5 tool calls per generation

### Example Flow

```
User provides 300KB Python script
↓
FileReader detects: is_large=True
↓
Agent receives: File metadata + search tool
↓
Agent thinks: "I need imports"
↓
Agent calls: search_in_file("^import |^from")
↓
Tool returns: [import numpy, import pandas, ...]
↓
Agent generates: Dockerfile with correct base image and dependencies
```

## Security Features Implemented

✅ **Path Traversal Prevention**
- Validates all file paths against traversal attacks
- Resolves paths to absolute and checks against base directories

✅ **File Size Limits**
- Enforces 500KB maximum script size
- Prevents memory exhaustion

✅ **Prompt Injection Detection**
- Detects "ignore instructions" patterns
- Detects excessive shell metacharacters
- Case-insensitive detection

✅ **API Key Protection**
- Removed `--api-key` CLI argument (visible in process list)
- Forces use of environment variables only

✅ **Container Resource Limits**
- Memory: 512MB max
- CPU: 1 core max
- Network: Disabled
- Processes: 100 max

✅ **Input Sanitization**
- Escapes special characters
- Removes null bytes
- Preserves UTF-8 printable characters

## Dependencies

```
openai>=1.0.0              # OpenAI API
pydantic-ai>=0.0.1         # Multi-provider LLM support
pytest>=7.0.0              # Testing framework
google-generativeai>=0.3.0 # Gemini API support
```

## File Structure

```
jai/
├── docs/
│   ├── ARCHITECTURE.md     # This file
│   ├── EXAMPLES.md         # Usage examples
│   └── TESTING.md          # Testing and verification
├── security.py             # Security validation & sanitization
├── file_handler.py         # Smart file reading
├── docker_wrapper_agent.py # LLM integration agent
├── docker_ops.py           # Docker operations
├── config.py               # Configuration management
├── docker_wrapper.py       # CLI tool
├── requirements.txt        # Dependencies
├── tests/
│   ├── test_security.py
│   ├── test_file_handler.py
│   ├── test_ai_generator.py
│   ├── test_docker_ops.py
│   └── test_integration.py
├── word_reverser.py        # Example script
├── line_counter.sh         # Example script
├── vowel_counter.js        # Example script
└── examples/               # Example usage files
```

## Future Enhancements

- Add Claude API support (easy with current PydanticAI architecture)
- Implement API usage tracking and cost estimation
- Add caching layer for repeated requests
- ML-based security validation
- Configurable resource limits per provider
- Support for multi-file scripts
- Integrated credential manager support
