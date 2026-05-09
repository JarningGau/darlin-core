# Python Compatibility Testing Design

## Goal

Design a repeatable compatibility test system for `darlinpy` that verifies:

- the package installs successfully across supported Python versions
- the required `pybind11` C++ extension is built and importable
- core package behavior passes a stable pytest subset under both minimum and latest dependency sets

The system should be CI-first and also provide a direct local reproduction path for every compatibility environment.

## Current Project Context

`darlinpy` is a Python package with a required compiled extension:

- `setup.py` declares `python_requires=">=3.8"`
- classifiers currently list Python `3.8`, `3.9`, `3.10`, and `3.11`
- build requirements come from `pyproject.toml` and include `setuptools`, `wheel`, and `pybind11`
- runtime dependencies are currently declared as:
  - `numpy>=1.20.0`
  - `scipy>=1.7.0`
  - `pandas>=1.3.0`

The repository already contains pytest-based tests, but it does not yet contain:

- a GitHub Actions workflow
- a version-matrix test runner such as `tox`
- an explicit minimum-dependency test mechanism

Because the compiled extension is required rather than optional, successful installation is itself a core compatibility assertion.

## Scope

This design covers:

- Python version compatibility testing
- minimum and latest runtime dependency boundary testing
- CI automation for the compatibility matrix
- local reproduction for each CI environment
- documentation of the compatibility workflow

This design does not cover:

- exhaustive dependency-combination testing beyond min/max boundaries
- wheel publishing or binary distribution
- performance benchmarking
- non-GitHub CI systems

## Supported Compatibility Contract

The compatibility system will enforce the following contract:

- officially supported Python versions: `3.8`, `3.9`, `3.10`, `3.11`
- exploratory Python version: `3.12`
- runtime dependency coverage per supported Python version:
  - minimum supported dependency set
  - latest resolvable dependency set

Python `3.12` will be tested as exploratory only. Failures on `3.12` should be visible in CI, but they must not fail the main required status checks.

## Success Criteria

The design is successful when all of the following are true:

1. Every supported Python version is tested in CI against both minimum and latest dependency sets.
2. The package installs from source in each environment using `pip install -e .`.
3. The compiled module `darlinpy.alignment._cas9_align` is built successfully, and `darlinpy.alignment.cas9_align.HAS_CPP_IMPL` evaluates to `True`.
4. A stable compatibility-focused pytest subset passes in each required environment.
5. Each CI environment can be reproduced locally with a matching `tox` environment name.

## Approach Options

### Option 1: GitHub Actions + tox

Use `tox` as the single environment-definition layer and GitHub Actions only as the execution host.

Pros:

- one source of truth for local and CI environments
- natural fit for Python-version and dependency-axis combinations
- easy local reproduction from CI failures
- compatible with future expansion such as lint, docs, or nightly jobs

Cons:

- requires adding and maintaining `tox.ini`
- minimum-dependency installation must be defined explicitly rather than inferred

Recommendation: this is the preferred approach.

### Option 2: GitHub Actions Only

Define the full matrix and all install logic directly in workflow YAML.

Pros:

- fewer files initially
- simple for a one-off workflow

Cons:

- local reproduction is weak
- matrix logic becomes embedded in CI config
- future maintenance gets harder as conditions expand

### Option 3: GitHub Actions + nox

Use `nox` sessions to script matrix behavior.

Pros:

- flexible Python-based session logic
- useful for complex conditional workflows

Cons:

- more custom machinery than needed here
- less conventional than `tox` for this specific compatibility problem

## Chosen Design

Use `tox` to define compatibility environments and GitHub Actions to run those environments in matrix form.

The design has four layers:

1. dependency boundary definition
2. tox environment definition
3. GitHub Actions execution matrix
4. minimal documentation for local reproduction

## Compatibility Matrix

### Required Matrix

The required CI matrix contains 8 blocking jobs:

- `py38-min`
- `py38-max`
- `py39-min`
- `py39-max`
- `py310-min`
- `py310-max`
- `py311-min`
- `py311-max`

### Exploratory Matrix

The exploratory CI matrix contains 2 non-blocking jobs:

- `py312-min`
- `py312-max`

These jobs should run and report status, but they should not fail the main PR or branch protection checks.

## Dependency Strategy

### Minimum Dependency Environments

Minimum dependency environments must use explicit pinned versions rather than relying on resolver behavior.

Initial minimum runtime dependency set:

- `numpy==1.20.0`
- `scipy==1.7.0`
- `pandas==1.3.0`

This set should live in a dedicated constraints or requirements file so that the meaning of "minimum dependency test" remains stable over time.

Recommended file:

- `requirements-min.txt`

The tox environment for `min` should install:

- test/build tooling
- pinned minimum runtime dependencies
- the package itself from source

### Latest Dependency Environments

Latest dependency environments should install the package normally and allow pip to resolve the latest compatible versions at test time.

This verifies forward compatibility against the current upstream ecosystem without attempting full dependency fuzzing.

## Installation and Smoke Checks

Each environment must perform a lightweight validation before running pytest:

1. install build and test tooling
2. install the target dependency set
3. run `pip install -e .`
4. import `darlinpy`
5. import the aligner module and assert `HAS_CPP_IMPL is True`

This early smoke check is important because the package includes a required native extension. It allows CI to fail with a precise installation/build error before entering the test suite.

## Test Selection Strategy

The compatibility matrix should not initially run the entire repository test suite.

Reasoning:

- the repository includes research-tool style tests and scripts
- some tests may be noisy, brittle, or overly sensitive to version-level numeric changes
- the purpose of this matrix is compatibility assurance, not exhaustive verification

Instead, define a stable compatibility-focused subset that covers core behavior:

- public API entry points
- config loading and default config behavior
- C++-backed alignment import and core alignment behavior
- mutation extraction behavior
- at least one integration path

Preferred initial coverage sources:

- `tests/test_api.py`
- `tests/test_config.py`
- `tests/test_cas9_align.py`
- `tests/test_mutations.py`
- selected stable cases from `tests/test_integration.py`

If some existing tests are too unstable for matrix use, they should be excluded from the compatibility subset rather than weakening the whole matrix.

## Tox Design

`tox` will be the authoritative environment interface for both local and CI usage.

Recommended environment naming pattern:

- `py38-min`
- `py38-max`
- `py39-min`
- `py39-max`
- `py310-min`
- `py310-max`
- `py311-min`
- `py311-max`
- `py312-min`
- `py312-max`

Each environment should:

- install `pytest`
- install the correct dependency mode
- install the package in editable mode
- run the smoke check
- run the compatibility-focused pytest command

The tox configuration should keep dependency mode explicit and avoid hiding behavior behind `.[dev]`, because `dev` currently includes unrelated tools such as formatting and typing utilities.

## GitHub Actions Design

Add a workflow file at:

- `.github/workflows/compatibility.yml`

The workflow should:

- trigger on pull requests and pushes to the main development branch
- use a matrix over Python version and dependency mode
- call the corresponding `tox` environment rather than reimplementing install logic inline
- mark Python `3.12` jobs as non-blocking
- surface job names clearly so failures identify both axes immediately

This keeps CI readable while ensuring that the actual environment behavior remains centralized in `tox`.

## Local Reproduction

Every CI job must have a direct local equivalent.

Examples:

- `tox -e py38-min`
- `tox -e py311-max`
- `tox -e py312-max`

This is a hard usability requirement. When CI fails, developers should be able to reproduce the exact environment name locally without reconstructing package-install logic from the workflow.

## Documentation Updates

Add a short developer-facing section to either `README.md` or `DEVELOPERS.md` describing:

- which Python versions are officially supported
- how compatibility testing is organized
- how to run a local tox environment
- what `min` and `max` mean

`DEVELOPERS.md` is the better fit because this is contributor workflow documentation rather than end-user installation guidance.

## File-Level Deliverables

The implementation phase should produce at least:

- `.github/workflows/compatibility.yml`
- `tox.ini`
- `requirements-min.txt`
- a small documentation update in `DEVELOPERS.md`

It may also produce one of the following if needed for test stability:

- a dedicated compatibility test command in tox
- a pytest marker
- a curated explicit compatibility test list

## Error Handling and Failure Modes

The design should make these failures distinguishable:

- Python-version incompatibility
- minimum dependency incompatibility
- latest dependency regression
- native extension build failure
- test-suite behavioral regression

This is why the workflow must keep:

- environment names explicit
- smoke checks separate from pytest
- exploratory Python jobs distinct from required jobs

## Implementation Notes

The implementation should prefer the smallest configuration that preserves clarity:

- do not introduce dependency-lock tooling
- do not attempt complete dependency-combination coverage
- do not merge exploratory and required status semantics
- do not overuse extras such as `.[dev]` for compatibility jobs

The first usable version should focus on reliable min/max boundary coverage. Broader environment exploration can be added later as nightly or optional jobs if needed.

## Out of Scope Follow-Ups

Possible future extensions, but not part of this implementation:

- automatic testing against pre-release NumPy or upcoming Python beta versions
- platform-matrix expansion across Linux, macOS, and Windows
- wheel-build verification
- nightly expanded compatibility sweeps
- splitting stable/slow/experimental test layers into separate CI workflows

## Final Recommendation

Implement compatibility testing with `tox` as the source of truth and GitHub Actions as the execution layer.

The concrete compatibility contract should be:

- supported: Python `3.8-3.11`
- exploratory: Python `3.12`
- dependencies per Python version: `min` and `max`
- pass conditions: source install succeeds, C++ extension is active, compatibility pytest subset passes

This gives `darlinpy` a clear, enforceable support boundary without overbuilding the CI system.
