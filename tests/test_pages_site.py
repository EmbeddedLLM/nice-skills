"""Local contracts for snapshot-based GitHub Pages previews; no GitHub writes."""
import contextlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import pages_preview as previews
sys.path.pop(0)


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        self.repository.mkdir()
        self.run_git("init", "-q")
        self.run_git("config", "user.name", "Example")
        self.run_git("config", "user.email", "example@example.invalid")
        for filename in previews.INPUTS:
            target = self.repository / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / filename, target)
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            target = self.repository / skill.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("Snapshot skill marker")
        self.main = self.commit()

    def run_git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repository).decode().strip()

    def commit(self):
        self.run_git("add", ".")
        self.run_git("commit", "-qm", "Synthetic snapshot")
        return self.run_git("rev-parse", "HEAD")

    def package(self, sources):
        with contextlib.redirect_stdout(io.StringIO()):
            previews.package(self.repository, self.root / "dist", sources)
        return self.root / "dist"

    def test_production_and_multiple_previews_then_close(self):
        """Ensures main stays at root, each PR uses its own source, and closing removes stale files."""
        template = self.repository / "site/index.html"
        template.write_text(template.read_text().replace("Great work.", "First preview."))
        (self.repository / "skills/theme-factory/SKILL.md").write_text("# Preview skill document\n\nRead **this** version. {{COUNT}}")
        first = self.commit()
        template.write_text(template.read_text().replace("First preview.", "Second preview."))
        second = self.commit()
        output = self.package({"main": self.main, "previews": [
            {"number": 5, "sha": first}, {"number": 6, "sha": second}]})
        self.assertIn("Great work.", (output / "index.html").read_text())
        self.assertIn("First preview.", (output / "pr-preview/5/index.html").read_text())
        preview_page = (output / "pr-preview/5/index.html").read_text()
        self.assertIn(f"/blob/{first}/skills/", preview_page)
        self.assertIn('Preview skill document</h1>', preview_page)
        self.assertIn('<strong>this</strong> version. {{COUNT}}', preview_page)
        self.assertNotIn('Preview skill document</h1>', (output / "index.html").read_text())
        self.assertIn("Second preview.", (output / "pr-preview/6/index.html").read_text())
        for number in (5, 6):
            page = (output / f"pr-preview/{number}/index.html").read_text()
            self.assertIn('href="./themes.css"', page)
            self.assertTrue((output / f"pr-preview/{number}/themes.css").is_file())
        self.package({"main": second, "previews": [{"number": 6, "sha": second}]})
        self.assertIn("Second preview.", (output / "index.html").read_text())
        self.assertFalse((output / "pr-preview/5").exists())
        self.assertTrue((output / "pr-preview/6/index.html").is_file())
        self.package({"main": second, "previews": []})
        self.assertFalse((output / "pr-preview").exists())

    def test_snapshot_helpers_are_never_executed_or_published(self):
        """Ensures PR Python files and unrelated data cannot run or enter the deployed artifact."""
        sentinel = self.root / "executed"
        for name in ("tools/build_site.py", "skills/theme-factory/scripts/themes.py"):
            path = self.repository / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"from pathlib import Path\nPath({str(sentinel)!r}).touch()\nraise RuntimeError('PR code ran')")
        (self.repository / "private-data.txt").write_text("Synthetic excluded content")
        sha = self.commit()
        output = self.package({"main": self.main, "previews": [{"number": 5, "sha": sha}]})
        self.assertFalse(sentinel.exists())
        self.assertEqual({path.name for path in (output / "pr-preview/5").iterdir()},
                         {"index.html", "styles.css", "app.js", "favicon.svg", "themes.css", ".nojekyll"})

    def test_symlink_and_invalid_build_preserve_previous_output(self):
        """Ensures unsafe or broken preview inputs fail without replacing the previous deployment."""
        output = self.package({"main": self.main, "previews": []})
        original = (output / "index.html").read_bytes()
        template = self.repository / "site/index.html"
        template.unlink()
        template.symlink_to("../../outside.html")
        sha = self.commit()
        with self.assertRaisesRegex(ValueError, "regular file"):
            self.package({"main": self.main, "previews": [{"number": 5, "sha": sha}]})
        self.assertEqual(original, (output / "index.html").read_bytes())
        template.unlink()
        template.write_text("Example")
        (self.repository / "skills/README.md").write_text("No published entries")
        sha = self.commit()
        with self.assertRaisesRegex(ValueError, "every published skill"):
            self.package({"main": self.main, "previews": [{"number": 5, "sha": sha}]})
        self.assertEqual(original, (output / "index.html").read_bytes())

    def test_invalid_commit_and_pr_number_are_rejected(self):
        """Ensures refs and PR identifiers cannot become Git options or output paths."""
        for sha in ("--help", "main", "../../outside"):
            with self.subTest(sha=sha), self.assertRaisesRegex(ValueError, "source commit"):
                previews.copy_snapshot(self.repository, sha, self.root / "input")
        for number in (0, -1, True, "../outside"):
            with self.subTest(number=number), self.assertRaisesRegex(ValueError, "pull request number"):
                self.package({"main": self.main, "previews": [{"number": number, "sha": self.main}]})


class GitHubTests(unittest.TestCase):
    def test_current_sources_exclude_forks_and_paginate(self):
        """Ensures every current same-repository PR is included even after the first API page."""
        def request(endpoint):
            if endpoint.endswith("git/ref/heads/main"):
                return {"object": {"sha": "a" * 40}}
            self.assertIn("state=open&base=main", endpoint)
            if endpoint.endswith("page=1"):
                return [{"number": number, "head": {"sha": "b" * 40,
                         "repo": {"full_name": "example/skills"}}} for number in range(1, 101)]
            return [{"number": 101, "head": {"sha": "c" * 40, "repo": {"full_name": "fork/skills"}}},
                    {"number": 102, "head": {"sha": "d" * 40, "repo": None}},
                    {"number": 103, "head": {"sha": "e" * 40, "repo": {"full_name": "example/skills"}}}]
        sources = previews.collect_sources(request, "example/skills")
        self.assertEqual(sources["main"], "a" * 40)
        self.assertEqual([item["number"] for item in sources["previews"]], [*range(1, 101), 103])

    def test_comments_are_updated_reused_and_closed_previews_retired(self):
        """Ensures deployed URLs are posted once, updated on commits, and retired after close."""
        comments = [{"id": 1, "body": previews.MARKER + "\nHuman comment", "user": {"login": "example"},
                     "issue_url": "https://api.github.com/repos/example/skills/issues/5"}]
        writes = []
        def request(endpoint, method="GET", data=None):
            if method != "GET":
                writes.append((endpoint, method, data))
                if method == "POST":
                    comments.append({"id": 2, "body": data["body"], "user": {"login": "github-actions[bot]"},
                                     "issue_url": "https://api.github.com/repos/example/skills/issues/5"})
                else:
                    comments[1]["body"] = data["body"]
                return {}
            if endpoint.endswith("/pulls/5"):
                return {"state": "closed"}
            return comments
        sources = [{"number": 5, "sha": "a" * 40}]
        previews.comment_previews(request, "example/skills", "https://example.github.io/skills", sources)
        self.assertEqual([method for _, method, _ in writes], ["POST"])
        self.assertIn("https://example.github.io/skills/pr-preview/5/", comments[1]["body"])
        previews.comment_previews(request, "example/skills", "https://example.github.io/skills/", sources)
        self.assertEqual(len(writes), 1)
        sources[0]["sha"] = "b" * 40
        previews.comment_previews(request, "example/skills", "https://skills.example/", sources)
        self.assertEqual(writes[-1][1], "PATCH")
        self.assertIn("https://skills.example/pr-preview/5/", comments[1]["body"])
        self.assertIn("b" * 40, comments[1]["body"])
        previews.comment_previews(request, "example/skills", "https://skills.example/", [])
        self.assertEqual(comments[1]["body"], previews.REMOVED)
        count = len(writes)
        previews.comment_previews(request, "example/skills", "https://skills.example/", [])
        self.assertEqual(len(writes), count)
        self.assertEqual(comments[0]["body"], previews.MARKER + "\nHuman comment")

    def test_open_preview_comment_is_not_retired(self):
        """Ensures a comment for an open PR is not marked closed merely because it is absent."""
        comment = {"id": 2, "body": previews.MARKER + "\nExisting", "user": {"login": "github-actions[bot]"},
                   "issue_url": "https://api.github.com/repos/example/skills/issues/5"}
        def request(endpoint, method="GET", data=None):
            self.assertEqual(method, "GET")
            return {"state": "open"} if endpoint.endswith("/pulls/5") else [comment]
        previews.comment_previews(request, "example/skills", "https://skills.example/", [])

    def test_cli_uses_only_validated_commits_and_exports_deployed_sources(self):
        """Ensures build mode fetches immutable sources and publishes metadata only after packaging."""
        sources = {"main": "a" * 40, "previews": [{"number": 5, "sha": "b" * 40}]}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environment = {"GITHUB_REPOSITORY": "example/skills", "GITHUB_OUTPUT": str(output)}
            with patch.dict("os.environ", environment), patch.object(sys, "argv", ["pages_preview.py", "build"]), \
                    patch.object(previews, "collect_sources", return_value=sources), \
                    patch.object(previews, "git") as fetch, patch.object(previews, "package") as package:
                previews.main()
                fetch.assert_called_once_with(previews.ROOT, "fetch", "--no-tags", "origin", "a" * 40, "b" * 40)
                package.assert_called_once_with(previews.ROOT, previews.ROOT / "dist", sources)
            self.assertEqual(json.loads(output.read_text().removeprefix("previews=")), sources["previews"])
            sources["main"] = "--help"
            with patch.dict("os.environ", environment), patch.object(sys, "argv", ["pages_preview.py", "build"]), \
                    patch.object(previews, "collect_sources", return_value=sources), \
                    patch.object(previews, "git") as fetch, patch.object(previews, "package") as package:
                with self.assertRaisesRegex(ValueError, "source commit"):
                    previews.main()
                fetch.assert_not_called()
                package.assert_not_called()


class WorkflowTests(unittest.TestCase):
    def test_trusted_checkout_serial_deployment_and_comment_permissions(self):
        """Ensures PR data cannot select executable code or acquire deployment/comment credentials."""
        workflow = (ROOT / ".github/workflows/pages.yml").read_text()
        self.assertIn("pull_request_target:", workflow)
        self.assertIn("types: [opened, reopened, synchronize, closed]", workflow)
        self.assertIn("group: pages\n", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        build, deploy = workflow.split("\n  deploy:\n")
        deploy, comment = deploy.split("\n  comment:\n")
        self.assertIn("ref: main", build)
        self.assertIn("head.repo.full_name == github.repository", build)
        self.assertIn("github.ref == 'refs/heads/main'", build)
        self.assertIn("contents: read", build)
        self.assertIn("pull-requests: read", build)
        self.assertNotIn(": write", build)
        self.assertIn("pages: write", deploy)
        self.assertIn("id-token: write", deploy)
        self.assertNotIn("checkout@", deploy)
        self.assertIn("needs: [build, deploy]", comment)
        self.assertIn("pull-requests: write", comment)
        self.assertIn("ref: main", comment)
        self.assertNotIn("head.sha", workflow)
