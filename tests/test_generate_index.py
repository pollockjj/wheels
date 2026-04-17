import json

from scripts import generate_index


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_get_releases_uses_github_api(monkeypatch) -> None:
    payload = [{"tag_name": "demo"}]
    monkeypatch.setattr(generate_index.urllib.request, "urlopen", lambda request: _Response(payload))

    releases = generate_index.get_releases("Example-Owner/wheels", token="abc123")

    assert releases == payload


def test_v2_torch_name_regex_converts_display_name() -> None:
    converted = generate_index._V2_TORCH_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}",
        "flash_attn-2.8.3+cu128torch2.9-cp312-cp312-manylinux_2_35_x86_64.whl",
    )

    assert converted == "flash_attn-2.8.3+cu128torch29-cp312-cp312-manylinux_2_35_x86_64.whl"


def test_main_uses_repository_context(monkeypatch, tmp_path) -> None:
    seen: dict[str, str | None] = {"repo": None}

    def fake_get_releases(repo: str, token: str = None) -> list:
        seen["repo"] = repo
        return []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_REPOSITORY", "Example-Owner/wheels")
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(generate_index, "get_releases", fake_get_releases)

    generate_index.main()

    assert seen["repo"] == "Example-Owner/wheels"
