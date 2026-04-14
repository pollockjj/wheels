from pathlib import Path

from scripts import generate_matrix


def test_get_default_arch_list_tracks_blackwell_rules() -> None:
    assert generate_matrix.get_default_arch_list("12.4", "2.5.0") == "7.0 8.0 9.0"
    assert generate_matrix.get_default_arch_list("12.8", "2.7.0") == "7.0 8.0 9.0 10.0 12.0"
    assert generate_matrix.get_default_arch_list("13.0", "2.9.0") == "8.0 9.0 10.0 12.0"


def test_generate_matrix_splits_windows_runner_classes(monkeypatch) -> None:
    monkeypatch.setattr(generate_matrix, "fetch_package_info", lambda *args, **kwargs: ("pkg", "9.9.9"))
    monkeypatch.setattr(generate_matrix, "get_existing_wheels", lambda *args, **kwargs: set())

    matrix = generate_matrix.generate_matrix("sageattention", overwrite=True)

    assert matrix
    assert all(job["package"] == "sageattention" for job in matrix)
    assert any(job["platform"] == "linux" for job in matrix)
    windows_jobs = [job for job in matrix if job["platform"] == "windows"]
    assert windows_jobs
    assert all(job["package"] == "sageattention" for job in windows_jobs)


def test_generate_matrix_package_filter_skips_other_specs(monkeypatch) -> None:
    monkeypatch.setattr(generate_matrix, "fetch_package_info", lambda *args, **kwargs: ("pkg", "1.0.0"))
    monkeypatch.setattr(generate_matrix, "get_existing_wheels", lambda *args, **kwargs: set())

    matrix = generate_matrix.generate_matrix("sageattn3", overwrite=True)

    assert matrix
    assert {job["package"] for job in matrix} == {"sageattn3"}
    assert all(job["arch_list"] == "10.0 12.0" for job in matrix)
