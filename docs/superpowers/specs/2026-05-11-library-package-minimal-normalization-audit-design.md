# Library Package Minimal Normalization Audit Design

Date: 2026-05-11
Status: Proposed

## Summary

This spec defines a minimal normalization pass for `darlinpy` as a Python library package. The goal is not to make the repository release-perfect or broadly refactor the codebase. The goal is to remove the most obvious forms of redundancy and non-library behavior that remain visible in the current repository surface.

The resulting repository should look and behave like a maintained library package at a basic professional level: source control should track source rather than local build residue, public library calls should not print to stdout by default, formal tests should be distinct from benchmarks and ad hoc scripts, and packaging/documentation boundaries should match the declared library-only support model.

## Goals

- Remove tracked local build and cache artifacts from the maintained source tree.
- Eliminate unrequested stdout output from normal public library execution paths.
- Separate formal test coverage from benchmarks and manual helper scripts.
- Reduce packaging and metadata redundancy to the minimum needed for a clear library build surface.
- Align repository layout and documentation with the existing library-only support claim.

## Non-Goals

- Convert the repository into a full release-engineered package.
- Add a CLI, release automation, or PyPI publishing workflow.
- Perform large-scale internal refactors unrelated to library package boundaries.
- Migrate the project to a `src/` layout.
- Add full type coverage, broad lint expansion, or style-only rewrites.
- Remove every research-oriented or maintainer-oriented helper artifact from the repository.

## Scope

This work is intentionally limited to the following areas:

1. Source tree hygiene.
2. Runtime output behavior in public library code paths.
3. Separation of formal tests from benchmarks and manual scripts.
4. Minimal packaging entry-point and metadata normalization.
5. Documentation and support-boundary alignment.

## Current Problems

Based on the current repository state on 2026-05-11, the package has already moved toward a library-only model, but it still contains several issues that are visibly out of place for a maintained Python library package.

Observed problems include:

- Tracked compiled artifacts and interpreter cache directories under `darlinpy/` and `tests/`.
- Direct `print()` usage in normal library execution paths, especially in `darlinpy/api.py` and error-reporting paths in alignment code.
- Mixed responsibilities in `tests/`, where maintained pytest coverage sits alongside benchmark and script-style files.
- A packaging surface that is mostly modernized but still needs a cleaner division of responsibility between `pyproject.toml` and `setup.py`.
- Documentation that declares a library-only support boundary, while repository structure still leaves some ambiguity about what is formal versus internal.

## Design Principles

### Minimal but strict

This effort should fix the obvious violations of a library package contract without expanding into broad modernization work. The standard is not "best possible package," but "no clear mismatch between declared library identity and actual repository behavior."

### Library-first behavior

If a user imports and calls supported APIs from Python, the package should behave like a library rather than like a script. Normal success paths should be silent unless the caller explicitly opts into diagnostics.

### Clear boundaries

The repository should distinguish source from build residue, formal tests from auxiliary tooling, and supported interfaces from maintainer-only artifacts.

### Avoid speculative cleanup

Do not widen scope just because nearby code could also be improved. Each change in this phase must support the minimal normalization goal directly.

## Proposed Design

## 1. Source Tree Hygiene

The repository should not track local interpreter cache files, compiled Python cache artifacts, or locally built extension binaries as part of the intended maintained source surface.

This includes artifacts such as:

- `__pycache__/`
- `*.pyc`
- locally built extension outputs such as `darlinpy/alignment/_cas9_align.cpython-*.so`

Required changes:

- Remove tracked cache and binary build residue from version control.
- Ensure ignore rules clearly exclude these artifacts going forward.
- Preserve extension build behavior through the normal packaging/build process rather than through precommitted binaries.

Acceptance criteria:

- Git-tracked source no longer includes `__pycache__/`, `*.pyc`, or local extension binaries.
- `.gitignore` clearly covers those artifacts.
- The compiled extension remains build-generated rather than repository-preloaded.

## 2. Runtime Output Behavior

Supported public library execution should not emit stdout output by default.

The current repository still contains direct `print()` calls in code paths that are part of normal public API usage. That behavior is appropriate for scripts or notebooks under explicit user control, but not for the default behavior of a library package.

Required changes:

- Remove unconditional `print()` calls from normal public execution paths.
- Replace retained diagnostics with one of:
  - explicit `verbose`-gated output
  - `logging`
  - structured returned information where appropriate
- Continue to use exceptions for real error signaling rather than printing and continuing silently.

This phase does not require a sophisticated logging architecture. It only requires that the default supported library path be silent unless the caller asks for progress or diagnostics.

Acceptance criteria:

- Default calls to supported public APIs do not emit unrequested stdout output.
- Any retained user-facing diagnostics are explicitly opt-in.
- Tests can verify the default silent behavior.

## 3. Formal Tests vs. Benchmarks and Scripts

The repository should make a clear distinction between maintained test coverage and auxiliary execution artifacts.

The current `tests/` tree contains a mix of:

- maintained pytest test modules
- benchmark-oriented files
- script-style helpers or manual validation files

Minimal normalization does not require deleting auxiliary files, but it does require that they stop presenting themselves as part of the formal test surface.

Required changes:

- Keep `tests/` focused on maintained pytest tests and test data.
- Move benchmark files into a dedicated location such as `benchmarks/`.
- Move manual validation or helper scripts into a separate directory such as `scripts/` or `dev/`.
- Prevent non-test helper files from being treated as part of the default pytest discovery surface.

Acceptance criteria:

- Default pytest execution targets maintained tests only.
- Benchmark and manual helper files no longer live in the formal test surface.
- Directory structure reflects the difference between library contract verification and auxiliary maintainer tooling.

## 4. Packaging Entry Points and Metadata Redundancy

The repository already uses `pyproject.toml` as the main packaging configuration, but `setup.py` remains present to support the compiled extension build. Minimal normalization should reduce ambiguity without forcing a risky packaging redesign.

Design decision:

- `pyproject.toml` remains the single authoritative source of project metadata.
- `setup.py`, if retained, should exist only as a minimal build bridge for the extension and should not duplicate project metadata such as version, dependencies, or descriptive fields.

This phase does not require removing `setup.py` if that would create unnecessary packaging risk. The standard is clarity of responsibility, not maximal modernization.

Acceptance criteria:

- Project metadata is maintained in one authoritative location.
- `setup.py`, if present, contains only the minimal logic required for extension build support.
- A maintainer can easily tell which file defines metadata and which file defines build hookup.

## 5. Documentation and Support Boundary Alignment

The repository already describes itself as library-only. The remaining work is to make documentation and structure consistently honor that claim.

Required changes:

- Ensure README examples and support statements point to supported library APIs only.
- Avoid implying that benchmark files or helper scripts are supported user interfaces.
- Mark retained non-library artifacts as maintainer/internal where needed.
- Keep developer documentation explicit about:
  - the formal verification entry point
  - supported public API usage
  - the status of auxiliary scripts and benchmarks

Acceptance criteria:

- A user reading README will not mistake internal helper files for supported interfaces.
- A maintainer reading developer docs can identify the formal test command and the intended support boundary.
- Documentation matches the actual repository layout after normalization.

## Explicit Out-of-Scope Retentions

The following issues may remain after this work and are not considered failures of the minimal normalization goal:

- Research-code style variation across internal modules.
- Lack of comprehensive static typing.
- Lack of `src/` layout migration.
- Lack of release automation or publication workflow.
- Larger internal module decomposition or architectural cleanup.

These are consciously deferred to avoid scope creep.

## Implementation Order

Work should proceed in this order:

1. Source tree hygiene.
2. Runtime output cleanup in public library paths.
3. Test, benchmark, and helper-script separation.
4. Packaging entry-point clarification.
5. Documentation alignment and final boundary check.

This order reduces risk by addressing low-risk hygiene first, then public library contract behavior, then supporting structure and documentation.

## Risks and Trade-Offs

### Risk: Removing stdout changes local expectations

Some local users may currently rely on printed progress output. This is an acceptable trade-off for a library-first default, provided any needed diagnostics remain available through explicit opt-in mechanisms.

### Risk: Moving files may hide incidental coverage

Some script-style or benchmark files may currently carry ad hoc regression value. The mitigation is to distinguish true maintained tests from auxiliary tools before relocating files.

### Risk: Packaging cleanup may disturb extension builds

`setup.py` still participates in extension build wiring. The mitigation is to keep packaging changes minimal and avoid redesigning the extension build mechanism in this phase.

### Risk: Scope creep

Repository cleanup work invites incidental refactoring. The mitigation is to reject changes that do not directly serve the minimal normalization goals described in this spec.

## Verification Strategy

Verification for this work should confirm the library contract and repository boundary improvements rather than broader package maturity.

Required verification categories:

- Repository hygiene verification:
  - tracked source excludes cache and local binary build artifacts
- Library runtime verification:
  - supported API calls are silent by default
- Test surface verification:
  - default pytest covers maintained tests only
- Packaging verification:
  - installation/build still produces the required extension through the build process
- Documentation verification:
  - README and developer guidance match the supported boundary and actual file layout

## Acceptance Summary

This minimal normalization effort is complete when all of the following are true:

- The repository no longer tracks local cache or local binary build residue as source.
- Default supported library execution is silent unless diagnostics are explicitly requested.
- Benchmarks and manual scripts are separated from the formal test surface.
- Packaging metadata and build responsibilities are minimally clear and non-duplicative.
- Documentation and repository layout consistently present `darlinpy` as a library-only package.

## Recommended Next Step

Write an implementation plan that converts this spec into a small, ordered sequence of code and repository changes with explicit verification at each stage.
