# Usage Examples

## Quick Start

Wrap any script in a Docker container using the AI tool:

```bash
python docker_wrapper.py <script_path> <example_usage_file> [--provider openai|gemini] [--max-retries N]
```

## Included Example Scripts

### 1. Word Reverser (Python)

Reverses the order of words in text input.

**File**: `word_reverser.py`

**Requirements**: Python 3.x

**Usage**:
```bash
python word_reverser.py 'Hello world'
```

**Output**:
```
world Hello
```

**Dockerify**:
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt
```

---

### 2. Line Counter (Bash)

Counts the number of lines in text input.

**File**: `line_counter.sh`

**Requirements**: Bash

**Usage**:
```bash
chmod +x line_counter.sh
./line_counter.sh 'Hello world
This is a test.'
```

**Output**:
```
Line Count: 2
```

**Dockerify**:
```bash
python docker_wrapper.py line_counter.sh examples/line_counter_example.txt
```

---

### 3. Vowel Counter (Node.js)

Counts the number of vowels in text input.

**File**: `vowel_counter.js`

**Requirements**: Node.js

**Usage**:
```bash
node vowel_counter.js 'Hello world'
```

**Output**:
```
Vowel Count: 3
```

**Dockerify**:
```bash
python docker_wrapper.py vowel_counter.js examples/vowel_counter_example.txt
```

---

## Running the Examples

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set API key:
```bash
# Using OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Or using Gemini
export GOOGLE_API_KEY="AIzaSy..."
```

### Basic Examples

#### Example 1: Python Script
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt
```

#### Example 2: Bash Script
```bash
python docker_wrapper.py line_counter.sh examples/line_counter_example.txt
```

#### Example 3: Node.js Script
```bash
python docker_wrapper.py vowel_counter.js examples/vowel_counter_example.txt
```

#### Example 4: With Gemini Provider
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt --provider gemini
```

#### Example 5: With Custom Retries
```bash
python docker_wrapper.py word_reverser.py examples/word_reverser_example.txt --max-retries 5
```

## How to Add a New Script

1. Create your script file (e.g., `my_script.py`)
2. Create an example file (e.g., `examples/my_script_example.txt`):
   ```
   INPUT: <test input>
   EXPECTED_OUTPUT: <expected output>
   ```
3. Run the tool:
   ```bash
   python docker_wrapper.py my_script.py examples/my_script_example.txt
   ```

The tool will:
- Detect the language automatically
- Generate an appropriate Dockerfile
- Test it and fix any issues
- Save the Dockerfile to `generated_dockerfiles/`

## Example Usage File Format

Create a text file with INPUT and EXPECTED_OUTPUT:

```
INPUT: Hello world
EXPECTED_OUTPUT: Vowel Count: 3
```

Or for multi-line input:

```
INPUT: Hello world
This is a test.
EXPECTED_OUTPUT: Line Count: 2
```

## Cost Considerations

- Uses `gpt-4o-mini` model (OpenAI) by default for cost efficiency
- Gemini also available for experiments
- Default max retries: 3 (to stay within budget)
- Each retry uses one API call
- Typical usage: 1-3 API calls per script

## Output Location

Generated Dockerfiles are saved to: `generated_dockerfiles/<script_name>_<timestamp>.Dockerfile`
