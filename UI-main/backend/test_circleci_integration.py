#!/usr/bin/env python3
"""
CircleCI Integration Test Script

This script demonstrates the CircleCI integration with the Test Support Tool.
It shows how to trigger CircleCI pipelines and monitor their status.

Usage:
    python test_circleci_integration.py
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://backend-i2dk.onrender.com"
CIRCLECI_API_TOKEN = os.getenv('CIRCLECI_API_TOKEN', 'your-circleci-token')
CIRCLECI_PROJECT_SLUG = os.getenv('CIRCLECI_PROJECT_SLUG', 'github/your-username/your-repo')

def test_circleci_trigger():
    """Test triggering a CircleCI pipeline"""
    print("🚀 Testing CircleCI Pipeline Trigger")
    print("=" * 50)
    
    # Test data
    test_data = {
        "branch": "main",
        "parameters": {
            "test_type": "integration_test",
            "triggered_by": "test_script",
            "timestamp": datetime.now().isoformat(),
            "description": "Testing CircleCI integration from script"
        }
    }
    
    try:
        # Trigger CircleCI pipeline
        response = requests.post(
            f"{BACKEND_URL}/trigger-circleci",
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ CircleCI pipeline triggered successfully!")
                print(f"📋 Pipeline ID: {result.get('pipeline_id')}")
                print(f"🔢 Build Number: {result.get('number')}")
                print(f"📅 Created: {result.get('created_at')}")
                return result.get('pipeline_id')
            else:
                print(f"❌ Failed to trigger pipeline: {result.get('error')}")
                return None
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_pipeline_status(pipeline_id):
    """Test getting pipeline status"""
    if not pipeline_id:
        return
    
    print(f"\n📊 Testing Pipeline Status for ID: {pipeline_id}")
    print("=" * 50)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/circleci-status/{pipeline_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            status = response.json()
            if status.get('pipeline', {}).get('success'):
                pipeline = status['pipeline']['pipeline']
                print(f"✅ Pipeline Status: {pipeline.get('state')}")
                print(f"📋 Build Number: {pipeline.get('number')}")
                print(f"🌿 Branch: {pipeline.get('vcs', {}).get('branch')}")
                print(f"📅 Created: {pipeline.get('created_at')}")
                
                # Show workflows
                if status.get('workflows', {}).get('success'):
                    workflows = status['workflows']['workflows']
                    print(f"🔄 Workflows: {len(workflows)}")
                    for workflow in workflows:
                        print(f"   - {workflow.get('name')}: {workflow.get('status')}")
            else:
                print(f"❌ Failed to get pipeline status: {status.get('pipeline', {}).get('error')}")
        else:
            print(f"❌ Status API call failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting status: {str(e)}")

def test_test_support_integration():
    """Test the test-support endpoint with CircleCI integration"""
    print(f"\n🧪 Testing Test Support Tool with CircleCI Integration")
    print("=" * 50)
    
    # Test data
    test_request = {
        "space_key": "TEST",
        "code_page_title": "Test Code Page",
        "test_input_page_title": "Test Input Page"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/test-support",
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Test support request successful!")
            
            # Check CircleCI integration
            circleci_trigger = result.get('circleci_trigger')
            if circleci_trigger and circleci_trigger.get('success'):
                print("✅ CircleCI integration working!")
                print(f"📋 Pipeline ID: {circleci_trigger.get('pipeline_id')}")
                print(f"🔢 Build Number: {circleci_trigger.get('number')}")
            else:
                print("⚠️ CircleCI integration not working or not configured")
                if circleci_trigger:
                    print(f"Error: {circleci_trigger.get('error')}")
            
            # Check AI content
            if result.get('strategy'):
                print(f"✅ AI Strategy generated ({len(result['strategy'])} chars)")
            if result.get('cross_platform'):
                print(f"✅ Cross-platform analysis generated ({len(result['cross_platform'])} chars)")
            if result.get('sensitivity'):
                print(f"✅ Sensitivity analysis generated ({len(result['sensitivity'])} chars)")
                
        else:
            print(f"❌ Test support request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in test support: {str(e)}")

def main():
    """Main test function"""
    print("🎯 CircleCI Integration Test Suite")
    print("=" * 60)
    print(f"📅 Test started at: {datetime.now().isoformat()}")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"📋 CircleCI Project: {CIRCLECI_PROJECT_SLUG}")
    print("")
    
    # Test 1: Direct CircleCI trigger
    pipeline_id = test_circleci_trigger()
    
    # Test 2: Pipeline status
    if pipeline_id:
        time.sleep(2)  # Wait a bit for pipeline to start
        test_pipeline_status(pipeline_id)
    
    # Test 3: Test support integration
    test_test_support_integration()
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")
    print("\n📋 Next Steps:")
    print("1. Check your CircleCI dashboard for triggered builds")
    print("2. Verify the build logs show the test execution")
    print("3. Check Confluence for posted results")
    print("4. Share the CircleCI build URLs with your mentor")

if __name__ == "__main__":
    main() 