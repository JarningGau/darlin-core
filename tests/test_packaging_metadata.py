from pathlib import Path


def test_pyproject_contains_project_metadata_sections():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "[project]" in pyproject
    assert 'name = "darlinpy"' in pyproject
    assert 'requires-python = ">=3.8"' in pyproject
    assert "[project.optional-dependencies]" in pyproject
