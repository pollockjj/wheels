import csv
import tempfile
import zipfile
from pathlib import Path

from scripts import patch_wheel_version


def _workspace_dir() -> Path:
    root = Path(__file__).resolve().parent / "_tmp"
    root.mkdir(exist_ok=True)
    return root


def _build_sample_wheel(base_dir: Path, filename: str) -> Path:
    wheel_path = base_dir / filename
    dist_info = "demo_pkg-1.2.3.dist-info"

    with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{dist_info}/METADATA", "Metadata-Version: 2.1\nName: demo_pkg\nVersion: 1.2.3\n")
        zf.writestr(f"{dist_info}/RECORD", "")
    return wheel_path


def test_extract_version_from_filename() -> None:
    assert patch_wheel_version.extract_version_from_filename(
        "sageattention-2.2.0+cu128torch2.9-cp312-cp312-linux_x86_64.whl"
    ) == ("sageattention", "2.2.0+cu128torch2.9")


def test_fix_wheel_updates_metadata_and_stays_out_of_tmp() -> None:
    with tempfile.TemporaryDirectory(dir=_workspace_dir(), prefix="wheel-test-") as tmpdir:
        base_dir = Path(tmpdir)
        wheel_path = _build_sample_wheel(
            base_dir,
            "demo_pkg-1.2.3+cu128torch2.9-cp312-cp312-linux_x86_64.whl",
        )

        modified = patch_wheel_version.fix_wheel(wheel_path)

        assert modified is True
        assert (base_dir / ".wheel-fix-tmp").exists()

        with zipfile.ZipFile(wheel_path) as zf:
            metadata = zf.read("demo_pkg-1.2.3+cu128torch2.9.dist-info/METADATA").decode("utf-8")
            record = zf.read("demo_pkg-1.2.3+cu128torch2.9.dist-info/RECORD").decode("utf-8")

        assert "Version: 1.2.3+cu128torch2.9" in metadata
        rows = list(csv.reader(record.splitlines()))
        assert rows[-1] == ["demo_pkg-1.2.3+cu128torch2.9.dist-info/RECORD", "", ""]
