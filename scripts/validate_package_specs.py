#!/usr/bin/env python3
"""Validate package YAML specs for structure and common data mistakes."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


CUDA_RE = re.compile(r"^\d+\.\d+$")
PYTHON_RE = re.compile(r"^3\.\d+$")
PYTORCH_RE = re.compile(r"^\d+\.\d+\.\d+$")
ARCH_TOKEN_RE = re.compile(r"^\d+\.\d+$")
KNOWN_TOP_LEVEL_KEYS = {
    "arch_list",
    "build_matrix",
    "build_subdir",
    "clone_recursive",
    "extra_cuda_components",
    "extra_deps",
    "free_disk_space",
    "max_jobs",
    "name",
    "patch_script",
    "pre_build_script",
    "source_repo",
    "source_tag",
    "cuda_installer",
    "version",
}
KNOWN_COMBINATION_KEYS = {"arch_list", "cuda", "pytorch", "python_versions"}
KNOWN_PLATFORMS = {"linux", "windows"}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate_arch_list(value: str, label: str, errors: list[str]) -> None:
    tokens = value.split()
    if not tokens:
        fail(f"{label}: arch_list must not be empty", errors)
        return
    for token in tokens:
        if not ARCH_TOKEN_RE.match(token):
            fail(f"{label}: invalid arch token {token!r}", errors)


def validate_package(path: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    label = path.name

    if not isinstance(data, dict):
        return [f"{label}: top-level YAML must be a mapping"]

    unknown_keys = sorted(set(data) - KNOWN_TOP_LEVEL_KEYS)
    if unknown_keys:
        fail(f"{label}: unknown top-level keys: {', '.join(unknown_keys)}", errors)

    for key in ("name", "source_repo", "version", "build_matrix"):
        if key not in data:
            fail(f"{label}: missing required key {key!r}", errors)

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        fail(f"{label}: name must be a non-empty string", errors)

    source_repo = data.get("source_repo")
    if not isinstance(source_repo, str) or source_repo.count("/") != 1:
        fail(f"{label}: source_repo must look like owner/repo", errors)

    version = data.get("version")
    if not isinstance(version, str) or not version.strip():
        fail(f"{label}: version must be a non-empty string", errors)

    arch_list = data.get("arch_list")
    if arch_list is not None:
        if not isinstance(arch_list, str):
            fail(f"{label}: arch_list must be a string", errors)
        else:
            validate_arch_list(arch_list, label, errors)

    build_matrix = data.get("build_matrix")
    if not isinstance(build_matrix, dict):
        fail(f"{label}: build_matrix must be a mapping", errors)
        return errors

    platforms = build_matrix.get("platforms")
    if not isinstance(platforms, list) or not platforms:
        fail(f"{label}: build_matrix.platforms must be a non-empty list", errors)
    else:
        invalid_platforms = [platform for platform in platforms if platform not in KNOWN_PLATFORMS]
        if invalid_platforms:
            fail(f"{label}: invalid platforms: {', '.join(invalid_platforms)}", errors)

    combinations = build_matrix.get("combinations")
    if not isinstance(combinations, list) or not combinations:
        fail(f"{label}: build_matrix.combinations must be a non-empty list", errors)
        return errors

    seen_combo_keys: set[tuple[str, str, str]] = set()
    for index, combo in enumerate(combinations, start=1):
        combo_label = f"{label}: combination {index}"
        if not isinstance(combo, dict):
            fail(f"{combo_label} must be a mapping", errors)
            continue

        unknown_combo_keys = sorted(set(combo) - KNOWN_COMBINATION_KEYS)
        if unknown_combo_keys:
            fail(f"{combo_label}: unknown keys: {', '.join(unknown_combo_keys)}", errors)

        cuda = combo.get("cuda")
        pytorch = combo.get("pytorch")
        python_versions = combo.get("python_versions")

        if not isinstance(cuda, str) or not CUDA_RE.match(cuda):
            fail(f"{combo_label}: invalid cuda value {cuda!r}", errors)
        if not isinstance(pytorch, str) or not PYTORCH_RE.match(pytorch):
            fail(f"{combo_label}: invalid pytorch value {pytorch!r}", errors)
        if not isinstance(python_versions, list) or not python_versions:
            fail(f"{combo_label}: python_versions must be a non-empty list", errors)
        else:
            for python_version in python_versions:
                if not isinstance(python_version, str) or not PYTHON_RE.match(python_version):
                    fail(f"{combo_label}: invalid python version {python_version!r}", errors)

        combo_arch_list = combo.get("arch_list")
        if combo_arch_list is not None:
            if not isinstance(combo_arch_list, str):
                fail(f"{combo_label}: arch_list must be a string", errors)
            else:
                validate_arch_list(combo_arch_list, combo_label, errors)

        if isinstance(cuda, str) and isinstance(pytorch, str) and isinstance(python_versions, list):
            for python_version in python_versions:
                if isinstance(python_version, str):
                    combo_key = (cuda, pytorch, python_version)
                    if combo_key in seen_combo_keys:
                        fail(
                            f"{combo_label}: duplicate cuda/pytorch/python tuple {cuda}/{pytorch}/{python_version}",
                            errors,
                        )
                    seen_combo_keys.add(combo_key)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate package YAML specs")
    parser.add_argument("--packages-dir", default="packages", help="Package spec directory")
    args = parser.parse_args()

    package_paths = sorted(Path(args.packages_dir).glob("*.yml"))
    if not package_paths:
        print("No package specs found", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in package_paths:
        errors.extend(validate_package(path))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Validated {len(package_paths)} package spec(s) successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
