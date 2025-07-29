# Automated CircleCI Testing System

This system allows you to automatically upload your selected code and test files to CircleCI for testing.

## How It Works

1. **Select your files**: Place your code page (`.py` file with functions) and test input (`.py` file with test functions) in the same directory
2. **Run the script**: Execute `python auto_upload_to_circleci.py`
3. **Get results**: View test results in CircleCI dashboard

## Setup (One-time only)

### First Time Setup
```bash
python auto_upload_to_circleci.py
```
- Enter your CircleCI API token
- Enter your project slug (e.g., `github/username/repo`)
- Configuration will be saved for future use

### Getting CircleCI API Token
1. Go to [CircleCI Personal API Tokens](https://app.circleci.com/settings/user/tokens)
2. Create a new token
3. Copy the token for use in the script

## Usage

### Step 1: Prepare Your Files
Place your selected files in the project directory:
```
your-project/
├── python_sample.py     ← Your code page
├── input_file.py        ← Your test input
└── auto_upload_to_circleci.py
```

### Step 2: Run the Script
```bash
python auto_upload_to_circleci.py
```

### Step 3: View Results
- Check the CircleCI dashboard for test results
- Results will show:
  - Number of test cases
  - Number of tests passed
  - Number of tests failed

## File Requirements

### Code Files
- Must be `.py` files
- Must contain function definitions (`def `)
- Will be automatically detected

### Test Files
- Must be `.py` files
- Must contain test functions (`def test_` or `import pytest`)
- Will be automatically detected

## Expected Output

```
🤖 AUTOMATED CIRCLECI UPLOAD
==================================================
📁 Looking for your selected code page and test input files...
📄 Found code files: ['python_sample.py']
🧪 Found test files: ['input_file.py']

🎯 Selected files for testing:
   📄 Code page: python_sample.py
   🧪 Test input: input_file.py

🚀 Starting automated upload and testing...
🚀 Uploading selected files to CircleCI...
✅ Pipeline triggered successfully!
🔗 View pipeline: https://app.circleci.com/pipelines/github/username/repo/[pipeline-id]

🎉 SUCCESS! Your selected files have been uploaded and testing has started.
📊 Check the CircleCI dashboard for test results:
🔗 https://app.circleci.com/pipelines/github/username/repo/[pipeline-id]

📋 Expected test results will show:
   - Number of test cases
   - Number of tests passed
   - Number of tests failed
```

## Troubleshooting

### No files found
- Make sure your files are `.py` files
- Ensure code files contain function definitions
- Ensure test files contain test functions

### Upload failed
- Check your CircleCI API token
- Verify your project slug is correct
- Ensure you have access to the CircleCI project

## Files in This Project

- `auto_upload_to_circleci.py` - Main automation script
- `run_dynamic_tests.py` - Test result parser
- `.circleci/config.yml` - CircleCI pipeline configuration
- `circleci_config.json` - Saved configuration (created after first run)