#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import requests


def sh(cmd: List[str], check: bool = True) -> str:
    p = subprocess.run(cmd, text=True, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return p.stdout


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def extract_unified_diff(text: str) -> Optional[str]:
    m = re.search(r"```(?:diff)?\n(.*?)\n```", text, flags=re.S)
    if m:
        block = m.group(1).strip()
        if "diff --git" in block:
            return block
    idx = text.find("diff --git")
    if idx >= 0:
        return text[idx:].strip()
    return None


def apply_patch(patch: str) -> None:
    p = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        input=patch,
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        raise RuntimeError(
            f"git apply failed.\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}\nPATCH(head):\n{patch[:4000]}"
        )


def chat(base_url: str, api_key: str, model: str, system: str, user: str) -> str:
    base = base_url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    url = base + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=900)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["docs-tests", "pylint-fix"], required=True)
    ap.add_argument("--touched-files")
    ap.add_argument("--focus-file")
    ap.add_argument("--tests-dir")
    ap.add_argument("--pylint-log")
    args = ap.parse_args()

    base_url = os.environ.get("AGENT_BASE_URL", "").strip()
    model = os.environ.get("AGENT_MODEL", "").strip()
    api_key = os.environ.get("AGENT_API_KEY", "").strip()

    if not base_url or not model or not api_key:
        print("Missing AGENT_BASE_URL / AGENT_MODEL / AGENT_API_KEY.", file=sys.stderr)
        return 2

    repo_root = sh(["git", "rev-parse", "--show-toplevel"]).strip()
    os.chdir(repo_root)

    system = (
        "You are a senior Python engineer.\n"
        "Return ONLY a unified diff (git patch) that applies cleanly.\n"
        "No explanations. No markdown. Diff only.\n"
        "Do not change runtime behavior unless fixing lint issues.\n"
        "Prefer minimal, reviewable changes.\n"
    )

    if args.mode == "docs-tests":
        touched = [ln.strip() for ln in read_text(args.touched_files).splitlines() if ln.strip()]
        if not touched:
            print("No touched files; exiting.")
            return 0

        focus_file = args.focus_file or ""
        tests_dir = args.tests_dir or "tests"

        # Include narrow context: focus file + existing tests folder + touched files
        ctx_parts = []

        def add_file(path: str) -> None:
            if Path(path).exists():
                ctx_parts.append(f"### FILE: {path}\n{read_text(path)}\n")

        for f in touched:
            add_file(f)

        # Add a bit of tests context (directory listing + conftest if present)
        tests_path = Path(tests_dir)
        if tests_path.exists():
            listing = "\n".join(str(p) for p in sorted(tests_path.glob("**/*.py")))
            ctx_parts.append(f"### TEST FILES LIST ({tests_dir})\n{listing}\n")
            conftest = tests_path / "conftest.py"
            if conftest.exists():
                add_file(str(conftest))
            # Add up to a few existing tests for style/context
            for p in sorted(tests_path.glob("test_*.py"))[:5]:
                add_file(str(p))

        user = (
            "Task:\n"
            "1) Improve docstrings/comments ONLY for the fork-touched Python files listed.\n"
            "2) Add/extend pytest tests under the specified tests directory (neo4j graph focus).\n\n"
            "Hard constraints:\n"
            "- Output must be a unified diff.\n"
            f"- Only modify the touched files and files under {tests_dir}/\n"
            "- No CI/config changes.\n\n"
            f"Primary focus file: {focus_file}\n"
            f"Tests directory: {tests_dir}\n\n"
            "Touched Python files:\n"
            + "\n".join(f"- {f}" for f in touched)
            + "\n\nContext:\n\n"
            + "\n".join(ctx_parts)
        )

        resp = chat(base_url, api_key, model, system, user)
        patch = extract_unified_diff(resp)
        if not patch:
            print("Model did not return a valid unified diff.", file=sys.stderr)
            print(resp[:2000], file=sys.stderr)
            return 3
        apply_patch(patch)
        return 0

    # pylint-fix
    pylint_log = read_text(args.pylint_log)
    focus_file = args.focus_file
    focus_content = read_text(focus_file)

    user = (
        "Task:\n"
        "Fix pylint issues to raise score above threshold without changing behavior.\n"
        "Prefer small, safe improvements (typing, naming, docstrings, imports).\n\n"
        "Hard constraints:\n"
        "- Output must be a unified diff.\n"
        f"- Only modify: {focus_file}\n\n"
        "Pylint output:\n"
        + pylint_log
        + "\n\n"
        f"### FILE: {focus_file}\n{focus_content}\n"
    )

    resp = chat(base_url, api_key, model, system, user)
    patch = extract_unified_diff(resp)
    if not patch:
        print("Model did not return a valid unified diff.", file=sys.stderr)
        print(resp[:2000], file=sys.stderr)
        return 3
    apply_patch(patch)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
