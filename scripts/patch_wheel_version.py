#!/usr/bin/env python3
"""
Patch wheel METADATA to include the full version from the wheel filename.
"""

import base64
import csv
import hashlib
import io
import re
import sys
import tempfile
import zipfile
from pathlib import Path


def extract_version_from_filename(filename: str) -> tuple[str, str]:
    m = re.match(r"^([A-Za-z0-9_]+)-([^-]+)-(cp|py)", filename)
    if not m:
        raise ValueError(f"Could not parse wheel filename: {filename}")
    return m.group(1), m.group(2)


def hash_content(data: bytes) -> tuple[str, int]:
    digest = hashlib.sha256(data).digest()
    b64 = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={b64}", len(data)


def rebuild_record(tmpdir: Path, dist_info_name: str) -> None:
    record_path = tmpdir / dist_info_name / "RECORD"
    record_rel = f"{dist_info_name}/RECORD"

    rows = []
    for file in sorted(tmpdir.rglob("*")):
        if not file.is_file():
            continue
        rel = str(file.relative_to(tmpdir))
        if rel == record_rel:
            continue
        digest, size = hash_content(file.read_bytes())
        rows.append((rel, digest, str(size)))

    rows.append((record_rel, "", ""))

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerows(rows)
    record_path.write_text(buf.getvalue(), encoding="utf-8")


def fix_wheel(wheel_path: Path) -> bool:
    filename = wheel_path.name
    pkg_name, version = extract_version_from_filename(filename)

    if "+" not in version:
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(wheel_path, "r") as zf:
            zf.extractall(tmpdir)

        dist_info_dirs = list(tmpdir.glob("*.dist-info"))
        if not dist_info_dirs:
            print(f"  WARNING: No .dist-info found in {filename}, skipping")
            return False
        dist_info = dist_info_dirs[0]

        metadata_path = dist_info / "METADATA"
        if not metadata_path.exists():
            print(f"  WARNING: No METADATA found in {filename}, skipping")
            return False

        content = metadata_path.read_text(encoding="utf-8")

        m = re.search(r"^Version: (.+)$", content, re.MULTILINE)
        if m and m.group(1) == version:
            print(f"  {filename}: already correct ({version})")
            return False

        current_version = m.group(1) if m else "unknown"
        print(f"  {filename}: {current_version} -> {version}")

        content = re.sub(r"^Version: .+$", f"Version: {version}", content, flags=re.MULTILINE)
        metadata_path.write_text(content, encoding="utf-8")

        old_name = dist_info.name
        new_name = f"{pkg_name}-{version}.dist-info"
        if old_name != new_name:
            new_dist_info = dist_info.parent / new_name
            dist_info.rename(new_dist_info)
            dist_info = new_dist_info

        rebuild_record(tmpdir, dist_info.name)

        with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in sorted(tmpdir.rglob("*")):
                if file.is_file():
                    zf.write(file, file.relative_to(tmpdir))

    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python patch_wheel_version.py <wheel_or_directory> [...]")
        sys.exit(1)

    paths = [Path(p) for p in sys.argv[1:]]
    fixed = 0

    for path in paths:
        if path.is_dir():
            wheels = sorted(path.glob("*.whl"))
        elif path.suffix == ".whl":
            wheels = [path]
        else:
            print(f"Skipping non-wheel: {path}")
            continue

        for whl in wheels:
            if fix_wheel(whl):
                fixed += 1

    print(f"Fixed {fixed} wheel(s)")


if __name__ == "__main__":
    main()
