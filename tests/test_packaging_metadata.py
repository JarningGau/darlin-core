from pathlib import Path


def test_pyproject_contains_project_metadata_sections():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "[project]" in pyproject
    assert 'name = "darlinpy"' in pyproject
    assert 'requires-python = ">=3.8"' in pyproject
    assert "[project.optional-dependencies]" in pyproject


def test_script_style_test_bootstrapping_is_removed():
    for path in [
        Path("tests/test_cas9_align.py"),
        Path("tests/test_integration.py"),
    ]:
        content = path.read_text(encoding="utf-8")
        assert "sys.path.insert" not in content
        assert 'if __name__ == "__main__":' not in content


def test_pixi_quality_config_exists():
    pixi = Path("pixi.toml").read_text(encoding="utf-8")

    assert '[tasks]' in pixi
    assert 'quality' in pixi
    assert 'ruff check darlinpy/__init__.py darlinpy/api.py darlinpy/alignment/carlin_aligner.py tests/test_api.py tests/test_packaging_metadata.py tests/test_cas9_align.py tests/test_integration.py' in pixi
    assert 'python -m pytest -q' in pixi
