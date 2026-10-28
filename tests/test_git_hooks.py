#!/usr/bin/env python3
"""YaPOC Git Hooks integration test suite using GitPython.

This module executes integration tests against the bare git repository
configured in base.conf. It tests server-side hook rejection of
prohibited file patterns using GitPython for repository interactions.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import unittest

import git


def load_base_config(conf_path: Path) -> dict[str, str]:
    """Parse shell variable definitions from base.conf.

    Resolves referenced shell variables to stay in sync with
    setup-env.sh and base.conf configuration.
    """
    config: dict[str, str] = {}
    if not conf_path.is_file():
        return config

    with open(conf_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # Ignore empty lines and shell comments
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, val = stripped.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                # Expand variable references (e.g. $GIT_REPO_BASE_PATH)
                for pk, pv in config.items():
                    val = val.replace(f"${pk}", pv)
                    val = val.replace(f"${{{pk}}}", pv)
                config[key] = val
    return config


# Locate base.conf from current directory or parent directory
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
CONF_PATH = (
    REPO_ROOT / "base.conf"
    if (REPO_ROOT / "base.conf").is_file()
    else TESTS_DIR / "base.conf"
)
BASE_CONF = load_base_config(CONF_PATH)

# Target bare repository and test working copy paths
GIT_TEST_REPO_PATH = Path(
    os.environ.get(
        "GIT_TEST_REPO_PATH",
        BASE_CONF.get("GIT_TEST_REPO_PATH", "/srv/git/test-repo.git"),
    )
)
WORKING_COPY_PATH = Path(
    os.environ.get(
        "WORKING_COPY_PATH",
        Path.home() / "git" / BASE_CONF.get(
            "GIT_TEST_REPO_NAME", "test-repo.git"
        ),
    )
)


def discard_current_commit(repo: git.Repo) -> None:
    """Discard the most recent commit and restore a pristine working tree.

    If the commit has a parent, a hard reset to HEAD~1 restores the
    tree. If the commit is the root commit (no parent exists), the HEAD
    ref is deleted to restore the unborn branch state, and all tracked
    and untracked files are wiped.
    """
    try:
        # Check if HEAD has at least one parent commit
        has_parent = len(repo.head.commit.parents) > 0
    except (ValueError, git.exc.GitCommandError):
        # HEAD is unborn or invalid (e.g. root commit rejected)
        has_parent = False

    if has_parent:
        # Hard reset back to parent commit
        repo.git.reset("--hard", "HEAD~1")
    else:
        # Root commit on initial branch: delete ref to return to unborn state
        repo.git.update_ref("-d", "HEAD")
        # Untrack files from index and clean working tree
        try:
            repo.git.rm("-rf", ".", ignore_unmatch=True)
        except git.exc.GitCommandError:
            pass

    # Clean any leftover untracked or ignored files
    repo.git.clean("-fdx")


def wgit_commit(
    repo: git.Repo,
    message: str,
    discard_prohibited: bool = False,
) -> tuple[bool, str]:
    """Stage changes, commit, and push to the remote repository.

    Parameters:
        repo: git.Repo instance for the local working copy.
        message: Git commit message.
        discard_prohibited: If True and push is rejected, discards
            the local commit and cleans the working tree.

    Returns:
        tuple of (success: bool, output: str)
    """
    # Stage all changes (new, modified, deleted)
    repo.git.add(A=True)

    # Create the local commit
    repo.git.commit("-m", message)

    # Attempt to push commit to remote repository
    try:
        push_output = repo.git.push()
        return True, str(push_output)
    except git.exc.GitCommandError as exc:
        # Push was rejected by server hook or remote
        if discard_prohibited:
            discard_current_commit(repo)
        return False, f"{exc.stdout}\n{exc.stderr}"


class TestYaPOCGitHooks(unittest.TestCase):
    """Integration test suite executing git hook checks using GitPython."""

    repo: git.Repo

    @classmethod
    def setUpClass(cls) -> None:
        """Configure global git user identity and prepare working copy."""
        # Ensure safe.directory and user identity are set
        git_cmd = git.Git()
        git_cmd.config("--global", "user.name", "Kanku User")
        git_cmd.config("--global", "user.email", "nobody@kanku.info")
        git_cmd.config(
            "--global",
            "--add",
            "safe.directory",
            str(GIT_TEST_REPO_PATH),
        )

        # Re-create fresh working copy directory to avoid stale state
        if WORKING_COPY_PATH.exists():
            shutil.rmtree(WORKING_COPY_PATH)
        WORKING_COPY_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Clone target bare repository using GitPython
        cls.repo = git.Repo.clone_from(
            url=str(GIT_TEST_REPO_PATH),
            to_path=str(WORKING_COPY_PATH),
        )

    def test_01_reject_osc_directory(self) -> None:
        """Test that committing files inside .osc directory is rejected."""
        osc_dir = WORKING_COPY_PATH / ".osc"
        osc_dir.mkdir(parents=True, exist_ok=True)
        (osc_dir / ".keep").touch()

        tc_name = "initial commit containing the .osc file"
        # Push should be rejected by pre-receive hook; discard_prohibited=True
        # cleans the unpushed commit so subsequent test cases start clean.
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=True,
        )
        self.assertFalse(
            success,
            f"Expected push rejection for .osc, but push succeeded: {output}",
        )
        # Ensure working tree was cleaned after rejection
        self.assertEqual(self.repo.git.status("--short").strip(), "")

    def test_02_reject_obsinfo_file(self) -> None:
        """Test that committing a file with .obsinfo suffix is rejected."""
        (WORKING_COPY_PATH / "package.obsinfo").touch()

        tc_name = "add file with .obsinfo suffix"
        # Push should be rejected by pre-receive hook and discarded
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=True,
        )
        self.assertFalse(
            success,
            f"Expected push rejection for .obsinfo, but push succeeded: "
            f"{output}",
        )
        # Ensure working tree was cleaned after rejection
        self.assertEqual(self.repo.git.status("--short").strip(), "")

    def test_03_reject_obscpio_file_in_subdir(self) -> None:
        """Test that committing a .obscpio file in a subdir is rejected."""
        subdir = WORKING_COPY_PATH / "subdir"
        subdir.mkdir(parents=True, exist_ok=True)
        (subdir / "archive.obscpio").touch()

        tc_name = "add file with .obscpio suffix in a subdir"
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=True,
        )
        self.assertFalse(
            success,
            f"Expected push rejection for .obscpio, but push succeeded: "
            f"{output}",
        )
        self.assertEqual(self.repo.git.status("--short").strip(), "")

    def test_04_allow_obsinfo_bak_file(self) -> None:
        """Test that a file ending in .obsinfo.bak is accepted."""
        (WORKING_COPY_PATH / "package.obsinfo.bak").touch()

        tc_name = "add file ending in .obsinfo.bak"
        # Positive test case: commit should succeed and remain in history
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=False,
        )
        self.assertTrue(
            success,
            f"Expected push to succeed, but push failed: {output}",
        )
        self.assertEqual(self.repo.git.status("--short").strip(), "")

    def test_05_allow_obscpio_prefix_file(self) -> None:
        """Test that a file with obscpio prefix and .py suffix is accepted."""
        (WORKING_COPY_PATH / "obscpio_generator.py").touch()

        tc_name = "add file with obscpio prefix"
        # Positive test case: commit should succeed and remain in history
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=False,
        )
        self.assertTrue(
            success,
            f"Expected push to succeed, but push failed: {output}",
        )
        self.assertEqual(self.repo.git.status("--short").strip(), "")

    def test_06_allow_file_ending_with_dot_osc(self) -> None:
        """Test that a regular file named test.osc is accepted."""
        (WORKING_COPY_PATH / "test.osc").touch()

        tc_name = "add file which ends with .osc"
        # Positive test case: commit should succeed and remain in history
        success, output = wgit_commit(
            self.repo,
            tc_name,
            discard_prohibited=False,
        )
        self.assertTrue(
            success,
            f"Expected push to succeed, but push failed: {output}",
        )
        self.assertEqual(self.repo.git.status("--short").strip(), "")


if __name__ == "__main__":
    unittest.main()
