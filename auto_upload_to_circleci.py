#!/usr/bin/env python3
"""
Automated CircleCI Upload - Works with selected code page and test input files
"""

import os
import sys
import json
import requests
import base64
import glob

def find_selected_files():
    """
    Find the code page and test input files that user has selected
    """
    # Look for common patterns in your workflow
    code_files = []
    test_files = []
    
    # Find all .py files
    py_files = glob.glob("*.py")
    
    for file in py_files:
        # Skip our utility scripts
        if file in ['auto_upload_to_circleci.py', 'upload_to_circleci.py', 'run_dynamic_tests.py', 'download_from_confluence.py', 'dynamic_test_runner.py']:
            continue
            
        # Check if it's a test file (contains test functions)
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'def test_' in content or 'import pytest' in content:
                    test_files.append(file)
                elif 'def ' in content and not file.startswith('test_'):
                    # This is likely a code file with functions
                    code_files.append(file)
        except:
            continue
    
    return code_files, test_files

def get_circleci_config():
    """
    Get CircleCI configuration from environment or config file
    """
    # Try environment variables first
    token = os.getenv('CIRCLECI_TOKEN')
    project_slug = os.getenv('CIRCLECI_PROJECT_SLUG')
    
    # If not in environment, try config file
    if not token or not project_slug:
        config_file = 'circleci_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    token = config.get('token')
                    project_slug = config.get('project_slug')
            except:
                pass
    
    return token, project_slug

def upload_files_to_circleci(code_file_path, test_file_path, circleci_token, project_slug):
    """
    Upload selected code and test files to CircleCI and trigger pipeline
    """
    try:
        print("🚀 Uploading selected files to CircleCI...")
        
        # Read the selected files
        with open(code_file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        with open(test_file_path, 'r', encoding='utf-8') as f:
            test_content = f.read()
        
        # Trigger CircleCI pipeline with the selected files
        trigger_url = f"https://circleci.com/api/v2/project/{project_slug}/pipeline"
        
        headers = {
            'Circle-Token': circleci_token,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'parameters': {
                'code_content': base64.b64encode(code_content.encode()).decode(),
                'test_content': base64.b64encode(test_content.encode()).decode(),
                'code_filename': os.path.basename(code_file_path),
                'test_filename': os.path.basename(test_file_path)
            }
        }
        
        response = requests.post(trigger_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            pipeline_data = response.json()
            pipeline_id = pipeline_data['id']
            print(f"✅ Pipeline triggered successfully!")
            print(f"🔗 View pipeline: https://app.circleci.com/pipelines/{project_slug}/{pipeline_id}")
            return pipeline_id
        else:
            print(f"❌ Failed to trigger pipeline: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading files: {e}")
        return None

def create_config_file():
    """
    Create a config file for CircleCI credentials (one-time setup)
    """
    print("📝 Setting up CircleCI configuration (one-time setup)...")
    
    token = input("Enter your CircleCI API token: ").strip()
    project_slug = input("Enter your CircleCI project slug (e.g., github/username/repo): ").strip()
    
    config = {
        'token': token,
        'project_slug': project_slug
    }
    
    with open('circleci_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved to circleci_config.json")
    return token, project_slug

def main():
    """
    Main function - automated upload of selected code and test files
    """
    print("🤖 AUTOMATED CIRCLECI UPLOAD")
    print("=" * 50)
    print("📁 Looking for your selected code page and test input files...")
    
    # Step 1: Find the selected files
    code_files, test_files = find_selected_files()
    
    if not code_files:
        print("❌ No code files found.")
        print("💡 Make sure you have selected a code page (.py file with functions)")
        return
    
    if not test_files:
        print("❌ No test files found.")
        print("💡 Make sure you have selected a test input file (.py file with test functions)")
        return
    
    print(f"📄 Found code files: {code_files}")
    print(f"🧪 Found test files: {test_files}")
    
    # Step 2: Select the files (use first ones found)
    code_file = code_files[0]
    test_file = test_files[0]
    
    print(f"\n🎯 Selected files for testing:")
    print(f"   📄 Code page: {code_file}")
    print(f"   🧪 Test input: {test_file}")
    
    # Step 3: Get CircleCI configuration
    token, project_slug = get_circleci_config()
    
    if not token or not project_slug:
        print("\n⚙️  First time setup - CircleCI configuration needed.")
        token, project_slug = create_config_file()
    
    # Step 4: Upload and trigger pipeline
    print(f"\n🚀 Starting automated upload and testing...")
    pipeline_id = upload_files_to_circleci(code_file, test_file, token, project_slug)
    
    if pipeline_id:
        print(f"\n🎉 SUCCESS! Your selected files have been uploaded and testing has started.")
        print(f"📊 Check the CircleCI dashboard for test results:")
        print(f"🔗 https://app.circleci.com/pipelines/{project_slug}/{pipeline_id}")
        print(f"\n📋 Expected test results will show:")
        print(f"   - Number of test cases")
        print(f"   - Number of tests passed")
        print(f"   - Number of tests failed")
    else:
        print(f"\n❌ Upload failed. Please check your configuration and try again.")

if __name__ == "__main__":
    main()