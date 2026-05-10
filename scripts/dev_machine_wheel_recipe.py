#!/usr/bin/env python3
"""Resolve exact development-machine wheel recipes for GitHub Actions."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
RECIPES_PATH = ROOT / "recipes" / "dev_machine_wheels.json"
PLATFORM_TAG = "manylinux_2_35_x86_64"


def load_recipes() -> dict[str, dict[str, str]]:
    data = json.loads(RECIPES_PATH.read_text())
    recipes = {}
    for recipe in data["recipes"]:
        recipe = {key: str(value) for key, value in recipe.items()}
        recipe["expected_wheel"] = expected_wheel(recipe)
        recipe["wheel_prefix"] = wheel_prefix(recipe)
        recipe["artifact_name"] = artifact_name(recipe)
        recipes[recipe["id"]] = recipe
    return recipes


def wheel_prefix(recipe: dict[str, str]) -> str:
    return (
        f"{recipe['package']}-{recipe['version']}"
        f"+cu{recipe['cuda_short']}torch{recipe['torch_short']}"
        f"-{recipe['python_tag']}-{recipe['abi_tag']}-"
    )


def expected_wheel(recipe: dict[str, str]) -> str:
    return f"{wheel_prefix(recipe)}{PLATFORM_TAG}.whl"


def artifact_name(recipe: dict[str, str]) -> str:
    return (
        f"{recipe['id']}"
        f"-py{recipe['python'].replace('.', '')}"
        f"-cu{recipe['cuda_short']}"
        f"-torch{recipe['pytorch']}"
    )


def get_recipe(recipe_id: str) -> dict[str, str]:
    recipes = load_recipes()
    try:
        return recipes[recipe_id]
    except KeyError:
        valid = ", ".join(sorted(recipes))
        raise SystemExit(f"Unknown recipe '{recipe_id}'. Valid recipes: {valid}")


def write_outputs(values: dict[str, Any]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def github_api(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pollockjj-wheels-exact-recipe",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def matching_wheel(name: str, recipe: dict[str, str]) -> bool:
    old_torch_prefix = recipe["wheel_prefix"].replace(
        f"torch{recipe['torch_short']}",
        f"torch{recipe['torch_short'].replace('.', '')}",
    )
    if not name.endswith(".whl"):
        return False
    if not (name.startswith(recipe["wheel_prefix"]) or name.startswith(old_torch_prefix)):
        return False
    return "manylinux" in name or "linux_x86_64" in name


def find_asset(repo: str, package: str, recipe: dict[str, str]) -> dict[str, Any] | None:
    tag = f"{package}-latest"
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    try:
        release = github_api(url)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    for asset in release.get("assets", []):
        if matching_wheel(asset.get("name", ""), recipe):
            return asset
    return None


def download(url: str, destination: Path) -> None:
    headers = {"User-Agent": "pollockjj-wheels-exact-recipe"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def command_list(_: argparse.Namespace) -> None:
    for recipe_id in load_recipes():
        print(recipe_id)


def command_emit(args: argparse.Namespace) -> None:
    recipe = get_recipe(args.recipe)
    write_outputs(recipe)
    print(json.dumps(recipe, indent=2, sort_keys=True))


def command_obtain(args: argparse.Namespace) -> None:
    recipe = get_recipe(args.recipe)
    dist = Path(args.dist)
    dist.mkdir(parents=True, exist_ok=True)

    origin_asset = find_asset(args.origin, recipe["package"], recipe)
    if origin_asset:
        result = {
            "mode": "origin_exists",
            "source_repo": args.origin,
            "source_url": origin_asset["browser_download_url"],
            "wheel_path": "",
        }
        write_outputs(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    upstream_asset = find_asset(args.upstream, recipe["package"], recipe)
    if upstream_asset:
        wheel_path = dist / upstream_asset["name"]
        download(upstream_asset["browser_download_url"], wheel_path)
        result = {
            "mode": "stolen",
            "source_repo": args.upstream,
            "source_url": upstream_asset["browser_download_url"],
            "wheel_path": str(wheel_path),
        }
        write_outputs(result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    result = {
        "mode": "build",
        "source_repo": "",
        "source_url": "",
        "wheel_path": "",
    }
    write_outputs(result)
    print(json.dumps(result, indent=2, sort_keys=True))


def command_verify_dist(args: argparse.Namespace) -> None:
    recipe = get_recipe(args.recipe)
    found = sorted(path for path in Path(args.dist).glob("*.whl"))
    matches = [path for path in found if matching_wheel(path.name, recipe)]
    if not matches:
        found_names = [path.name for path in found]
        raise SystemExit(
            f"Expected wheel prefix not found: {recipe['wheel_prefix']}\n"
            f"Found wheels: {json.dumps(found_names)}"
        )
    print(matches[0])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=command_list)

    emit_parser = subparsers.add_parser("emit")
    emit_parser.add_argument("--recipe", required=True)
    emit_parser.set_defaults(func=command_emit)

    obtain_parser = subparsers.add_parser("obtain")
    obtain_parser.add_argument("--recipe", required=True)
    obtain_parser.add_argument("--origin", default="pollockjj/wheels")
    obtain_parser.add_argument("--upstream", default="Comfy-Org/wheels")
    obtain_parser.add_argument("--dist", default="dist")
    obtain_parser.set_defaults(func=command_obtain)

    verify_parser = subparsers.add_parser("verify-dist")
    verify_parser.add_argument("--recipe", required=True)
    verify_parser.add_argument("--dist", default="dist")
    verify_parser.set_defaults(func=command_verify_dist)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
