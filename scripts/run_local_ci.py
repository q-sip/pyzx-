#!/usr/bin/env python3
import re
import subprocess
import sys
from typing import Tuple

PYLINT_FILE = "pyzx/graph/graph_neo4j.py"
PYLINT_THRESHOLD = 9.5


def run_and_capture(cmd: list[str]) -> Tuple[int, str]:
    """Run a command, stream output live, and also capture it for parsing."""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert proc.stdout is not None

    out_lines: list[str] = []
    for line in proc.stdout:
        sys.stdout.write(line)
        out_lines.append(line)

    rc = proc.wait()
    return rc, "".join(out_lines)


def extract_pylint_score(output: str) -> float | None:
    matches = re.findall(r"rated at ([0-9]+(?:\.[0-9]+)?)/10", output)
    if not matches:
        return None
    return float(matches[-1])


def main() -> int:
    # 1) Pylint (score gate)
    # rc, out = run_and_capture([sys.executable, "-m", "pylint", PYLINT_FILE])
    # score = extract_pylint_score(out)
    # if score is None:
    #     print("FAILED: Could not determine pylint score.")
    #     return 1

    # print(f"Pylint score: {score:.2f}/10 (threshold {PYLINT_THRESHOLD})")
    # if score < PYLINT_THRESHOLD:
    #     print(f"FAILED: pylint score {score:.2f} < {PYLINT_THRESHOLD}")
    #     return 1

    # 2) mypy (match your workflow)
    print('runaa')
    rc, _ = run_and_capture([sys.executable, "-m", "mypy", '--follow-imports=silent', 'tests/'])
    if rc != 0:
        print("FAILED: mypy errors.")
        return rc
    print('runattu')

    # # 3) unit tests (match your workflow)
    # rc, _ = run_and_capture(
    #     [
    #         sys.executable,
    #         "-m",
    #         "unittest",
    #         "discover",
    #         "-s",
    #         "tests",
    #         "-t",
    #         ".",
    #         "--verbose",
    #     ]
    # )
    # if rc != 0:
    #     print("FAILED: unit tests.")
    #     return rc

    print("PASS: local CI checks succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
