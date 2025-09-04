import os
import requests
import json

# Base GitHub API URL for the repo (do NOT include /commits or /branches)
GITHUB_API_URL = os.environ.get(
    "GITHUB_API_URL",
    "https://api.github.com/repos/{owner}/{repo}"
)
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
LAST_COMMIT_DIR = os.environ.get("LAST_COMMIT_DIR", "/data")
ARGO_EVENT_SOURCE_URL = os.environ.get(
    "ARGO_EVENT_SOURCE_URL",
    "http://argo-event-source-service.default.svc.cluster.local:12000/commit"
)

# Ensure directory for per-branch commit files exists
os.makedirs(LAST_COMMIT_DIR, exist_ok=True)


def github_request(url):
    """Send a GET request to GitHub API with optional token."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def get_branches():
    """Return list of branch objects from GitHub."""
    branches_url = f"{GITHUB_API_URL}/branches"
    return github_request(branches_url)


def get_latest_commit_sha(branch):
    """Return latest commit SHA from branch object."""
    return branch["commit"]["sha"]


def get_commit_file(branch_name):
    """Return file path to store last commit SHA for a branch."""
    safe_branch = branch_name.replace("/", "_")
    return os.path.join(LAST_COMMIT_DIR, f"{safe_branch}.txt")


def read_last_commit(branch_name):
    """Read last stored commit SHA from file."""
    commit_file = get_commit_file(branch_name)
    if os.path.exists(commit_file):
        with open(commit_file, "r") as f:
            return f.read().strip()
    return None


def write_last_commit(branch_name, commit_sha):
    """Write latest commit SHA to file."""
    commit_file = get_commit_file(branch_name)
    with open(commit_file, "w") as f:
        f.write(commit_sha)


def send_event(branch_name, commit_sha):
    """Send a webhook event to Argo EventSource."""
    event = {
        "event": "commit-detected",  # must match Sensor eventName
        "repo": GITHUB_REPO,
        "branch": branch_name,
        "commit_sha": commit_sha,
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(ARGO_EVENT_SOURCE_URL, data=json.dumps(event), headers=headers)
    response.raise_for_status()
    print(f"📤 Event sent for branch {branch_name} commit {commit_sha}")


def main():
    try:
        branches = get_branches()

        for branch in branches:
            branch_name = branch["name"]
            latest_commit_sha = get_latest_commit_sha(branch)
            last_commit_sha = read_last_commit(branch_name)

            if latest_commit_sha != last_commit_sha:
                print(f"✅ New commit detected on branch {branch_name}: {latest_commit_sha}")
                send_event(branch_name, latest_commit_sha)
                write_last_commit(branch_name, latest_commit_sha)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
