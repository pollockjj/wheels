#!/usr/bin/env python3
"""Generate build matrix from package YAML configs, excluding existing wheels."""
import argparse
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional

import yaml

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # Python < 3.11 fallback


PHANTOM_COMBOS = {
    ("124", "2.5", "313", "windows"),
    ("129", "2.10", "310", "windows"),
    ("129", "2.10", "311", "windows"),
    ("129", "2.10", "312", "windows"),
    ("129", "2.10", "313", "windows"),
    ("129", "2.10", "314", "windows"),
}


def fetch_package_info(repo: str, tag: str, subdir: str = "") -> tuple[Optional[str], Optional[str]]:
    ref = tag or "main"
    base = f"https://raw.githubusercontent.com/{repo}/{ref}"
    if subdir:
        base = f"{base}/{subdir}"

    name, version = None, None

    try:
        with urllib.request.urlopen(f"{base}/pyproject.toml", timeout=10) as r:
            data = tomllib.loads(r.read().decode())
            project = data.get("project", {})
            name = project.get("name", "").replace("-", "_") or None
            version = project.get("version")
    except Exception:
        pass

    if not version:
        try:
            with urllib.request.urlopen(f"{base}/version.txt", timeout=10) as r:
                version = r.read().decode().strip() or None
        except Exception:
            pass

    return name, version


def get_default_arch_list(cuda_version: str, pytorch_version: str) -> str:
    cuda_major, cuda_minor = map(int, cuda_version.split(".")[:2])
    pytorch_major, pytorch_minor = map(int, pytorch_version.split(".")[:2])

    if cuda_major >= 13:
        archs = ["8.0", "9.0"]
    else:
        archs = ["7.0", "8.0", "9.0"]

    pytorch_supports_blackwell = (pytorch_major, pytorch_minor) >= (2, 6)

    if pytorch_supports_blackwell:
        if (cuda_major, cuda_minor) >= (12, 8):
            archs.append("10.0")
        if (cuda_major, cuda_minor) >= (12, 8):
            archs.append("12.0")

    return " ".join(archs)


def get_existing_wheels(package_name: str) -> set:
    try:
        result = subprocess.run(
            ["gh", "release", "view", f"{package_name}-latest", "--json", "assets", "-q", ".assets[].name"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return set(result.stdout.strip().split("\n"))
    except Exception:
        pass
    return set()


def wheel_exists(existing_wheels: set, package: str, cuda_short: str, torch_short: str, python_short: str, platform: str) -> bool:
    torch_short_v1 = torch_short.replace(".", "")
    patterns = [
        f"+cu{cuda_short}torch{torch_short}-cp{python_short}-cp{python_short}-",
        f"+cu{cuda_short}torch{torch_short_v1}-cp{python_short}-cp{python_short}-",
    ]
    if platform == "linux":
        return any(p in w and ("manylinux" in w or "linux_x86_64" in w) for p in patterns for w in existing_wheels)
    return any(p in w and "win_amd64" in w for p in patterns for w in existing_wheels)


def generate_matrix(package_filter: str, overwrite: bool = False, platform_filter: str = "all", cuda_filter: str = "all") -> list:
    packages_dir = Path(__file__).parent.parent / "packages"
    matrix = []
    skipped = 0

    for pkg_file in packages_dir.glob("*.yml"):
        pkg = yaml.safe_load(pkg_file.read_text())

        if package_filter != "all" and pkg["name"] != package_filter:
            continue

        _, detected_version = fetch_package_info(pkg["source_repo"], pkg.get("source_tag", ""), pkg.get("build_subdir", ""))
        pkg_name = pkg["name"].replace("-", "_")
        pkg_version = detected_version or pkg.get("version", "")

        existing_wheels = set()
        if not overwrite:
            wheel_pkg_name = pkg["name"].replace("-", "_")
            existing_wheels = get_existing_wheels(wheel_pkg_name)

        build = pkg["build_matrix"]

        if "combinations" in build:
            combos = []
            for c in build["combinations"]:
                python_vers = c.get("python_versions", build.get("python_versions", []))
                combo_arch_list = c.get("arch_list")
                combos.append((c["cuda"], c["pytorch"], python_vers, combo_arch_list))
        else:
            python_vers = build["python_versions"]
            combos = [(cuda, pytorch, python_vers, None) for cuda in build["cuda_versions"] for pytorch in build["pytorch_versions"]]

        for cuda, pytorch, python_versions, combo_arch_list in combos:
            if cuda_filter != "all" and cuda != cuda_filter:
                continue

            cuda_short = cuda.replace(".", "")
            torch_short = ".".join(pytorch.split(".")[:2])

            for python_ver in python_versions:
                python_short = python_ver.replace(".", "")

                for platform in build["platforms"]:
                    if platform_filter != "all" and platform != platform_filter:
                        continue
                    if (cuda_short, torch_short, python_short, platform) in PHANTOM_COMBOS:
                        continue
                    if wheel_exists(existing_wheels, pkg["name"], cuda_short, torch_short, python_short, platform):
                        skipped += 1
                        continue

                    matrix.append({
                        "package": pkg_name,
                        "version": pkg_version,
                        "source_repo": pkg["source_repo"],
                        "source_tag": pkg.get("source_tag", ""),
                        "cuda": cuda,
                        "cuda_short": cuda_short,
                        "pytorch": pytorch,
                        "python": python_ver,
                        "platform": platform,
                        "arch_list": combo_arch_list or pkg.get("arch_list") or get_default_arch_list(cuda, pytorch),
                        "extra_deps": pkg.get("extra_deps", ""),
                        "pre_build_script": pkg.get("pre_build_script", ""),
                        "free_disk_space": pkg.get("free_disk_space", False),
                        "max_jobs": pkg.get("max_jobs", 1),
                        "clone_recursive": pkg.get("clone_recursive", False),
                        "patch_script": pkg.get("patch_script", ""),
                        "build_subdir": pkg.get("build_subdir", ""),
                        "cuda_installer": pkg.get("cuda_installer", "network"),
                        "extra_cuda_components": pkg.get("extra_cuda_components", ""),
                    })

    if skipped > 0:
        print(f"Skipped {skipped} existing wheels")

    return matrix


def main():
    parser = argparse.ArgumentParser(description="Generate build matrix from package configs")
    parser.add_argument("--package", default="all", help="Package to build (or 'all')")
    parser.add_argument("--output", default="matrix.json", help="Output file path")
    parser.add_argument("--overwrite", action="store_true", help="Ignore existing wheels and rebuild all")
    parser.add_argument("--platform", default="all", help="Platform filter: all, linux, windows")
    parser.add_argument("--cuda", default="all", help="CUDA version filter: all, 12.4, 12.6, 12.8, 13.0")
    args = parser.parse_args()

    matrix = generate_matrix(args.package, overwrite=args.overwrite, platform_filter=args.platform, cuda_filter=args.cuda)

    linux_jobs = [j for j in matrix if j["platform"] == "linux"]
    windows_jobs = [j for j in matrix if j["platform"] == "windows"]

    output = {
        "linux": {"include": linux_jobs},
        "windows": {"include": windows_jobs},
    }

    with open(args.output, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    print(f"Generated {len(matrix)} build jobs ({len(linux_jobs)} Linux, {len(windows_jobs)} Windows)")

    for job in matrix:
        print(f"  - {job['package']} py{job['python']} cu{job['cuda_short']} {job['platform']}")


if __name__ == "__main__":
    main()
