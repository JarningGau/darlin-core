from pathlib import Path


def test_pyproject_contains_project_metadata_sections():
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "[project]" in pyproject
    assert 'name = "darlinpy"' in pyproject
    assert 'requires-python = ">=3.8"' in pyproject
    assert 'license = { text = "MIT" }' in pyproject
    assert "[project.optional-dependencies]" in pyproject
    assert "[tool.setuptools]" in pyproject
    assert 'license-files = ["LICENSE"]' in pyproject


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
    assert 'python -m pip install --no-build-isolation -e .' in pixi
    assert 'quality' in pixi
    assert 'ruff check darlinpy/__init__.py darlinpy/api.py darlinpy/alignment/carlin_aligner.py tests/test_api.py tests/test_packaging_metadata.py tests/test_cas9_align.py tests/test_integration.py' in pixi
    assert 'python -m pytest -q' in pixi


def test_quality_workflow_exists():
    workflow = Path(".github/workflows/quality.yml").read_text(encoding="utf-8")

    assert "name: quality" in workflow
    assert "pixi run quality" in workflow


def test_readme_describes_library_only_usage():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "library-only" in readme.lower()
    assert "legacy/internal" in readme
    assert "bin/" in readme


def test_developers_doc_mentions_quality_and_verification():
    developers = Path("DEVELOPERS.md").read_text(encoding="utf-8")
    assert "pixi run quality" in developers
    assert "conda run -n darlinpy-test python -m pytest -q" in developers
