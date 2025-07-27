# CircleCI Setup Guide - Fix "Invalid token provided" Error

## Current Issue
You're seeing this error: `❌ CircleCI trigger failed: CircleCI API returned 401: Invalid token provided.`

This means the CircleCI integration is not properly configured. Let's fix this step by step.

## Step 1: Get Your CircleCI API Token

1. **Go to CircleCI User Settings**:
   - Visit: https://app.circleci.com/settings/user/tokens
   - Sign in to your CircleCI account

2. **Create New Token**:
   - Click "Create New Token"
   - Name: `Test Support Tool Integration`
   - Copy the token immediately (you won't see it again!)

## Step 2: Find Your Project Slug

Your project slug format is: `github/username/repository-name`

**To find it:**
1. Go to your CircleCI dashboard: https://app.circleci.com/pipelines
2. Find your project in the list
3. The URL will show: `https://app.circleci.com/pipelines/github/username/repo-name`
4. Your project slug is: `github/username/repo-name`

## Step 3: Set Environment Variables

### Option A: Render.com (Recommended)
1. Go to your Render dashboard
2. Select your backend service
3. Go to "Environment" tab
4. Add these variables:

```bash
CIRCLECI_API_TOKEN=your-actual-circleci-token-here
CIRCLECI_PROJECT_SLUG=github/your-username/your-repo-name
```

### Option B: Local Development
Create a `.env` file in your backend directory:

```bash
CIRCLECI_API_TOKEN=your-actual-circleci-token-here
CIRCLECI_PROJECT_SLUG=github/your-username/your-repo-name
```

## Step 4: Verify Your Repository is Connected to CircleCI

1. **Check if your repo is connected**:
   - Go to: https://app.circleci.com/pipelines
   - Look for your repository in the list
   - If not there, you need to connect it

2. **Connect your repository**:
   - Go to: https://app.circleci.com/projects
   - Click "Set Up Project"
   - Select your repository
   - Choose "Use Existing Config" (since we already have `.circleci/config.yml`)

## Step 5: Test the Integration

1. **Redeploy your backend** (if using Render)
2. **Click "Generate Strategy"** in the Test Support Tool
3. **Check the logs** - you should see:
   ```
   ✅ CircleCI pipeline triggered successfully!
   📋 Pipeline ID: [some-id]
   🔢 Build Number: [number]
   ```

## Troubleshooting

### Error: "Invalid token provided"
- ✅ Check your `CIRCLECI_API_TOKEN` is correct
- ✅ Make sure there are no extra spaces
- ✅ Verify the token hasn't expired

### Error: "CircleCI project not found"
- ✅ Check your `CIRCLECI_PROJECT_SLUG` format
- ✅ Verify your repository is connected to CircleCI
- ✅ Make sure the repository exists and is accessible

### Error: "API token doesn't have permission"
- ✅ Create a new token with proper permissions
- ✅ Make sure you're using a user token, not a project token

## Example Configuration

Here's what your environment variables should look like:

```bash
# Replace with your actual values
CIRCLECI_API_TOKEN=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
CIRCLECI_PROJECT_SLUG=github/johndoe/finalproject-main
```

## What You'll See When It Works

After successful setup, when you click "Generate Strategy":

1. **Frontend**: CircleCI Status section appears with live updates
2. **CircleCI Dashboard**: New build appears and runs in real-time
3. **Confluence**: Live status page and final results posted automatically

## Quick Test Script

Run this to test your configuration:

```bash
python test_circleci_integration.py
```

This will:
- Test the CircleCI API connection
- Trigger a test pipeline
- Show you the dashboard links
- Verify everything is working

## Need Help?

If you're still having issues:

1. **Check the backend logs** for detailed error messages
2. **Verify your CircleCI account** has access to the repository
3. **Try creating a new API token** with fresh permissions
4. **Make sure your repository** has the `.circleci/config.yml` file

## Success Indicators

When everything is working correctly, you'll see:

```
🚀 Triggering CircleCI pipeline for branch: main
📋 Enhanced Parameters: {...}
🔗 CircleCI Dashboard URL: https://app.circleci.com/pipelines/github/your-username/your-repo
✅ CircleCI pipeline triggered successfully!
📋 Pipeline ID: abc123-def456-ghi789
🔢 Build Number: 42
🔗 Live Dashboard: https://app.circleci.com/pipelines/github/your-username/your-repo/42
📊 Build URL: https://app.circleci.com/pipelines/abc123-def456-ghi789
📄 Immediate notification posted to Confluence
```

This setup will provide undeniable proof to your mentor that CircleCI is being used for automated testing! 