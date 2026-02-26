#!/usr/bin/env python3
import subprocess
import sys


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def main() -> int:
    # Make sure we're in a git repo
    try:
        inside = run(["git", "rev-parse", "--is-inside-work-tree"])
        if inside.lower() != "true":
            print("Not inside a git work tree; skipping up-to-date check.")
            return 0
    except Exception:
        print("Could not determine git repo state; skipping up-to-date check.")
        return 0

    # Get the current branch name
    try:
        current_branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

        # If we are NOT on dev, skip the check and continue (pass)
        if current_branch != "dev":
            print(f"On branch '{current_branch}'; skipping dev up-to-date check.")
            return 0

    except Exception:
        print("Could not determine current branch; skipping check.")
        return 0

    # Fetch origin/dev (safe; does not modify working tree)
    try:
        subprocess.run(["git", "fetch", "origin", "dev"], check=True)
    except subprocess.CalledProcessError:
        print("FAILED: git fetch origin dev")
        print("Fix: check your network/remote, then retry commit.")
        return 1

    # Ensure origin/dev exists
    try:
        run(["git", "rev-parse", "--verify", "origin/dev"])
    except Exception:
        print("Could not find origin/dev after fetch; skipping check.")
        return 0

    # Count how many commits we're ahead/behind origin/dev
    # Output is: "<ahead> <behind>"
    try:
        counts = run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...origin/dev"]
        )
        ahead_s, behind_s = counts.split()
        ahead = int(ahead_s)
        behind = int(behind_s)
    except Exception as e:
        print(f"Could not compare HEAD with origin/dev: {e}")
        return 1

    if behind > 0:
        print(f"FAILED: Your branch is behind origin/dev by {behind} commit(s).")
        print("Fix (recommended): git pull --rebase origin dev")
        print("Then re-run commit.")
        return 1

    if ahead > 0:
        # Being ahead is fine; just informational.
        print(f"Info: Your branch is ahead of origin/dev by {ahead} commit(s).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
