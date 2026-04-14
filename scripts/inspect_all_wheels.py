#!/usr/bin/env python3
"""Inspect wheel files and emit JSON/Markdown audit reports."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from email.parser import Parser
from pathlib import Path


WHEEL_RE = re.compile(
    r"^(?P<name>[^-]+)-(?P<version>[^-]+)-(?P<python_tag>[^-]+)-(?P<abi_tag>[^-]+)-(?P<platform_tag>.+)\.whl$"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_metadata(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata_text = archive.read(metadata_name).decode("utf-8")
    parsed = Parser().parsestr(metadata_text)
    return {
        "name": parsed.get("Name", ""),
        "version": parsed.get("Version", ""),
        "summary": parsed.get("Summary", ""),
        "requires_python": parsed.get("Requires-Python", ""),
    }


def inspect_wheel(path: Path) -> dict[str, object]:
    match = WHEEL_RE.match(path.name)
    if not match:
        raise ValueError(f"Unparseable wheel filename: {path.name}")

    metadata = read_metadata(path)
    return {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "name": metadata["name"] or match.group("name"),
        "version": metadata["version"] or match.group("version"),
        "python_tag": match.group("python_tag"),
        "abi_tag": match.group("abi_tag"),
        "platform_tag": match.group("platform_tag"),
        "summary": metadata["summary"],
        "requires_python": metadata["requires_python"],
    }


def render_markdown(items: list[dict[str, object]]) -> str:
    lines = [
        "# Wheel Inspection Report",
        "",
        "| Filename | Version | Python Tag | Platform Tag | Size Bytes | SHA256 |",
        "|:--|:--|:--|:--|--:|:--|",
    ]
    for item in items:
        lines.append(
            f"| `{item['filename']}` | `{item['version']}` | `{item['python_tag']}` | `{item['platform_tag']}` | {item['size_bytes']} | `{item['sha256']}` |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect wheel files")
    parser.add_argument("--wheel-dir", required=True, help="Directory containing wheel files")
    parser.add_argument("--output-json", required=True, help="JSON report path")
    parser.add_argument("--output-md", required=True, help="Markdown report path")
    args = parser.parse_args()

    wheel_dir = Path(args.wheel_dir)
    wheels = sorted(wheel_dir.glob("*.whl"))
    if not wheels:
        raise FileNotFoundError(f"No wheel files found in {wheel_dir}")

    items = [inspect_wheel(path) for path in wheels]
    Path(args.output_json).write_text(json.dumps(items, indent=2) + "\n", encoding="utf-8")
    Path(args.output_md).write_text(render_markdown(items), encoding="utf-8")
    print(f"Inspected {len(items)} wheel(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
