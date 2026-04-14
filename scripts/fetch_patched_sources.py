#!/usr/bin/env python3
"""Fetch package source trees and apply local patch scripts for audit review."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent.parent
PACKAGES_DIR = ROOT / "packages"


def load_package(package_name: str) -> dict:
    package_path = PACKAGES_DIR / f"{package_name}.yml"
    if not package_path.exists():
        raise FileNotFoundError(f"Unknown package: {package_name}")
    return yaml.safe_load(package_path.read_text(encoding="utf-8"))


def resolve_packages(package_name: str) -> list[dict]:
    if package_name == "all":
        return [yaml.safe_load(path.read_text(encoding="utf-8")) for path in sorted(PACKAGES_DIR.glob("*.yml"))]
    return [load_package(package_name)]


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def copy_tree_without_git(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".git"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and patch source trees for wheel audit")
    parser.add_argument("--package", required=True, help="Package name or 'all'")
    parser.add_argument("--output-dir", required=True, help="Output directory for patched sources")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    work_root = ROOT / ".audit-work" / "sources"
    work_root.mkdir(parents=True, exist_ok=True)

    for package in resolve_packages(args.package):
        package_name = package["name"]
        clone_dir = work_root / package_name
        if clone_dir.exists():
            shutil.rmtree(clone_dir)

        run(["git", "clone", f"https://github.com/{package['source_repo']}.git", str(clone_dir)])
        if package.get("source_tag"):
            run(["git", "checkout", package["source_tag"]], cwd=clone_dir)

        patch_script = package.get("patch_script")
        if patch_script:
            run([sys.executable, str(ROOT / patch_script)], cwd=clone_dir)

        target_dir = output_dir / package_name
        copy_tree_without_git(clone_dir, target_dir)

        metadata = {
            "package": package_name,
            "source_repo": package["source_repo"],
            "source_tag": package.get("source_tag", ""),
            "patch_script": patch_script or "",
            "build_subdir": package.get("build_subdir", ""),
        }
        (target_dir / ".cuda-wheels-meta.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        print(f"Fetched patched sources for {package_name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
