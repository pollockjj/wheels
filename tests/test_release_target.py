import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import release_target


def test_build_release_target_renders_expected_index_url() -> None:
    target = release_target.build_release_target("Example-Owner/wheels")

    assert target == {
        "release_repo": "Example-Owner/wheels",
        "index_url": "https://example-owner.github.io/wheels",
    }


def test_release_target_cli_json_output(tmp_path) -> None:
    script = Path(__file__).resolve().parent.parent / "scripts" / "release_target.py"

    result = subprocess.run(
        [sys.executable, str(script), "--repo", "Example-Owner/wheels", "--format", "json"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "release_repo": "Example-Owner/wheels",
        "index_url": "https://example-owner.github.io/wheels",
    }


def test_release_target_missing_repository_context(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)

    with pytest.raises(ValueError, match="GITHUB_REPOSITORY"):
        release_target.resolve_release_repo()
