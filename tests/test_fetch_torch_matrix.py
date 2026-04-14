import io

from scripts import fetch_torch_matrix


class _Response:
    def __init__(self, body: str) -> None:
        self.body = body.encode("utf-8")

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def test_fetch_torch_wheels_filters_old_and_free_threaded(monkeypatch) -> None:
    html = """
<a>torch-2.8.0+cu128-cp310-cp310-linux_x86_64.whl</a>
<a>torch-2.8.0+cu128-cp313t-cp313t-linux_x86_64.whl</a>
<a>torch-2.8.0+cu128-cp39-cp39-linux_x86_64.whl</a>
<a>torch-2.8.0+cu128-cp311-cp311-win_amd64.whl</a>
"""

    monkeypatch.setattr(fetch_torch_matrix.urllib.request, "urlopen", lambda *args, **kwargs: _Response(html))

    wheels = fetch_torch_matrix.fetch_torch_wheels("cu128")

    assert wheels == [
        {"cuda": "cu128", "torch": "2.8.0", "python": "3.10", "platform": "linux_x86_64"},
        {"cuda": "cu128", "torch": "2.8.0", "python": "3.11", "platform": "windows"},
    ]


def test_build_matrix_deduplicates_and_sorts(monkeypatch) -> None:
    sample = [
        {"cuda": "cu128", "torch": "2.8.0", "python": "3.11", "platform": "windows"},
        {"cuda": "cu128", "torch": "2.8.0", "python": "3.10", "platform": "linux_x86_64"},
        {"cuda": "cu128", "torch": "2.8.0", "python": "3.10", "platform": "linux_x86_64"},
    ]
    monkeypatch.setattr(fetch_torch_matrix, "CUDA_VERSIONS", ["cu128"])
    monkeypatch.setattr(fetch_torch_matrix, "fetch_torch_wheels", lambda cuda: list(sample))

    matrix = fetch_torch_matrix.build_matrix()

    assert matrix["total"] == 2
    assert matrix["combos"][0]["python"] == "3.10"
    assert matrix["summary"][0]["platforms"] == ["linux_x86_64", "windows"]
