#!/usr/bin/env python3
"""Package main and same-repository PR previews, then reconcile deployed preview comments."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import urllib.request

from build_site import build

ROOT = Path(__file__).resolve().parents[1]
MARKER = "<!-- pages-pr-preview -->"
REMOVED = MARKER + "\nPreview removed after this pull request closed."
INPUTS = {
    "site/index.html", "site/styles.css", "site/app.js", "site/favicon.svg",
    "skills/README.md", "skills/theme-factory/assets/theme-guide.html",
}


def api(endpoint, method="GET", data=None):
    request = urllib.request.Request(
        "https://api.github.com" + endpoint,
        data=json.dumps(data).encode() if data is not None else None,
        method=method,
        headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                 "X-GitHub-Api-Version": "2022-11-28"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def paginate(request, endpoint):
    items = []
    page = 1
    while True:
        batch = request(f"{endpoint}{'&' if '?' in endpoint else '?'}per_page=100&page={page}")
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def collect_sources(request, repository):
    main = request(f"/repos/{repository}/git/ref/heads/main")["object"]["sha"]
    pulls = paginate(request, f"/repos/{repository}/pulls?state=open&base=main")
    previews = [{"number": pull["number"], "sha": pull["head"]["sha"]} for pull in pulls
                if pull["head"]["repo"] and pull["head"]["repo"]["full_name"] == repository]
    return {"main": main, "previews": previews}


def git(repository, *args):
    return subprocess.check_output(["git", *args], cwd=repository)


def copy_snapshot(repository, sha, output):
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("Invalid source commit")
    entries = git(repository, "ls-tree", "-rz", "--full-tree", sha).split(b"\0")
    for entry in filter(None, entries):
        metadata, filename = entry.decode().split("\t", 1)
        if filename not in INPUTS and not re.fullmatch(r"skills/[a-z0-9-]+/SKILL\.md", filename):
            continue
        mode, kind, blob = metadata.split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"Snapshot input must be a regular file: {filename}")
        destination = output / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(git(repository, "cat-file", "blob", blob))


def package(repository, output, sources):
    # Build a fresh complete deployment before replacing the previous output.
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as directory:
        staging = Path(directory)
        site = staging / "site-output"
        snapshots = [("main", sources["main"], site)]
        for preview in sources["previews"]:
            number = preview["number"]
            if type(number) is not int or number <= 0:
                raise ValueError("Invalid pull request number")
            snapshots.append((str(number), preview["sha"], site / "pr-preview" / str(number)))
        for name, sha, destination in snapshots:
            source = staging / "inputs" / name
            copy_snapshot(repository, sha, source)
            build(destination, source, source_ref="main" if name == "main" else sha)
        if output.exists():
            shutil.rmtree(output)
        shutil.move(site, output)


def bot_preview(comment):
    return comment["user"]["login"] == "github-actions[bot]" and MARKER in comment["body"]


def comment_previews(request, repository, page_url, previews):
    for preview in previews:
        number, sha = preview["number"], preview["sha"]
        url = f"{page_url.rstrip('/')}/pr-preview/{number}/"
        body = (f"{MARKER}\n[View the deployed preview]({url})\n\n"
                f"Source commit: [{sha}](https://github.com/{repository}/commit/{sha}).\n\n"
                "This preview updates on new commits and is removed when the pull request closes.")
        endpoint = f"/repos/{repository}/issues/{number}/comments"
        existing = next((item for item in paginate(request, endpoint) if bot_preview(item)), None)
        if existing:
            if existing["body"] != body:
                request(f"/repos/{repository}/issues/comments/{existing['id']}", "PATCH", {"body": body})
        else:
            request(endpoint, "POST", {"body": body})
    # Inspect all previous preview comments: queued runs can replace a PR's close event.
    for comment in paginate(request, f"/repos/{repository}/issues/comments"):
        if not bot_preview(comment) or comment["body"] == REMOVED:
            continue
        number = int(comment["issue_url"].rsplit("/", 1)[1])
        if any(preview["number"] == number for preview in previews):
            continue
        pull = request(f"/repos/{repository}/pulls/{number}")
        if pull["state"] == "closed":
            request(f"/repos/{repository}/issues/comments/{comment['id']}", "PATCH", {"body": REMOVED})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build", "comment"])
    args = parser.parse_args()
    repository = os.environ["GITHUB_REPOSITORY"]
    if args.command == "build":
        sources = collect_sources(api, repository)
        commits = [sources["main"], *(preview["sha"] for preview in sources["previews"])]
        if not all(re.fullmatch(r"[a-f0-9]{40}", sha) for sha in commits):
            raise ValueError("Invalid source commit")
        git(ROOT, "fetch", "--no-tags", "origin", *sorted(set(commits)))
        package(ROOT, ROOT / "dist", sources)
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write("previews=" + json.dumps(sources["previews"]) + "\n")
    else:
        comment_previews(api, repository, os.environ["PAGE_URL"], json.loads(os.environ["DEPLOYED_PREVIEWS"]))


if __name__ == "__main__":
    main()
