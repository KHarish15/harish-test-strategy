# CircleCI Integration Setup Guide

This guide explains how to set up CircleCI integration with the Test Support Tool to provide proof of CI/CD pipeline execution.

## Overview

When you click "Generate Strategy" in the Test Support Tool, it now:
1. ✅ Triggers a real CircleCI pipeline
2. ✅ Shows live pipeline status and logs
3. ✅ Displays build information and results
4. ✅ Provides direct links to CircleCI dashboard

## Setup Steps

### 1. CircleCI API Token

1. Go to [CircleCI User Settings](https://app.circleci.com/settings/user/tokens)
2. Click "Create New Token"
3. Give it a name like "Test Support Tool Integration"
4. Copy the token

### 2. Environment Variables

Add these environment variables to your backend deployment:

```bash
# CircleCI Configuration
CIRCLECI_API_TOKEN=your-circleci-api-token-here
CIRCLECI_PROJECT_SLUG=github/your-username/your-repo-name

# Example:
CIRCLECI_API_TOKEN=abc123def456ghi789
CIRCLECI_PROJECT_SLUG=github/johndoe/finalproject-main
```

### 3. CircleCI Configuration

The `.circleci/config.yml` file is already configured to:
- Run comprehensive test suites
- Generate AI-powered test analysis
- Post results to Confluence
- Provide detailed build artifacts

### 4. Verification

To verify the integration is working:

1. **Click "Generate Strategy"** in the Test Support Tool
2. **Watch the CircleCI Status** section appear with:
   - Pipeline ID and Build Number
   - Real-time status updates
   - Live logs from CircleCI
   - Direct link to CircleCI dashboard

3. **Check CircleCI Dashboard**:
   - Go to your CircleCI project
   - You should see new builds triggered
   - Each build will have detailed logs and artifacts

## What Happens When You Click "Generate Strategy"

### Backend Process:
1. **API Call**: Frontend calls `/test-support` endpoint
2. **CircleCI Trigger**: Backend triggers CircleCI pipeline with parameters:
   ```json
   {
     "test_type": "strategy_generation",
     "code_page": "Your Code Page Title",
     "space_key": "YOUR_SPACE",
     "code_length": 1234,
     "request_timestamp": "2024-01-15T10:30:00Z"
   }
   ```
3. **AI Generation**: Simultaneously generates test strategy using Gemini AI
4. **Response**: Returns both AI content and CircleCI trigger status

### CircleCI Pipeline:
1. **Test Execution**: Runs comprehensive test suite
2. **AI Analysis**: Sends test results to AI for analysis
3. **Confluence Post**: Automatically posts results to Confluence
4. **Artifacts**: Stores test reports and coverage data

### Frontend Display:
1. **Real-time Status**: Shows pipeline status with live updates
2. **Build Information**: Displays build number, pipeline ID, creation time
3. **Live Logs**: Shows real-time logs from CircleCI
4. **Direct Links**: Provides button to view in CircleCI dashboard

## Troubleshooting

### Common Issues:

1. **"CircleCI trigger failed"**
   - Check your `CIRCLECI_API_TOKEN` is correct
   - Verify `CIRCLECI_PROJECT_SLUG` matches your repository
   - Ensure the token has proper permissions

2. **"Pipeline not found"**
   - Check if your repository is connected to CircleCI
   - Verify the project slug format: `github/username/repo-name`

3. **"Status polling failed"**
   - Check network connectivity to CircleCI API
   - Verify API token permissions

### Debug Information:

The backend logs will show:
```
🚀 Triggering CircleCI pipeline for branch: main
📋 Parameters: {'test_type': 'strategy_generation', ...}
✅ CircleCI pipeline triggered successfully! Pipeline ID: abc123-def456
📊 CircleCI Pipeline Triggered:
   Pipeline ID: abc123-def456
   Branch: main
   Parameters: {...}
   Timestamp: 2024-01-15T10:30:00Z
```

## Benefits for Your Mentor

This integration provides concrete proof that:

1. **Real CI/CD**: Every "Generate Strategy" click triggers actual CircleCI builds
2. **Automated Testing**: CircleCI runs comprehensive test suites automatically
3. **AI Integration**: Test results are analyzed by AI and posted to Confluence
4. **Transparency**: Live status updates and direct links to CircleCI dashboard
5. **Audit Trail**: Complete history of all test strategy generations with build IDs

## Next Steps

1. Set up the environment variables in your deployment
2. Test the integration by clicking "Generate Strategy"
3. Share the CircleCI dashboard links with your mentor
4. Show the live status updates and build information

This provides undeniable proof that your system is using CircleCI for automated testing and CI/CD processes! 