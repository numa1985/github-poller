import os
import requests
import json

GITHUB_API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com/repos/{owner}/{repo}/commits")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
LAST_COMMIT_FILE = os.environ.get("LAST_COMMIT_FILE", "/data/last_commit.txt")
ARGO_EVENT_SOURCE_URL = os.environ.get("ARGO_EVENT_SOURCE_URL", "http://argo-event-source-service.default.svc.cluster.local:12000/webhook")

def get_latest_commit():
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(GITHUB_API_URL, headers=headers)
    response.raise_for_status()
    commits = response.json()
    return commits[0]['sha']

def read_last_commit():
    if os.path.exists(LAST_COMMIT_FILE):
        with open(LAST_COMMIT_FILE, 'r') as f:
            return f.read().strip()
    return None

def write_last_commit(commit_sha):
    with open(LAST_COMMIT_FILE, 'w') as f:
        f.write(commit_sha)

def send_event(commit_sha):
    event = {
        "event": "push",
        "commit_sha": commit_sha
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(ARGO_EVENT_SOURCE_URL, data=json.dumps(event), headers=headers)
    response.raise_for_status()

def main():
    try:
        latest_commit_sha = get_latest_commit()
        last_commit_sha = read_last_commit()

        if latest_commit_sha != last_commit_sha:
            send_event(latest_commit_sha)
            write_last_commit(latest_commit_sha)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
