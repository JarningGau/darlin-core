# Python Compatibility Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a CI-first compatibility test system for `darlinpy` that validates reduced Python/dependency boundaries, required C++ extension availability, and a stable pytest subset, with exact local reproduction through `tox`.

**Architecture:** Define the compatibility contract once in `tox.ini`, keep minimum dependencies explicit in `requirements-min.txt`, and make GitHub Actions call named tox environments instead of re-encoding install logic. Limit the matrix to `py38-min`, `py39-max`, `py311-min`, `py311-max`, plus non-blocking `py312-max`, and keep compatibility verification separate from the full repository test suite.

**Tech Stack:** Python packaging (`setuptools`, `pyproject.toml`), `tox`, `pytest`, GitHub Actions, `pip`, `pybind11`

---

## File Map

### Create

- `.github/workflows/compatibility.yml`
  Responsibility: run the reduced compatibility matrix in GitHub Actions and map each job to one tox environment.
- `tox.ini`
  Responsibility: define the compatibility environments, dependency modes, smoke checks, and pytest command.
- `requirements-min.txt`
  Responsibility: pin the minimum runtime dependency boundary used by `*-min` tox jobs.

### Modify

- `DEVELOPERS.md`
  Responsibility: document supported versions, tox entry points, and the meaning of `min` and `max`.

### Reuse Without Modification Unless Needed

- `setup.py`
  Source of truth for `python_requires`, install requirements, and extension build.
- `pyproject.toml`
  Source of truth for build backend and build-time dependency requirements.
- `tests/test_api.py`
  Candidate compatibility coverage for public API behavior.
- `tests/test_config.py`
  Candidate compatibility coverage for config loading and scoring behavior.
- `tests/test_cas9_align.py`
  Candidate compatibility coverage for the extension-backed aligner and `HAS_CPP_IMPL`.
- `tests/test_mutations.py`
  Candidate compatibility coverage for mutation identification and formatting.
- `tests/test_integration.py`
  Candidate source for one stable end-to-end compatibility path.

## Compatibility Test Command

Use one explicit pytest command in tox rather than relying on discovery:

```bash
pytest \
  tests/test_api.py \
  tests/test_config.py \
  tests/test_cas9_align.py \
  tests/test_mutations.py \
  tests/test_integration.py::TestCARLINIntegration::test_end_to_end_perfect_sequence \
  tests/test_integration.py::TestCARLINIntegration::test_config_integration \
  -q
```

This keeps the matrix focused on stable core behavior while still covering API, config, extension-backed alignment, mutation logic, and a minimal integration path.

### Task 1: Add Minimum-Dependency Boundary File

**Files:**
- Create: `requirements-min.txt`
- Test: `python -m pip install -r requirements-min.txt`

- [ ] **Step 1: Write the file with the exact minimum runtime pins**

```text
numpy==1.20.0
scipy==1.7.0
pandas==1.3.0
```

- [ ] **Step 2: Verify the file is readable by pip**

Run: `python -m pip install -r requirements-min.txt --dry-run`
Expected: pip resolves `numpy==1.20.0`, `scipy==1.7.0`, and `pandas==1.3.0` without syntax errors in the requirements file.

- [ ] **Step 3: Commit**

```bash
git add requirements-min.txt
git commit -m "test: add minimum dependency constraints"
```

### Task 2: Add tox Environments for Compatibility Jobs

**Files:**
- Create: `tox.ini`
- Reuse: `requirements-min.txt`
- Test: `tox -l`

- [ ] **Step 1: Write a failing tox configuration skeleton**

Create `tox.ini` with this initial structure:

```ini
[tox]
envlist = py38-min, py39-max, py311-min, py311-max, py312-max
isolated_build = true

[testenv]
description = compatibility job
package = editable
deps =
    pytest
commands =
    python -c "raise SystemExit('tox commands not implemented yet')"
```

- [ ] **Step 2: Run tox to verify the skeleton fails in the expected place**

Run: `tox -e py311-max`
Expected: FAIL with `tox commands not implemented yet`, proving tox loads the environment name correctly before real commands are added.

- [ ] **Step 3: Replace the placeholder command with explicit dependency-mode installation and smoke checks**

Update `tox.ini` to:

```ini
[tox]
envlist = py38-min, py39-max, py311-min, py311-max, py312-max
isolated_build = true

[testenv]
description = darlinpy compatibility job
package = editable
deps =
    pytest
commands_pre =
    min: python -m pip install -r requirements-min.txt
    max: python -m pip install numpy scipy pandas
commands =
    python -c "import darlinpy; print(darlinpy.__version__)"
    python -c "from darlinpy.alignment.cas9_align import HAS_CPP_IMPL; assert HAS_CPP_IMPL is True"
    pytest tests/test_api.py tests/test_config.py tests/test_cas9_align.py tests/test_mutations.py tests/test_integration.py::TestCARLINIntegration::test_end_to_end_perfect_sequence tests/test_integration.py::TestCARLINIntegration::test_config_integration -q
```

- [ ] **Step 4: Run tox to verify the environment list is exposed correctly**

Run: `tox -l`
Expected:

```text
py38-min
py39-max
py311-min
py311-max
py312-max
```

- [ ] **Step 5: Run one max environment locally**

Run: `tox -e py311-max`
Expected: PASS, with the smoke check confirming `HAS_CPP_IMPL` and the compatibility pytest subset completing successfully.

- [ ] **Step 6: Run one min environment locally**

Run: `tox -e py311-min`
Expected: PASS, or a concrete dependency-compatibility failure tied to the minimum pins rather than tox configuration.

- [ ] **Step 7: Commit**

```bash
git add tox.ini requirements-min.txt
git commit -m "test: add tox compatibility environments"
```

### Task 3: Add GitHub Actions Compatibility Workflow

**Files:**
- Create: `.github/workflows/compatibility.yml`
- Reuse: `tox.ini`
- Test: `python - <<'PY'\nimport yaml, pathlib\nprint(yaml.safe_load(pathlib.Path('.github/workflows/compatibility.yml').read_text())['name'])\nPY`

- [ ] **Step 1: Write the workflow with the reduced `4+1` matrix**

Create `.github/workflows/compatibility.yml` with:

```yaml
name: compatibility

on:
  push:
    branches: [main]
  pull_request:

jobs:
  compatibility:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        include:
          - python-version: "3.8"
            toxenv: py38-min
            experimental: false
          - python-version: "3.9"
            toxenv: py39-max
            experimental: false
          - python-version: "3.11"
            toxenv: py311-min
            experimental: false
          - python-version: "3.11"
            toxenv: py311-max
            experimental: false
          - python-version: "3.12"
            toxenv: py312-max
            experimental: true
    continue-on-error: ${{ matrix.experimental }}
    name: ${{ matrix.toxenv }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install tox
        run: python -m pip install --upgrade pip tox
      - name: Run compatibility environment
        run: tox -e ${{ matrix.toxenv }}
```

- [ ] **Step 2: Validate the workflow YAML parses**

Run:

```bash
python - <<'PY'
import pathlib
import yaml
data = yaml.safe_load(pathlib.Path(".github/workflows/compatibility.yml").read_text())
assert data["name"] == "compatibility"
assert "jobs" in data
print("workflow ok")
PY
```

Expected:

```text
workflow ok
```

- [ ] **Step 3: Verify the workflow names match tox environment names**

Run:

```bash
python - <<'PY'
import pathlib
import yaml
data = yaml.safe_load(pathlib.Path(".github/workflows/compatibility.yml").read_text())
toxenvs = [item["toxenv"] for item in data["jobs"]["compatibility"]["strategy"]["matrix"]["include"]]
expected = ["py38-min", "py39-max", "py311-min", "py311-max", "py312-max"]
assert toxenvs == expected
print("matrix ok")
PY
```

Expected:

```text
matrix ok
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/compatibility.yml tox.ini
git commit -m "ci: add compatibility workflow"
```

### Task 4: Document Local Reproduction and Support Boundary

**Files:**
- Modify: `DEVELOPERS.md`
- Reuse: `tox.ini`, `.github/workflows/compatibility.yml`
- Test: `rg -n "Compatibility testing|py38-min|py311-max|py312-max" DEVELOPERS.md`

- [ ] **Step 1: Add a compatibility testing section to `DEVELOPERS.md`**

Insert content like:

```md
## Compatibility Testing

The project officially supports Python 3.8 through 3.11. Compatibility CI also runs one exploratory Python 3.12 job as non-blocking signal only.

The required compatibility jobs are:

- `py38-min`
- `py39-max`
- `py311-min`
- `py311-max`

The exploratory compatibility job is:

- `py312-max`

`min` means the pinned runtime floor from `requirements-min.txt`.
`max` means the latest versions resolved by pip at test time.

Run a local compatibility job with tox:

```bash
tox -e py38-min
tox -e py311-min
tox -e py311-max
tox -e py312-max
```
```

- [ ] **Step 2: Verify the new section is discoverable**

Run: `rg -n "Compatibility Testing|py38-min|py311-max|py312-max" DEVELOPERS.md`
Expected: output shows the new section header and the listed tox environment names.

- [ ] **Step 3: Commit**

```bash
git add DEVELOPERS.md
git commit -m "docs: add compatibility testing workflow"
```

### Task 5: Validate End-to-End Locally Before Claiming Completion

**Files:**
- Reuse: `tox.ini`, `.github/workflows/compatibility.yml`, `requirements-min.txt`, `DEVELOPERS.md`
- Test: local command results only

- [ ] **Step 1: Run all required local compatibility jobs**

Run:

```bash
tox -e py38-min
tox -e py39-max
tox -e py311-min
tox -e py311-max
```

Expected: all four required environments PASS, each showing successful editable install, `HAS_CPP_IMPL` smoke-check success, and passing compatibility pytest output.

- [ ] **Step 2: Run the exploratory local job**

Run: `tox -e py312-max`
Expected: PASS if Python 3.12 already works; otherwise fail with a concrete signal that can be tolerated in CI because the workflow marks it non-blocking.

- [ ] **Step 3: Inspect the git diff for unintended changes**

Run: `git status --short`
Expected: only `.github/workflows/compatibility.yml`, `tox.ini`, `requirements-min.txt`, and `DEVELOPERS.md` are modified or staged for this feature work.

- [ ] **Step 4: Create the final commit**

```bash
git add .github/workflows/compatibility.yml tox.ini requirements-min.txt DEVELOPERS.md
git commit -m "test: add python compatibility matrix"
```

## Self-Review

### Spec Coverage Check

- Reduced `4+1` matrix: covered by Task 2 and Task 3.
- Minimum and latest dependency boundaries: covered by Task 1 and Task 2.
- Required C++ extension smoke check: covered by Task 2 and Task 5.
- Stable compatibility pytest subset: covered by the explicit pytest command in Task 2.
- Local reproduction via tox: covered by Task 2, Task 4, and Task 5.
- Developer documentation: covered by Task 4.

### Placeholder Scan

No `TBD`, `TODO`, or deferred “write tests later” placeholders remain. Each task names exact files, commands, and expected outcomes.

### Type and Naming Consistency

- Tox environment names are consistent across the plan: `py38-min`, `py39-max`, `py311-min`, `py311-max`, `py312-max`.
- The workflow job matrix and documentation use the same environment names as tox.
- The smoke check consistently uses `darlinpy.alignment.cas9_align.HAS_CPP_IMPL`.
