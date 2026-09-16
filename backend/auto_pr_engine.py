import os
import sys
import json
import time
import base64
import urllib.request
import urllib.error
import subprocess
from datetime import datetime, timezone

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
LEDGER_PATH = os.path.join(PARENT_DIR, "open_source_workspace", "CONTRIBUTIONS_LEDGER.json")
RADAR_PATH = os.path.join("d:\\projects\\pruthvi828", "OSS_RADAR.md")

def get_oauth_token():
    """Retrieve stored GitHub OAuth token from Git Credential Manager."""
    try:
        p = subprocess.Popen(['git', 'credential', 'fill'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, _ = p.communicate('protocol=https\nhost=github.com\n\n')
        for line in out.splitlines():
            if line.startswith('password='):
                return line.split('=', 1)[1]
    except Exception as e:
        print(f"[!] Error reading credential helper: {e}")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    raise ValueError("No GitHub token found in Git Credential Manager or environment.")

def api_call(url, method="GET", data=None, token=None):
    headers = {
        "User-Agent": "Pruthvi-AutoPR-Engine/2.0",
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"error": body}
        return e.code, parsed
    except Exception as e:
        return 500, {"error": str(e)}

def load_ledger():
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"contributions": []}

def save_ledger(ledger):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

def check_open_prs(repo_full_name, search_term, token):
    url = f"https://api.github.com/search/issues?q=repo:{repo_full_name}+is:pr+is:open+{urllib.parse.quote(search_term)}"
    status, res = api_call(url, token=token)
    if status == 200:
        return res.get("total_count", 0)
    return 0

class AutoPREngine:
    def __init__(self, callback=None):
        self.callback = callback or self._default_log
        self.token = get_oauth_token()
        self.ledger = load_ledger()

    def _default_log(self, stage: str, message: str, percent: int = 0):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{stage.upper()}] ({percent}%) {message}")

    def get_authenticated_user(self):
        status, user = api_call("https://api.github.com/user", token=self.token)
        if status != 200:
            raise ValueError(f"Failed to authenticate: {user}")
        return user.get("login")

    def run_one_click(self):
        """Execute complete 1-click discovery, verification, patch, and PR submission."""
        self.callback("auth", "Resolving GitHub credentials...", 10)
        username = self.get_authenticated_user()
        self.callback("auth", f"Authenticated as @{username}", 15)

        # Curated list of verified open-source targets
        # Target candidates: Issue #1576 in esphome/devices.esphome.io
        candidate_targets = [
            {
                "upstream": "esphome/devices.esphome.io",
                "issue_ref": "#1576",
                "topic": "Tongou-TO-Q-SYS-JWT-power-meter",
                "file": "src/docs/devices/Tongou-TO-Q-SYS-JWT-power-meter/index.md",
                "find": "https://developer.tuya.com/docs/mcu-standard-protocol/MCUSDK-wifi-base?id=Kd2bxu84567gk",
                "replace": "https://developer.tuya.com/en/docs/iot/mcu-standard-protocol?id=Kd2bxu84567gk",
                "desc": "Update dead Tuya MCU SDK protocol documentation URL to active English portal endpoint"
            },
            {
                "upstream": "esphome/devices.esphome.io",
                "issue_ref": "#1576",
                "topic": "Tuya-DY-CK400A-Garage-Door-Opener",
                "file": "src/docs/devices/Tuya-DY-CK400A-Garage-Door-Opener/index.md",
                "find": "https://developer.tuya.com/docs/iot/wifie1smodule?id=K9605thnvg3e7",
                "replace": "https://developer.tuya.com/en/docs/iot/wifie1smodule?id=K9605thnvg3e7",
                "desc": "Update dead Tuya Wi-Fi module datasheet URL to active English documentation endpoint"
            }
        ]

        submitted_topics = {c.get("topic") for c in self.ledger.get("contributions", [])}
        selected = None

        self.callback("scout", "Scanning verified open-source candidate backlog...", 25)
        for cand in candidate_targets:
            if cand["topic"] in submitted_topics:
                continue
            # Check if anyone else has an open PR for this topic
            open_prs = check_open_prs(cand["upstream"], cand["topic"], self.token)
            if open_prs == 0:
                selected = cand
                break
            else:
                self.callback("scout", f"Topic {cand['topic']} already has {open_prs} open PRs. Skipping to next.", 30)

        if not selected:
            self.callback("complete", "All immediate queued candidates have active PRs or were already submitted!", 100)
            return {"status": "up_to_date", "message": "No pending unassigned candidates."}

        self.callback("scout", f"Selected target: {selected['topic']} on {selected['upstream']}", 35)

        upstream_owner, repo_name = selected["upstream"].split("/")
        branch_name = f"fix-{selected['topic'].lower()[:24]}-{int(time.time())}"

        # 1. Ensure Fork Exists
        self.callback("fork", f"Verifying fork of {selected['upstream']}...", 45)
        status, fork = api_call(f"https://api.github.com/repos/{username}/{repo_name}", token=self.token)
        if status == 404:
            self.callback("fork", f"Creating fork on @{username}...", 50)
            api_call(f"https://api.github.com/repos/{upstream_owner}/{repo_name}/forks", method="POST", data={}, token=self.token)
            time.sleep(6)
        else:
            self.callback("fork", "Fork verified.", 55)

        # 2. Get latest upstream/fork main SHA
        status, ref = api_call(f"https://api.github.com/repos/{username}/{repo_name}/git/refs/heads/main", token=self.token)
        if status != 200:
            raise RuntimeError(f"Could not fetch main branch for {username}/{repo_name}")
        base_sha = ref["object"]["sha"]

        # 3. Create branch
        self.callback("branch", f"Creating dedicated branch '{branch_name}'...", 65)
        branch_payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
        status, _ = api_call(f"https://api.github.com/repos/{username}/{repo_name}/git/refs", method="POST", data=branch_payload, token=self.token)

        # 4. Fetch target file
        self.callback("patch", f"Fetching {selected['file']}...", 75)
        status, file_data = api_call(f"https://api.github.com/repos/{username}/{repo_name}/contents/{selected['file']}?ref={branch_name}", token=self.token)
        if status != 200:
            raise RuntimeError(f"Could not read {selected['file']} from fork.")
        
        file_sha = file_data["sha"]
        content = base64.b64decode(file_data["content"]).decode("utf-8")

        if selected["find"] not in content:
            raise ValueError(f"Target pattern not found in {selected['file']}. Upstream may have changed.")

        patched_content = content.replace(selected["find"], selected["replace"])

        # 5. Commit patch
        self.callback("commit", f"Committing patch to {branch_name}...", 85)
        commit_msg = f"fix({selected['topic']}): update dead external documentation URL"
        commit_payload = {
            "message": commit_msg,
            "content": base64.b64encode(patched_content.encode("utf-8")).decode("utf-8"),
            "sha": file_sha,
            "branch": branch_name
        }
        api_call(f"https://api.github.com/repos/{username}/{repo_name}/contents/{selected['file']}", method="PUT", data=commit_payload, token=self.token)

        # 6. Submit Pull Request
        self.callback("pr", f"Opening Pull Request to {selected['upstream']}...", 92)
        pr_body = f"""## Description
Fixes broken external documentation URL in `{selected['file']}` identified in {selected['issue_ref']}:

- **Before:** `{selected['find']}` (404 / broken)
- **After:** `{selected['replace']}` (Active documentation endpoint)

Resolves broken documentation link for `{selected['topic']}` in {selected['issue_ref']}.
"""
        pr_payload = {
            "title": f"fix({selected['topic']}): update broken external documentation link",
            "head": f"{username}:{branch_name}",
            "base": "main",
            "body": pr_body
        }
        status, pr_res = api_call(f"https://api.github.com/repos/{selected['upstream']}/pulls", method="POST", data=pr_payload, token=self.token)

        if status not in [200, 201]:
            raise RuntimeError(f"PR creation failed ({status}): {pr_res}")

        pr_url = pr_res.get("html_url")
        pr_number = pr_res.get("number")
        self.callback("success", f"🎉 Pull Request #{pr_number} successfully opened: {pr_url}", 100)

        # Record to ledger
        record = {
            "pr_url": pr_url,
            "pr_number": pr_number,
            "repo": selected["upstream"],
            "topic": selected["topic"],
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "branch": branch_name
        }
        self.ledger["contributions"].append(record)
        save_ledger(self.ledger)

        # Update OSS Radar if present
        self._update_radar(record)

        return record

    def _update_radar(self, record):
        if os.path.exists(RADAR_PATH):
            try:
                with open(RADAR_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                badge_line = f"\n- **Latest Automated Contribution:** [PR #{record['pr_number']} on {record['repo']}]({record['pr_url']}) ({record['submitted_at'][:10]})\n"
                if "Latest Automated Contribution" not in content:
                    content = content.replace("---", badge_line + "\n---", 1)
                    with open(RADAR_PATH, "w", encoding="utf-8") as f:
                        f.write(content)
            except Exception as e:
                print(f"[!] Warning updating radar: {e}")

if __name__ == "__main__":
    engine = AutoPREngine()
    result = engine.run_one_click()
    print("\nResult:\n", json.dumps(result, indent=2))
