#!/usr/bin/env python3
"""
Trigger CircleCI with file content and filenames as parameters
"""

import requests
import base64
import os
import json

def trigger_circleci_with_files(code_content, test_content, code_filename, test_filename, circleci_token, project_slug):
    """
    Trigger CircleCI pipeline with file content and filenames as parameters
    """
    try:
        print("🚀 Triggering CircleCI with file content...")
        
        # Encode file content as base64
        code_content_b64 = base64.b64encode(code_content.encode()).decode()
        test_content_b64 = base64.b64encode(test_content.encode()).decode()
        
        # Trigger CircleCI pipeline with parameters
        trigger_url = f"https://circleci.com/api/v2/project/{project_slug}/pipeline"
        
        headers = {
            'Circle-Token': circleci_token,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'parameters': {
                'code_content': code_content_b64,
                'test_content': test_content_b64,
                'code_filename': code_filename,
                'test_filename': test_filename
            }
        }
        
        response = requests.post(trigger_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            pipeline_data = response.json()
            pipeline_id = pipeline_data['id']
            print(f"✅ Pipeline triggered successfully!")
            print(f"🔗 View pipeline: https://app.circleci.com/pipelines/{project_slug}/{pipeline_id}")
            return {
                'success': True,
                'pipeline_id': pipeline_id,
                'dashboard_url': f"https://app.circleci.com/pipelines/{project_slug}/{pipeline_id}"
            }
        else:
            print(f"❌ Failed to trigger pipeline: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                'success': False,
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except Exception as e:
        print(f"❌ Error triggering CircleCI: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """
    Example usage of the CircleCI trigger function
    """
    print("🎯 CircleCI File Upload Trigger")
    print("=" * 40)
    
    # Example file content
    code_content = """def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def multiply(a, b):
    return a * b

def is_even(n):
    return n % 2 == 0

def get_max(numbers):
    if not numbers:
        raise ValueError("Empty list provided")
    return max(numbers)"""

    test_content = """import pytest
from main import add, subtract, divide, multiply, is_even, get_max

def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(10, 5) == 5
    assert subtract(5, 10) == -5

def test_divide():
    assert divide(10, 2) == 5
    with pytest.raises(ValueError):
        divide(5, 0)

def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(0, 100) == 0

def test_is_even():
    assert is_even(4) is True
    assert is_even(5) is False

def test_get_max():
    assert get_max([1, 5, 3]) == 5
    with pytest.raises(ValueError):
        get_max([])"""

    # Get CircleCI configuration
    token = os.getenv('CIRCLECI_TOKEN')
    project_slug = os.getenv('CIRCLECI_PROJECT_SLUG')
    
    if not token or not project_slug:
        print("❌ Please set CIRCLECI_TOKEN and CIRCLECI_PROJECT_SLUG environment variables")
        return
    
    # Trigger CircleCI
    result = trigger_circleci_with_files(
        code_content=code_content,
        test_content=test_content,
        code_filename="main.py",
        test_filename="test_main.py",
        circleci_token=token,
        project_slug=project_slug
    )
    
    if result['success']:
        print(f"\n🎉 SUCCESS! CircleCI pipeline triggered with file content.")
        print(f"📊 Check results at: {result['dashboard_url']}")
    else:
        print(f"\n❌ FAILED: {result['error']}")

if __name__ == "__main__":
    main()