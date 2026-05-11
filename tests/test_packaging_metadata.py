from pathlib import Path


def test_distribution_metadata_uses_darlin_core_identity():
    pyproject = Path("pyproject.toml").read_text()

    assert 'name = "darlin-core"' in pyproject
    assert 'Homepage = "https://github.com/jarninggau/darlin-core"' in pyproject
    assert 'Repository = "https://github.com/jarninggau/darlin-core"' in pyproject


def test_setuptools_uses_src_layout_for_package_discovery():
    pyproject = Path("pyproject.toml").read_text()

    assert 'where = ["src"]' in pyproject
    assert 'include = ["darlin_core", "darlin_core.*"]' in pyproject
    assert '"darlin_core.config" = ["data/*.json"]' in pyproject


def test_extension_build_targets_renamed_package():
    setup_py = Path("setup.py").read_text()

    assert '"darlin_core.alignment._cas9_align"' in setup_py
    assert '"src/darlin_core/alignment/_cas9_align.cpp"' in setup_py


def test_repository_uses_src_package_root_only():
    assert Path("src/darlin_core").is_dir()
    assert not Path("darlinpy").exists()
