#!/usr/bin/env python3
"""
CircleCI Real-time Visibility Demo

This script demonstrates how to see tests running in real-time on CircleCI
when you click "Generate Strategy" in the Test Support Tool.

Usage:
    python demo_circleci_realtime.py
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BACKEND_URL = "https://backend-az2r.onrender.com"

def demo_realtime_visibility():
    """Demonstrate real-time CircleCI visibility"""
    print("🎯 CircleCI Real-time Visibility Demo")
    print("=" * 60)
    print("This demo shows how to see tests running in real-time on CircleCI")
    print("when you click 'Generate Strategy' in the Test Support Tool.")
    print("")
    
    print("📋 STEP 1: Trigger CircleCI Pipeline")
    print("-" * 40)
    
    # Test data
    test_request = {
        "space_key": "TEST",
        "code_page_title": "Demo Code Page",
        "test_input_page_title": "Demo Test Input"
    }
    
    try:
        print("🚀 Calling Test Support Tool with CircleCI integration...")
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
                print("✅ CircleCI pipeline triggered successfully!")
                print(f"📋 Pipeline ID: {circleci_trigger.get('pipeline_id')}")
                print(f"🔢 Build Number: {circleci_trigger.get('number')}")
                print(f"🔗 Dashboard URL: {circleci_trigger.get('dashboard_url')}")
                
                print("\n📊 STEP 2: Real-time Visibility Instructions")
                print("-" * 40)
                print("Now you can see the test running in real-time:")
                print("")
                print("1. 🔗 OPEN CIRCLECI DASHBOARD:")
                print(f"   {circleci_trigger.get('dashboard_url')}")
                print("")
                print("2. 🔄 REFRESH THE PAGE:")
                print("   - You'll see the build appear in the list")
                print("   - Click on the build to see live execution")
                print("")
                print("3. 📊 WATCH LIVE EXECUTION:")
                print("   - See test steps running in real-time")
                print("   - Watch logs update as tests execute")
                print("   - Monitor test results as they complete")
                print("")
                print("4. 📄 CONFLUENCE UPDATES:")
                print("   - Check your Confluence space for live status page")
                print("   - Final results will be posted automatically")
                print("")
                
                print("🎯 WHAT YOU'LL SEE ON CIRCLECI:")
                print("-" * 40)
                print("✅ Pipeline triggered by Test Support Tool")
                print("✅ Display Pipeline Information step")
                print("✅ Install dependencies step")
                print("✅ Create comprehensive test suite step")
                print("✅ Execute comprehensive test suite step")
                print("✅ Store artifacts step")
                print("✅ AI-enhanced testing job")
                print("")
                
                print("📈 REAL-TIME FEATURES:")
                print("-" * 40)
                print("🔄 Live log streaming")
                print("📊 Step-by-step progress")
                print("⏱️ Execution time tracking")
                print("📋 Test result summaries")
                print("🎯 Coverage reports")
                print("🤖 AI analysis integration")
                print("")
                
                return circleci_trigger
            else:
                print("⚠️ CircleCI integration not working or not configured")
                if circleci_trigger:
                    print(f"Error: {circleci_trigger.get('error')}")
                return None
                
        else:
            print(f"❌ Test support request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error in demo: {str(e)}")
        return None

def show_manual_steps():
    """Show manual steps for real-time visibility"""
    print("\n📋 MANUAL STEPS FOR REAL-TIME VISIBILITY")
    print("=" * 60)
    print("")
    print("1. 🚀 CLICK 'GENERATE STRATEGY' in Test Support Tool")
    print("   - This triggers a real CircleCI pipeline")
    print("   - You'll see CircleCI Status section appear")
    print("")
    print("2. 🔗 OPEN CIRCLECI DASHBOARD")
    print("   - Go to: https://app.circleci.com/pipelines")
    print("   - Find your project in the list")
    print("   - Or use the direct link from the UI")
    print("")
    print("3. 🔄 REFRESH AND WATCH")
    print("   - Refresh the CircleCI dashboard")
    print("   - You'll see a new build appear")
    print("   - Click on the build to see live execution")
    print("")
    print("4. 📊 REAL-TIME FEATURES YOU'LL SEE:")
    print("   - Live log streaming as tests run")
    print("   - Step-by-step progress indicators")
    print("   - Test results as they complete")
    print("   - Coverage reports being generated")
    print("   - AI analysis integration")
    print("")
    print("5. 📄 CONFLUENCE INTEGRATION")
    print("   - Check your Confluence space")
    print("   - Look for 'CircleCI Build #X - Live Status' page")
    print("   - Final results will be posted automatically")
    print("")

def show_troubleshooting():
    """Show troubleshooting steps"""
    print("\n🔧 TROUBLESHOOTING")
    print("=" * 60)
    print("")
    print("If you don't see the build on CircleCI:")
    print("")
    print("1. ✅ Check Environment Variables:")
    print("   - CIRCLECI_API_TOKEN is set correctly")
    print("   - CIRCLECI_PROJECT_SLUG matches your repo")
    print("")
    print("2. 🔗 Verify Repository Connection:")
    print("   - Ensure your repo is connected to CircleCI")
    print("   - Check CircleCI project settings")
    print("")
    print("3. 🔄 Refresh Dashboard:")
    print("   - CircleCI dashboard may need refresh")
    print("   - Check 'All Branches' view")
    print("")
    print("4. 📊 Check Build History:")
    print("   - Look in recent builds section")
    print("   - Filter by branch if needed")
    print("")

def main():
    """Main demonstration function"""
    print("🎯 CircleCI Real-time Visibility Demonstration")
    print("=" * 60)
    print(f"📅 Demo started at: {datetime.now().isoformat()}")
    print("")
    
    # Run the demo
    circleci_result = demo_realtime_visibility()
    
    # Show manual steps
    show_manual_steps()
    
    # Show troubleshooting
    show_troubleshooting()
    
    print("\n" + "=" * 60)
    print("🎉 Demo completed!")
    print("")
    print("💡 KEY TAKEAWAYS:")
    print("   - Every 'Generate Strategy' click triggers real CircleCI builds")
    print("   - You can see tests running in real-time on CircleCI dashboard")
    print("   - Results are automatically posted to Confluence")
    print("   - Complete audit trail with build IDs and timestamps")
    print("")
    print("🔗 NEXT STEPS:")
    print("   1. Set up CircleCI environment variables")
    print("   2. Test the integration by clicking 'Generate Strategy'")
    print("   3. Open CircleCI dashboard to see live execution")
    print("   4. Share the build URLs with your mentor")

if __name__ == "__main__":
    main() 