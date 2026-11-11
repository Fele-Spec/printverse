"""Create the PrintVerse repository under the authenticated GitHub account."""
from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request


def credential() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True, capture_output=True, check=False,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("No saved GitHub credential")


def api(token: str, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        "https://api.github.com" + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PrintVerse",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main() -> None:
    token = credential()
    status, user = api(token, "GET", "/user")
    if status != 200:
        raise SystemExit(f"GitHub auth failed: {status}")
    owner = user["login"]
    print("account", owner)
    status, repo = api(token, "GET", f"/repos/{owner}/printverse")
    if status == 404:
        status, repo = api(token, "POST", "/user/repos", {
            "name": "printverse",
            "description": "PrintVerse: colour AI 3D, Voron digital twin, virtual printing, filament accounting, desktop pet and standalone cloud platform.",
            "private": False,
            "has_issues": True,
            "has_projects": False,
            "has_wiki": False,
            "auto_init": False,
        })
        print("create", status)
    else:
        print("existing", status)
    if status not in (200, 201):
        raise SystemExit(f"repo error: {status} {repo}")
    print("repo", repo["full_name"], repo["html_url"], repo["default_branch"])
    print("clone", repo["clone_url"])


if __name__ == "__main__":
    main()
