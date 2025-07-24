import os
import requests

def create_jira_issue(summary, description, issue_type="Task"):
    """
    Create a Jira issue using REST API.
    Requires the following environment variables:
      - JIRA_BASE_URL (e.g., https://your-domain.atlassian.net)
      - JIRA_EMAIL
      - JIRA_API_TOKEN
      - JIRA_PROJECT_KEY
    """
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")

    if not all([base_url, email, api_token, project_key]):
        raise ValueError("Missing one or more Jira environment variables.")

    url = f"{base_url}/rest/api/3/issue"
    auth = (email, api_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type}
        }
    }
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    if response.status_code not in (200, 201):
        raise Exception(f"Failed to create Jira issue: {response.status_code} {response.text}")
    return response.json()  # Contains 'key', 'id', etc. 