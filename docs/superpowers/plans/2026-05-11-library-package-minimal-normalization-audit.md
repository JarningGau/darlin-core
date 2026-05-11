# Library Package Minimal Normalization Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the most obvious non-library artifacts and boundary mismatches from `darlinpy` without expanding into release-engineering or broad refactoring work.

**Architecture:** Keep the package layout and build mechanism intact, but tighten the library contract in four passes: source-tree hygiene, explicit runtime output boundaries, formal-test surface normalization, and packaging/documentation alignment. Each pass adds or tightens a focused regression test before changing code or repository layout, so the work remains small, reviewable, and reversible.

**Tech Stack:** Python, pytest, setuptools, pybind11, tox, pixi, Git

---

## File Structure Map

- Modify: `.gitignore`
  Responsibility: ignore local cache files, compiled artifacts, and new auxiliary output locations.
- Modify: `darlinpy/api.py`
  Responsibility: make analysis summary formatting explicit and keep default library execution silent.
- Modify: `darlinpy/alignment/carlin_aligner.py`
  Responsibility: keep sanitization diagnostics out of stdout unless explicitly requested.
- Modify: `tests/test_api.py`
  Responsibility: lock the public `AnalysisResult` output contract and default quiet behavior.
- Modify: `tests/test_packaging_metadata.py`
  Responsibility: codify repository-hygiene, test-surface, packaging-boundary, and docs-boundary expectations.
- Modify: `tests/test_config.py`
  Responsibility: remain a maintained pytest module without path bootstrapping, script wrappers, or debug prints.
- Modify: `tests/test_integration.py`
  Responsibility: remain a maintained pytest module without script-style entrypoint residue.
- Modify: `tests/test_sanitization.py`
  Responsibility: remain a maintained pytest module without path bootstrapping, script wrappers, or debug prints.
- Move: `tests/benchmark_cas9_align.py` -> `benchmarks/benchmark_cas9_align.py`
  Responsibility: keep benchmark code available without presenting it as part of the maintained test surface.
- Move: `tests/annotate_CA.py` -> `scripts/annotate_ca_matlab_compare.py`
  Responsibility: keep the MATLAB comparison helper available as a maintainer script rather than a test artifact.
- Modify: `README.md`
  Responsibility: describe supported library usage and mark auxiliary directories as maintainer/internal only.
- Modify: `DEVELOPERS.md`
  Responsibility: document the formal verification entry points and the status of `benchmarks/` and `scripts/`.
- Modify: `setup.py`
  Responsibility: stay a minimal extension-build hook only, with no duplicated metadata.
- Delete from version control: `darlinpy/alignment/_cas9_align.cpython-310-x86_64-linux-gnu.so`
- Delete from version control: `darlinpy/__pycache__/...`
- Delete from version control: `tests/__pycache__/...`

### Task 1: Remove Tracked Build Residue and Lock Hygiene Expectations

**Files:**
- Modify: `.gitignore`
- Modify: `tests/test_packaging_metadata.py`
- Delete: `darlinpy/alignment/_cas9_align.cpython-310-x86_64-linux-gnu.so`
- Delete: `darlinpy/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/__pycache__/__init__.cpython-39.pyc`
- Delete: `darlinpy/__pycache__/api.cpython-310.pyc`
- Delete: `darlinpy/__pycache__/api.cpython-39.pyc`
- Delete: `darlinpy/alignment/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/alignment/__pycache__/__init__.cpython-39.pyc`
- Delete: `darlinpy/alignment/__pycache__/aligned_seq.cpython-310.pyc`
- Delete: `darlinpy/alignment/__pycache__/aligned_seq.cpython-39.pyc`
- Delete: `darlinpy/alignment/__pycache__/carlin_aligner.cpython-310.pyc`
- Delete: `darlinpy/alignment/__pycache__/carlin_aligner.cpython-39.pyc`
- Delete: `darlinpy/alignment/__pycache__/cas9_align.cpython-310.pyc`
- Delete: `darlinpy/alignment/__pycache__/cas9_align.cpython-39.pyc`
- Delete: `darlinpy/calling/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/calling/__pycache__/allele_caller.cpython-310.pyc`
- Delete: `darlinpy/calling/__pycache__/allele_data.cpython-310.pyc`
- Delete: `darlinpy/config/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/config/__pycache__/__init__.cpython-39.pyc`
- Delete: `darlinpy/config/__pycache__/amplicon_configs.cpython-310.pyc`
- Delete: `darlinpy/config/__pycache__/amplicon_configs.cpython-39.pyc`
- Delete: `darlinpy/config/__pycache__/scoring_matrices.cpython-310.pyc`
- Delete: `darlinpy/config/__pycache__/scoring_matrices.cpython-39.pyc`
- Delete: `darlinpy/mutations/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/mutations/__pycache__/__init__.cpython-39.pyc`
- Delete: `darlinpy/mutations/__pycache__/mutation.cpython-310.pyc`
- Delete: `darlinpy/mutations/__pycache__/mutation.cpython-39.pyc`
- Delete: `darlinpy/utils/__pycache__/__init__.cpython-310.pyc`
- Delete: `darlinpy/utils/__pycache__/__init__.cpython-39.pyc`
- Delete: `darlinpy/utils/__pycache__/build_config.cpython-310.pyc`
- Delete: `darlinpy/utils/__pycache__/build_config.cpython-39.pyc`
- Delete: `darlinpy/utils/__pycache__/misc.cpython-310.pyc`
- Delete: `darlinpy/utils/__pycache__/misc.cpython-39.pyc`
- Delete: `tests/__pycache__/__init__.cpython-310.pyc`
- Delete: `tests/__pycache__/test_allele_calling.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_api.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_cas9_align.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_config.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_integration.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_mutations.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_packaging_metadata.cpython-310-pytest-9.0.3.pyc`
- Delete: `tests/__pycache__/test_sanitization.cpython-310-pytest-9.0.3.pyc`
- Test: `tests/test_packaging_metadata.py`

- [ ] **Step 1: Write the failing hygiene regression test**

```python
def test_source_tree_excludes_local_build_residue():
    unexpected_paths = [
        Path("darlinpy/alignment/_cas9_align.cpython-310-x86_64-linux-gnu.so"),
        Path("darlinpy/__pycache__"),
        Path("tests/__pycache__"),
    ]

    for path in unexpected_paths:
        assert not path.exists(), f"{path} should not exist in the maintained source tree"
```

- [ ] **Step 2: Run the focused packaging test to verify failure**

Run: `python -m pytest tests/test_packaging_metadata.py::test_source_tree_excludes_local_build_residue -q`

Expected: FAIL because the tracked `.so` and cache directories still exist.

- [ ] **Step 3: Remove tracked residue and tighten ignore rules**

```gitignore
# Python artifacts
__pycache__/
*.py[cod]
*.so

# Auxiliary outputs
benchmarks/*.tsv
temp/
```

```bash
git rm -r darlinpy/__pycache__ darlinpy/alignment/__pycache__ darlinpy/calling/__pycache__ darlinpy/config/__pycache__ darlinpy/mutations/__pycache__ darlinpy/utils/__pycache__ tests/__pycache__
git rm darlinpy/alignment/_cas9_align.cpython-310-x86_64-linux-gnu.so
```

- [ ] **Step 4: Run the focused packaging test to verify it passes**

Run: `python -m pytest tests/test_packaging_metadata.py::test_source_tree_excludes_local_build_residue -q`

Expected: PASS.

- [ ] **Step 5: Commit the hygiene cleanup**

```bash
git add .gitignore tests/test_packaging_metadata.py
git add -u darlinpy tests
git commit -m "chore: remove tracked build residue"
```

### Task 2: Make the Library Output Boundary Explicit

**Files:**
- Modify: `darlinpy/api.py`
- Modify: `darlinpy/alignment/carlin_aligner.py`
- Modify: `tests/test_api.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write failing tests for explicit summary formatting and quiet sanitization fallback**

```python
def test_analysis_result_format_summary_returns_text_without_printing(capsys):
    result = AnalysisResult(
        mutations=[],
        alignment_scores=[85.5],
        summary_stats={},
        config_used="Col1a1",
    )

    summary = result.format_summary()
    captured = capsys.readouterr()

    assert "CARLIN Sequence Analysis Results Summary" in summary
    assert "Configuration: Col1a1" in summary
    assert captured.out == ""


def test_align_sequence_sanitization_failure_is_quiet_by_default(monkeypatch, capsys):
    from darlinpy.alignment import create_default_aligner

    aligner = create_default_aligner()

    def explode(_aligned_seq):
        raise ValueError("synthetic sanitization failure")

    monkeypatch.setattr(aligner, "_perform_sanitization", explode)
    result = aligner.align_sequence(aligner.reference_sequence, verbose=False, sanitize=True)
    captured = capsys.readouterr()

    assert captured.out == ""
    assert result["sanitized"] is False
```

- [ ] **Step 2: Run the focused API tests to verify failure**

Run: `python -m pytest tests/test_api.py::TestAnalysisResult::test_analysis_result_format_summary_returns_text_without_printing tests/test_api.py::TestAnalyzeSequences::test_align_sequence_sanitization_failure_is_quiet_by_default -q`

Expected: FAIL because `AnalysisResult.format_summary()` does not exist yet, and the new quiet-fallback test has not been added to the current class structure.

- [ ] **Step 3: Implement explicit summary formatting and keep diagnostics out of stdout**

```python
@dataclass
class AnalysisResult:
    ...
    def format_summary(self) -> str:
        lines = [
            "CARLIN Sequence Analysis Results Summary",
            "=" * 40,
            f"Configuration: {self.config_used}",
            f"Processing time: {self.processing_time:.2f} seconds",
            "",
            "Sequence statistics:",
            f"  Total sequences: {self.num_sequences}",
            f"  Average alignment score: {self.average_alignment_score:.2f}",
            "",
            "Mutation statistics:",
            f"  Total mutations: {self.total_mutations}",
        ]
        for mut_type, count in self.get_mutation_summary().items():
            lines.append(f"  {mut_type} type: {count}")
        return "\n".join(lines)

    def print_summary(self) -> None:
        print(self.format_summary())
```

```python
except Exception as e:
    if verbose:
        logger.warning(
            "Sequence normalization failed; continuing with original alignment results: %s",
            e,
        )
```

- [ ] **Step 4: Run the focused API tests to verify they pass**

Run: `python -m pytest tests/test_api.py::TestAnalysisResult::test_analysis_result_format_summary_returns_text_without_printing tests/test_api.py::TestAnalyzeSequences::test_align_sequence_sanitization_failure_is_quiet_by_default -q`

Expected: PASS.

- [ ] **Step 5: Commit the output-boundary change**

```bash
git add darlinpy/api.py darlinpy/alignment/carlin_aligner.py tests/test_api.py
git commit -m "refactor: make library output explicit"
```

### Task 3: Separate Formal Tests from Benchmarks and Manual Scripts

**Files:**
- Modify: `tests/test_packaging_metadata.py`
- Modify: `tests/test_config.py`
- Modify: `tests/test_integration.py`
- Modify: `tests/test_sanitization.py`
- Create: `benchmarks/benchmark_cas9_align.py`
- Create: `scripts/annotate_ca_matlab_compare.py`
- Delete: `tests/benchmark_cas9_align.py`
- Delete: `tests/annotate_CA.py`
- Test: `tests/test_packaging_metadata.py`
- Test: `tests/test_config.py`
- Test: `tests/test_integration.py`
- Test: `tests/test_sanitization.py`

- [ ] **Step 1: Write failing repository-shape tests for auxiliary files and maintained pytest modules**

```python
def test_auxiliary_tools_are_outside_the_formal_test_surface():
    assert not Path("tests/benchmark_cas9_align.py").exists()
    assert not Path("tests/annotate_CA.py").exists()
    assert Path("benchmarks/benchmark_cas9_align.py").exists()
    assert Path("scripts/annotate_ca_matlab_compare.py").exists()


def test_maintained_tests_do_not_use_script_bootstrapping():
    for path in [
        Path("tests/test_cas9_align.py"),
        Path("tests/test_config.py"),
        Path("tests/test_integration.py"),
        Path("tests/test_sanitization.py"),
    ]:
        content = path.read_text(encoding="utf-8")
        assert "sys.path.insert" not in content
        assert 'if __name__ == "__main__":' not in content
```

- [ ] **Step 2: Run the focused packaging test to verify failure**

Run: `python -m pytest tests/test_packaging_metadata.py::test_auxiliary_tools_are_outside_the_formal_test_surface tests/test_packaging_metadata.py::test_maintained_tests_do_not_use_script_bootstrapping -q`

Expected: FAIL because benchmark and helper scripts still live under `tests/`, and several maintained test modules still contain path bootstrapping or `__main__` wrappers.

- [ ] **Step 3: Move auxiliary files and clean maintained pytest modules**

```python
from darlinpy.config import (
    AmpliconConfig,
    ScoringConfig,
    get_default_scoring_config,
    get_original_carlin_config,
)
```

```python
# Delete from maintained pytest modules:
# - shebang lines
# - sys.path.insert(...) bootstrapping
# - print(...) debug output
# - if __name__ == "__main__": wrappers
```

```bash
mkdir -p benchmarks scripts
mv tests/benchmark_cas9_align.py benchmarks/benchmark_cas9_align.py
mv tests/annotate_CA.py scripts/annotate_ca_matlab_compare.py
```

- [ ] **Step 4: Run the maintained test subset to verify the reshaped surface still works**

Run: `python -m pytest tests/test_packaging_metadata.py tests/test_config.py tests/test_integration.py tests/test_sanitization.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the test-surface normalization**

```bash
git add tests/test_packaging_metadata.py tests/test_config.py tests/test_integration.py tests/test_sanitization.py benchmarks/benchmark_cas9_align.py scripts/annotate_ca_matlab_compare.py
git add -u tests
git commit -m "test: separate formal tests from auxiliary tools"
```

### Task 4: Lock Packaging and Documentation Boundaries to the Library-Only Model

**Files:**
- Modify: `tests/test_packaging_metadata.py`
- Modify: `README.md`
- Modify: `DEVELOPERS.md`
- Modify: `setup.py`
- Test: `tests/test_packaging_metadata.py`

- [ ] **Step 1: Write failing tests for setup.py minimalism and docs boundary clarity**

```python
def test_setup_py_remains_an_extension_only_build_hook():
    setup_py = Path("setup.py").read_text(encoding="utf-8")

    assert "Pybind11Extension" in setup_py
    assert "version=" not in setup_py
    assert "install_requires" not in setup_py
    assert "python_requires" not in setup_py


def test_developer_docs_describe_auxiliary_directories():
    readme = Path("README.md").read_text(encoding="utf-8")
    developers = Path("DEVELOPERS.md").read_text(encoding="utf-8")

    assert "benchmarks/" in readme
    assert "scripts/" in readme
    assert "benchmarks/" in developers
    assert "scripts/" in developers
```

- [ ] **Step 2: Run the focused packaging test to verify failure**

Run: `python -m pytest tests/test_packaging_metadata.py::test_setup_py_remains_an_extension_only_build_hook tests/test_packaging_metadata.py::test_developer_docs_describe_auxiliary_directories -q`

Expected: FAIL because the docs do not yet describe the new auxiliary directories and their maintainer/internal status.

- [ ] **Step 3: Update docs and keep setup.py intentionally minimal**

```python
setup(
    ext_modules=[
        Pybind11Extension(
            "darlinpy.alignment._cas9_align",
            ["darlinpy/alignment/_cas9_align.cpp"],
            cxx_std=17,
        )
    ],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
```

```markdown
## Repository Layout

- `darlinpy/`: supported library package
- `tests/`: maintained pytest coverage for the supported library contract
- `benchmarks/`: maintainer-only performance experiments, not part of default verification
- `scripts/`: maintainer-only helper scripts, not supported user interfaces
```

- [ ] **Step 4: Run the packaging/doc checks plus the maintained quality path**

Run: `python -m pytest tests/test_packaging_metadata.py -q`

Expected: PASS.

Run: `python -m pytest tests/test_api.py tests/test_config.py tests/test_cas9_align.py tests/test_integration.py tests/test_mutations.py tests/test_sanitization.py tests/test_packaging_metadata.py -q`

Expected: PASS.

Run: `python -m pip install -e .`

Expected: PASS, with the extension rebuilt from source rather than loaded from a tracked binary.

- [ ] **Step 5: Commit the packaging and docs boundary updates**

```bash
git add README.md DEVELOPERS.md setup.py tests/test_packaging_metadata.py
git commit -m "docs: align library-only package boundaries"
```

### Task 5: Final Verification and Hand-off

**Files:**
- Reuse: `.gitignore`
- Reuse: `darlinpy/api.py`
- Reuse: `darlinpy/alignment/carlin_aligner.py`
- Reuse: `tests/test_api.py`
- Reuse: `tests/test_packaging_metadata.py`
- Reuse: `tests/test_config.py`
- Reuse: `tests/test_integration.py`
- Reuse: `tests/test_sanitization.py`
- Reuse: `README.md`
- Reuse: `DEVELOPERS.md`

- [ ] **Step 1: Rebuild the extension from source in a clean working state**

Run: `python -m pip install -e .`

Expected: PASS, with setuptools rebuilding `darlinpy.alignment._cas9_align` from `darlinpy/alignment/_cas9_align.cpp`.

- [ ] **Step 2: Run the maintained pytest suite**

Run: `python -m pytest tests/test_api.py tests/test_config.py tests/test_cas9_align.py tests/test_integration.py tests/test_mutations.py tests/test_sanitization.py tests/test_packaging_metadata.py -q`

Expected: PASS.

- [ ] **Step 3: Run the documented quality path**

Run: `pixi run quality`

Expected: PASS.

- [ ] **Step 4: Inspect the final diff against the spec boundary**

Run: `git diff --stat HEAD~4..HEAD`

Expected: only the files named in this plan are changed, with no unrelated refactor drift.

- [ ] **Step 5: Commit any final doc or verification-only adjustments**

```bash
git add README.md DEVELOPERS.md tests/test_packaging_metadata.py
git commit -m "chore: finalize minimal library normalization audit"
```

## Self-Review

- Spec coverage:
  - Source tree hygiene: Task 1.
  - Runtime output behavior: Task 2.
  - Formal tests vs. auxiliary tools: Task 3.
  - Packaging entry-point and metadata clarity: Task 4.
  - Documentation/support-boundary alignment: Task 4 and Task 5.
- Placeholder scan:
  - No `TBD`, `TODO`, or deferred “write tests later” placeholders remain.
  - Each task names exact files, commands, and expected outcomes.
- Type and naming consistency:
  - `AnalysisResult.format_summary()` is introduced before later tasks refer to it.
  - Auxiliary directories are consistently named `benchmarks/` and `scripts/`.
  - The maintained verification file is consistently `tests/test_packaging_metadata.py`.
