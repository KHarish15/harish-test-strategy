#!/usr/bin/env python3
"""
Test script for CircleCI integration
This script simulates the CircleCI pipeline and posts results to Confluence
"""

import os
import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://backend-i2dk.onrender.com"
CONFLUENCE_SPACE = "TEST"  # Default space for testing

def test_circleci_integration():
    """Test the CircleCI integration by simulating test results"""
    
    print("🧪 Testing CircleCI Integration...")
    
    # Simulate test results
    test_results = {
        "status": "completed",
        "passed": 5,
        "failed": 2,
        "logs": """
Running tests...
test_basic_functionality PASSED
test_user_authentication PASSED
test_data_validation PASSED
test_api_integration FAILED - Connection timeout
test_database_operations PASSED
test_error_handling PASSED
test_security_validation FAILED - Invalid token format
        """,
        "timestamp": datetime.now().isoformat(),
        "pipeline_info": {
            "branch": "main",
            "commit": "abc123def456",
            "build_number": "42"
        }
    }
    
    try:
        # Step 1: Send test results to AI analysis
        print("📊 Sending test results to AI analysis...")
        analysis_response = requests.post(
            f"{BACKEND_URL}/analyze-logs",
            json={"test_results": test_results},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            print("✅ AI analysis completed successfully")
            print(f"📝 Analysis length: {len(analysis_data.get('analysis', ''))} characters")
        else:
            print(f"❌ AI analysis failed: {analysis_response.status_code}")
            print(f"Error: {analysis_response.text}")
            return False
        
        # Step 2: Post results to Confluence
        print("📄 Posting results to Confluence...")
        
        confluence_content = f"""
## 🧪 Test Results Summary

### Build Information
- **Build Number**: #{test_results['pipeline_info']['build_number']}
- **Branch**: {test_results['pipeline_info']['branch']}
- **Commit**: {test_results['pipeline_info']['commit'][:8]}
- **Timestamp**: {test_results['timestamp']}

### Test Results
- **Status**: {test_results['status'].title()}
- **Passed**: {test_results['passed']} tests
- **Failed**: {test_results['failed']} tests
- **Success Rate**: {round(test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100, 1)}%

### AI Analysis
{analysis_data.get('analysis', 'No analysis available')}

### Test Logs
```
{test_results['logs']}
```

---
*Generated automatically by CircleCI integration on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        confluence_request = {
            "space_key": CONFLUENCE_SPACE,
            "page_title": f"Test Results - CircleCI Build #{test_results['pipeline_info']['build_number']}",
            "content": confluence_content,
            "mode": "append"
        }
        
        confluence_response = requests.post(
            f"{BACKEND_URL}/save-to-confluence",
            json=confluence_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if confluence_response.status_code == 200:
            print("✅ Successfully posted to Confluence")
            confluence_data = confluence_response.json()
            print(f"📋 Message: {confluence_data.get('message', 'No message')}")
        else:
            print(f"❌ Failed to post to Confluence: {confluence_response.status_code}")
            print(f"Error: {confluence_response.text}")
            return False
        
        print("\n🎉 CircleCI Integration Test Completed Successfully!")
        print("📊 Test Results:")
        print(f"   - Tests Passed: {test_results['passed']}")
        print(f"   - Tests Failed: {test_results['failed']}")
        print(f"   - AI Analysis: ✅ Completed")
        print(f"   - Confluence Post: ✅ Completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_circleci_integration()
    exit(0 if success else 1) 