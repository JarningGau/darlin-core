# Library-Only Package Normalization Design

Date: 2026-05-09
Status: Proposed

## Summary

This spec defines a normalization pass that reshapes `darlinpy` into a standard research-grade Python library for bioinformatics use. The goal is not to expand feature scope, add a command-line interface, or complete a PyPI release workflow. The goal is to make the existing library surface clearer, more stable, better tested, better packaged, and better documented.

The resulting package should behave like a library-first dependency that downstream Python code can import safely. Public API boundaries should be explicit, runtime side effects should be controlled, tests and CI should exercise supported usage patterns, packaging metadata should match modern Python expectations, and documentation should describe only what the current codebase formally supports.

## Goals

- Define and document the supported public API for library consumers.
- Reduce coupling between users and internal implementation modules.
- Remove or control unrequested runtime side effects from library code.
- Normalize packaging metadata and source tree hygiene for standard Python packaging workflows.
- Align tests and CI with the supported library-only usage model.
- Rewrite user-facing documentation so it reflects the current implementation rather than historical or aspirational behavior.
- Keep `bin/` out of the supported user surface while preserving the option to remove it from the release surface later.

## Non-Goals

- Add new analysis features, new algorithms, or new input formats.
- Introduce a supported CLI.
- Promise end-user support for scripts under `bin/`.
- Commit to a full PyPI release workflow in this phase.
- Reorganize internal code purely for style if it does not support the library-only normalization goal.

## Scope

This work covers five areas:

1. Public API definition and boundary setting.
2. Runtime behavior and result consistency.
3. Packaging, build metadata, and source tree hygiene.
4. Tests, CI, and quality checks for supported use cases.
5. User-facing and developer-facing documentation.

## Current Problems

Based on the current repository state, the package is functional but still presents as research code that has been made installable, rather than as a cleanly bounded library.

Observed issues include:

- Public and internal interfaces are not clearly separated.
- Library code emits direct `print()` output during normal operation.
- Result schemas are not fully normalized for downstream use.
- Packaging metadata is split across older `setup.py` patterns and minimal `pyproject.toml` configuration.
- Source directories contain compiled or cached artifacts that do not belong in the maintained source surface.
- Tests still carry some script-oriented patterns instead of library-oriented conventions.
- Documentation and support boundaries do not yet cleanly reflect a library-only support model.

## Design Principles

### Library-first

Consumers should be able to understand how to use `darlinpy` by reading the top-level package exports and a small number of high-level examples. Users should not need to depend on internal submodules to accomplish normal use cases.

### Explicit support boundaries

The package should state what is stable and what is internal. This reduces accidental compatibility commitments and allows implementation modules to evolve without being treated as public contract.

### Controlled runtime behavior

Library code should not print to stdout during normal successful execution unless the caller explicitly opts into that behavior.

### Stable downstream integration

Objects returned by supported APIs should have predictable structure and semantics so that notebooks, analysis pipelines, and test suites can consume them reliably.

### Minimal, purposeful normalization

This spec prefers focused corrections that improve library quality. It does not require broad refactoring unrelated to the supported library surface.

## Proposed Design

## 1. Public API Surface

The supported API should be defined at the package boundary and documented as such.

Supported public entry points should include:

- Top-level package imports exposed through `darlinpy.__init__`
- The high-level sequence analysis API
- Supported configuration construction/loading interfaces that are needed for normal library use
- Result objects returned by supported high-level APIs

Internal modules should remain importable for maintainers but should not be documented as stable user-facing interfaces unless intentionally promoted.

Expected outcomes:

- The README and API documentation point users to top-level imports first.
- Internal modules are described as implementation details unless explicitly promoted.
- `__all__` and module docs are used consistently where helpful to signal intended usage.

## 2. Runtime Behavior and Result Consistency

Library behavior should be safe for programmatic use.

Required changes:

- Replace unconditional user-facing `print()` calls in library execution paths with one of:
  - `logging`
  - explicit `verbose`-gated output
  - structured return information
- Preserve clear error signaling through exceptions for unsupported inputs and unrecoverable states.
- Normalize result conversion behavior so tabular outputs have stable column meaning and consistent empty-value handling.

For result objects:

- `AnalysisResult` remains the main high-level return type.
- Methods such as DataFrame conversion should produce stable schemas.
- Empty mutation values should use one consistent representation.
- Public result methods should be documented by behavior, not by incidental implementation details.

## 3. Packaging and Build Normalization

The package should move toward modern Python packaging conventions without changing its library-only scope.

Required changes:

- Consolidate project metadata into a more complete `pyproject.toml` configuration aligned with current Python packaging norms.
- Retain build support for the required C++ extension.
- Keep dependency declarations clear across runtime, development, and compatibility-testing concerns.
- Ensure package data inclusion rules are explicit and minimal.
- Remove compiled artifacts and cache files from the maintained source tree.

Expected outcomes:

- Build requirements and project metadata are easier to audit.
- The package can still be installed in editable and non-editable modes with the compiled extension requirement intact.
- Source control reflects source, not local build residue.

## 4. Tests and CI

Testing should reflect the supported library surface rather than historical script usage.

Required changes:

- Keep tests centered on supported Python import paths and high-level library behavior.
- Remove test patterns that exist only to support ad hoc script execution where they do not serve the maintained library interface.
- Preserve extension-aware testing so failures caused by missing compiled components remain clear.
- Expand CI beyond compatibility-only testing to include at least basic code quality checks appropriate for a research Python library.

Recommended CI coverage:

- Supported Python version compatibility
- Package install/build verification
- Core unit and integration tests for public APIs
- Lint and optionally static type checks

This phase does not require exhaustive style or type guarantees across every internal module, but it should establish a clear quality floor.

## 5. Documentation

Documentation should describe the package as it is supported now.

Required changes:

- Rewrite README around the supported library-only usage model.
- Remove any implication that `bin/` scripts are part of the supported user contract.
- Describe `bin/` as legacy/internal and note that it may later be removed from the release surface.
- Document installation expectations, including the compiled extension requirement.
- Provide a minimal high-confidence example using the supported high-level API.
- Add concise developer guidance for testing and local verification.

Documentation should prefer accuracy over breadth. Unsupported workflows should not appear in user-facing examples.

## `bin/` Handling

Scripts under `bin/` are not part of the supported user interface in this normalization effort.

Design decision:

- Keep `bin/` in the repository for now.
- Mark it as legacy/internal in documentation where needed.
- Do not treat it as part of the public API surface.
- Do not expand tests or user guides around it.
- Preserve the option to remove it from future release surfaces or repository layout in a later phase.

## Implementation Boundaries

This normalization effort may adjust internals where necessary to support the public contract, but it should avoid broad rearchitecture.

Allowed internal changes:

- Small module doc updates to clarify support boundaries
- Refactoring print-heavy paths into controlled reporting
- Normalizing result object behavior
- Packaging and metadata cleanup
- Test cleanup that aligns with supported behavior

Out of scope:

- Renaming or reorganizing large internal subsystems unless needed to support a public contract change
- Introducing a new CLI layer
- Rewriting the analysis model

## Acceptance Criteria

The normalization is complete when all of the following are true:

- The package clearly presents a library-only user model.
- Public API entry points are identifiable and documented.
- Internal modules are not implicitly presented as stable user-facing interfaces.
- Normal library usage does not emit unrequested stdout output.
- High-level result conversion behavior is stable and documented.
- Packaging metadata is normalized and sufficient for standard Python library maintenance.
- Source control no longer carries compiled or cached artifacts as part of the intended source surface.
- Tests and CI validate supported library behavior and extension expectations.
- User-facing documentation no longer suggests support for `bin/` as a formal interface.

## Risks and Trade-Offs

### Risk: Over-documenting internals

If documentation continues to describe internal modules in detail, users will keep depending on them. The mitigation is to lead with top-level APIs and document internals only as implementation notes.

### Risk: Tightening output semantics may break incidental consumers

Some existing local workflows may implicitly depend on current print behavior or loosely typed tabular output. The mitigation is to treat silent, structured library behavior as the target contract and note these changes in developer-facing documentation.

### Risk: Packaging cleanup touches multiple files

Metadata and build normalization may require coordinated edits across packaging files, docs, and CI. The mitigation is to keep changes scoped to packaging correctness rather than broad project restructuring.

## Verification Strategy

Verification for this work should demonstrate that the supported library contract still works after normalization.

Required verification categories:

- Editable install succeeds with documented prerequisites.
- Test suite passes for supported high-level APIs.
- Compiled extension expectations are exercised and fail clearly when unmet.
- README examples stay aligned with the supported API.
- CI covers the supported Python library maintenance path.

## Open Questions Resolved by This Spec

- Is the package a CLI-first tool? No.
- Is `bin/` part of the formal user interface? No.
- Should the current phase target full PyPI release operations? No.
- Should the current phase still normalize packaging and release readiness? Yes, to the level expected for a standard maintained research Python library.

## Recommended Next Step

Create an implementation plan that sequences the work in this order:

1. Public API and runtime behavior cleanup
2. Packaging and source tree normalization
3. Test and CI alignment
4. Documentation rewrite and final verification
