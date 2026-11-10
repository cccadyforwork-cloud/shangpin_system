"""Checks for the local Git guard's noninteractive remote verification."""

import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import owner_git_guard


class OwnerGitGuardGitTest(unittest.TestCase):
    def test_discards_gui_askpass_when_calling_git(self):
        success = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
        with patch.dict(os.environ, {"GIT_ASKPASS": "/tmp/desktop-askpass",
                                      "SSH_ASKPASS": "/tmp/desktop-askpass"}):
            with patch.object(owner_git_guard.subprocess, "run", return_value=success) as run:
                result = owner_git_guard.git(Path("/tmp/repo"), "ls-remote", "origin")
        self.assertIs(result, success)
        env = run.call_args.kwargs["env"]
        self.assertNotIn("GIT_ASKPASS", env)
        self.assertNotIn("SSH_ASKPASS", env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")

    def test_retries_transient_network_failure_but_still_blocks(self):
        failed = SimpleNamespace(returncode=128, stdout="", stderr="Could not resolve host: github.com")
        with patch.object(owner_git_guard.subprocess, "run", side_effect=[failed, failed]) as run:
            with patch.object(owner_git_guard.time, "sleep"):
                with self.assertRaisesRegex(owner_git_guard.GuardError, "temporary network failure"):
                    owner_git_guard.git(Path("/tmp/repo"), "ls-remote", "origin")
        self.assertEqual(run.call_count, 2)

    def test_does_not_retry_authentication_error_or_expose_details(self):
        failed = SimpleNamespace(returncode=128, stdout="", stderr="secret credential: Repository not found")
        with patch.object(owner_git_guard.subprocess, "run", return_value=failed) as run:
            with self.assertRaises(owner_git_guard.GuardError) as raised:
                owner_git_guard.git(Path("/tmp/repo"), "ls-remote", "origin")
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("secret credential", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
