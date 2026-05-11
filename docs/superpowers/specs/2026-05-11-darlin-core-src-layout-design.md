# Darlin Core Src Layout Migration Design

Date: 2026-05-11
Status: Proposed

## Summary

This spec defines a packaging-focused repository migration from the current `darlinpy` layout to a standard `src/` layout with a hard package rename. The goal is to make the maintained Python library import path `darlin_core`, make the published distribution name `darlin-core`, and ensure the compiled extension, package data, tests, and documentation all align with that new package identity.

This is an atomic rename and layout migration. The resulting repository should expose only `darlin_core` as the supported import package, store maintained package code only under `src/darlin_core/`, and publish only `darlin-core` as the distribution name.

## Goals

- Rename the supported Python import package from `darlinpy` to `darlin_core`.
- Move the maintained library package to `src/darlin_core/`.
- Rename the published distribution from `darlinpy` to `darlin-core`.
- Keep the pybind11 extension build working under the renamed package.
- Update tests, examples, scripts, and documentation so they consistently use the renamed package.
- Ensure package data and editable installs continue to work from the `src/` layout.

## Non-Goals

- Provide a compatibility alias or transition shim for `darlinpy`.
- Preserve old `darlinpy` imports for one release.
- Redesign the build backend or replace the current setuptools-plus-pybind11 approach.
- Perform unrelated internal refactors beyond what is needed for the rename and layout migration.
- Add release automation, CLI support, or broader packaging workflow changes.

## Scope

This work covers five areas:

1. Package and source tree relocation.
2. Distribution metadata rename.
3. Extension build path and module rename.
4. Import-path updates across tests, examples, scripts, and docs.
5. Verification for install, import, and package-data integrity.

## Current State

As of 2026-05-11, the repository uses:

- a top-level package directory at `darlinpy/`
- distribution metadata in `pyproject.toml` with `project.name = "darlinpy"`
- setuptools package discovery that includes `darlinpy` from the repository root
- a `setup.py` pybind11 extension declaration targeting `darlinpy.alignment._cas9_align`
- documentation and examples that present `darlinpy` as the supported library import path

The current layout works, but it keeps importable package code at the repository root and binds packaging identity to the legacy `darlinpy` name. That leaves the project with a non-standard library layout and a package name that no longer matches the intended long-term public identity.

## Design Principles

### Single public identity

After this migration, there should be one supported package identity only: `darlin_core` for Python imports and `darlin-core` for distribution metadata. Leaving mixed names in supported surfaces would create avoidable ambiguity.

### Standard source layout

Maintained Python package code should live only under `src/`. This reduces the chance of tests passing because the repository root is on `sys.path`, and it makes editable installs better reflect installed behavior.

### Minimal build-system disruption

The build wiring should change only as much as needed to support the rename and path move. The repository already uses setuptools and pybind11 successfully, so this migration should preserve that approach rather than redesign it.

### Complete boundary migration

This is not just a directory rename. Every maintained import path, build target, package-data rule, and user-facing example that refers to the old package identity must move in the same change.

## Proposed Design

## 1. Package And Build Layout

The maintained library package should move from `darlinpy/` to `src/darlin_core/`.

The repository should treat `src/darlin_core/` as the only maintained Python package root. The former top-level `darlinpy/` package directory should be removed rather than retained as an alias or forwarding package.

Packaging configuration should be updated so setuptools discovers packages from `src/` only. `pyproject.toml` should continue to hold authoritative package metadata, while `setup.py` remains the minimal extension-build bridge.

The pybind11 extension target should be renamed from `darlinpy.alignment._cas9_align` to `darlin_core.alignment._cas9_align`, and its source path should move accordingly to `src/darlin_core/alignment/_cas9_align.cpp`.

## 2. Distribution Metadata

The published distribution name should change from `darlinpy` to `darlin-core`.

Required metadata updates include:

- `project.name`
- repository and homepage URLs, where they encode the old package name
- package discovery configuration
- package data configuration
- any installation or verification examples that reference the distribution name

This migration does not need to settle broader release workflow questions, but metadata should be internally consistent and reflect the new public package identity.

## 3. Migration Surface

The migration should remove `darlinpy` from all maintained supported surfaces.

This includes:

- internal imports within the library package
- test imports and any package-path assertions
- example code under `examples/`
- supported script imports under maintained helper scripts
- README and developer documentation
- build configuration and extension module declarations
- package data paths such as JSON assets under the config package

Any retained `darlinpy` reference in maintained files should be treated as a migration defect unless it is clearly historical text or intentionally describing the old name in documentation.

## 4. Runtime And Data-File Expectations

The rename and `src/` migration must preserve runtime behavior.

In particular:

- top-level imports from `darlin_core` should expose the same supported public API currently exported by `darlinpy`
- the compiled extension should remain importable through the renamed alignment package
- JSON config assets under the config package should still be available at runtime after the move
- examples and tests should exercise the installed-package behavior expected from the `src/` layout

This spec does not change the supported API contract itself. It changes package identity and source layout while preserving the current supported library behavior.

## 5. Verification Strategy

Verification should prove both packaging correctness and runtime correctness.

Required checks:

- pytest passes after all maintained imports are updated to `darlin_core`
- editable installation succeeds from the `src/` layout
- a smoke import confirms the compiled extension remains importable through `darlin_core.alignment.cas9_align`
- package-data-backed configuration loading still works after the move
- maintained source files no longer contain stale `darlinpy` references except where explicitly historical

Recommended verification commands should include at least:

- the maintained pytest entry point
- an editable install or equivalent local packaging verification path
- a direct Python import smoke test for the extension-backed alignment module

## Risks And Trade-Offs

### Risk: Extension module name drift

If the extension build declaration is not renamed consistently with the package move, imports may compile successfully but fail at runtime. The mitigation is to update the fully qualified extension module name and verify import through the installed package path.

### Risk: `src/` discovery misconfiguration

If setuptools discovery or package-data rules still point at repository-root assumptions, installs may omit modules or JSON assets. The mitigation is to move package discovery explicitly to `src/` and verify runtime config loading.

### Risk: False-positive test success from local paths

Tests may pass accidentally if they rely on the repository root being importable. The mitigation is to verify editable installation behavior and keep the maintained package only under `src/`.

### Risk: Incomplete rename across supported surfaces

A partial rename would leave confusing mixed identity in docs, tests, or helper code. The mitigation is to treat every maintained `darlinpy` reference as suspect and audit the full migration surface in one pass.

## Acceptance Criteria

The migration is complete when all of the following are true:

- the supported Python import package is `darlin_core`
- maintained library code lives under `src/darlin_core/` only
- the published distribution metadata uses `darlin-core`
- the pybind11 extension builds and imports under `darlin_core.alignment._cas9_align`
- maintained tests, examples, scripts, and docs use the renamed package identity
- config package data remains available at runtime after the move
- editable install and test execution succeed without relying on the old top-level package layout
- no maintained supported surface still presents `darlinpy` as the current package name

## Implementation Order

Work should proceed in this order:

1. Move package code to `src/darlin_core/`.
2. Update build and package discovery configuration.
3. Rewrite internal and external imports to `darlin_core`.
4. Update documentation, examples, and helper scripts.
5. Run packaging and runtime verification, then fix any stale path assumptions.

This order reduces churn during the migration because package location and build identity are established before downstream references are rewritten and validated.
