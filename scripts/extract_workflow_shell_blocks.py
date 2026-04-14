#!/usr/bin/env python3
"""Extract bash/sh workflow run blocks into standalone scripts for shellcheck."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml


GITHUB_EXPR_RE = re.compile(r"\$\{\{[^}]+\}\}")


def iter_yaml_files(root: Path) -> list[Path]:
    return sorted(root.glob("*.yml")) + sorted(root.glob("*.yaml"))


def should_lint_shell(shell: str | None) -> bool:
    if shell is None:
        return True
    shell_name = shell.strip().lower()
    return shell_name in {"bash", "sh"} or shell_name.startswith("bash ")


def extract_runs(node: object, source: Path, output_dir: Path, prefix: str, counter: list[int]) -> int:
    written = 0
    if isinstance(node, dict):
        run_value = node.get("run")
        if isinstance(run_value, str) and should_lint_shell(node.get("shell")):
            counter[0] += 1
            target = output_dir / f"{prefix}_{counter[0]:03d}.sh"
            normalized = GITHUB_EXPR_RE.sub("${GITHUB_EXPR}", run_value.rstrip())
            target.write_text(f"#!/usr/bin/env bash\nset -euo pipefail\n{normalized}\n", encoding="utf-8")
            written += 1
        for value in node.values():
            written += extract_runs(value, source, output_dir, prefix, counter)
    elif isinstance(node, list):
        for value in node:
            written += extract_runs(value, source, output_dir, prefix, counter)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract workflow shell blocks for shellcheck")
    parser.add_argument("--workflow-dir", required=True, help="Directory containing workflow YAML files")
    parser.add_argument("--action-dir", required=True, help="Directory containing composite action YAML files")
    parser.add_argument("--output-dir", required=True, help="Directory to write extracted shell scripts")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for source in iter_yaml_files(Path(args.workflow_dir)):
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        total += extract_runs(data, source, output_dir, source.stem, [0])

    for source in sorted(Path(args.action_dir).glob("*/action.yml")):
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        total += extract_runs(data, source, output_dir, source.parent.name, [0])

    print(f"Extracted {total} shell block(s) to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
