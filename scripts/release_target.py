#!/usr/bin/env python3
"""Resolve release-target repository data for workflow and index generation."""
from __future__ import annotations

import argparse
import json
import os
import sys


def resolve_release_repo(explicit_repo: str | None = None) -> str:
    repo = explicit_repo or os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required when --repo is not provided")

    owner, sep, repo_name = repo.partition("/")
    if sep != "/" or not owner or not repo_name:
        raise ValueError(f"Repository must be in OWNER/REPO format, got: {repo!r}")
    return repo


def build_release_target(explicit_repo: str | None = None) -> dict[str, str]:
    release_repo = resolve_release_repo(explicit_repo)
    owner, repo_name = release_repo.split("/", 1)
    return {
        "release_repo": release_repo,
        "index_url": f"https://{owner.lower()}.github.io/{repo_name}",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=None, help="Repository in OWNER/REPO format")
    parser.add_argument(
        "--format",
        choices=("json", "index-url"),
        default="json",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        target = build_release_target(args.repo)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "index-url":
        print(target["index_url"])
        return 0

    print(json.dumps(target, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
