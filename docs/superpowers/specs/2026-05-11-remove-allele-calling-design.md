# Remove Allele Calling Design

Date: 2026-05-11
Status: Proposed

## Summary

This spec defines a breaking simplification of `darlinpy` that removes allele-calling behavior from the supported package surface. The package should present one clear responsibility: align DARLIN/CARLIN amplicon sequences to a configured reference and annotate the resulting edits as mutations.

The current repository still carries a dominant-allele model in public API parameters, result types, internal modules, tests, examples, and README language. That model is no longer part of the intended product boundary. This change removes it rather than hiding it behind compatibility shims.

## Goals

- Remove dominant-allele and allele-calling concepts from the supported package behavior.
- Shrink the public API to sequence alignment plus mutation annotation.
- Simplify high-level result objects so they describe only supported outputs.
- Rewrite tests, examples, and documentation to match the new package boundary.
- Accept breaking API changes where needed to make the supported contract unambiguous.

## Non-Goals

- Add new analysis capabilities, new output formats, or new alignment algorithms.
- Preserve backward compatibility for allele-calling parameters or result types.
- Keep deprecated allele-calling code paths available behind hidden flags.
- Reorganize unrelated subsystems that do not support this scope reduction.

## Current Problems

The repository currently mixes two different product stories:

- The README describes the package as aligning sequences, calling dominant alleles, and annotating mutations.
- `analyze_sequences()` still exposes allele-calling configuration through `method` and `dominant_threshold`.
- `AnalysisResult` still stores `called_alleles` and reports allele-calling statistics.
- `darlinpy/calling/` contains dedicated allele-calling logic and result types that no longer match the intended package purpose.
- Tests and examples reinforce allele-calling as a first-class feature.

This creates unnecessary complexity and a misleading public contract. Users reading the package surface can reasonably conclude that allele calling is supported and maintained, even though the intended scope is narrower.

## Design Principles

### One supported job

The package should expose one coherent analysis path: validate input sequences, align each valid sequence, annotate mutations from each aligned sequence, and return structured results for downstream analysis.

### No dead product language

If allele calling is out of scope, it should disappear from public parameters, result schemas, docs, examples, and test narratives. Leaving the terminology in place invites accidental support commitments.

### Breaking changes over ambiguous compatibility

This is an intentional API contraction. Removing obsolete concepts is preferable to preserving them as ignored parameters or empty result fields.

### Preserve useful downstream outputs

The simplification should not reduce the value of the package's real outputs. Alignment details, mutation annotations, tabular conversion, and input validation should remain stable and clear.

## Proposed Design

## 1. Public API Contract

`analyze_sequences()` remains the main high-level entry point, but its signature is reduced to parameters that directly serve alignment and mutation annotation.

Required API changes:

- Remove `method`.
- Remove `dominant_threshold`.
- Remove any documented support for exact versus coarse-grain allele-calling modes.

Expected supported behavior:

- Accept a sequence collection and a configuration or locus selector.
- Filter invalid or too-short inputs using the current supported validation rules.
- Align each valid sequence.
- Annotate mutations from each aligned sequence.
- Return a result object that describes those alignment and annotation outputs only.

## 2. Result Model Simplification

`AnalysisResult` should stop carrying allele-oriented state.

Required changes:

- Remove `called_alleles`.
- Remove allele-calling success metrics such as `num_called_alleles` and `calling_success_rate`.
- Remove user-facing summary language that refers to called alleles.
- Keep fields that describe valid sequences, aligned query/reference strings, alignment scores, mutation annotations, summary stats, processing time, and configuration identity.

If a per-sequence structured object is still useful internally or publicly, it should be named around alignment or annotation rather than allele semantics. This spec does not require introducing such a type unless it materially improves the supported API.

## 3. Module and Dependency Cleanup

The allele-calling subsystem should be removed from the main package surface and code path.

Required changes:

- Remove `darlinpy/calling/` from maintained package functionality.
- Remove imports and references to `AlleleCaller` and `AlleleCallResult` from `darlinpy/api.py` and any re-export surfaces.
- Remove or rewrite examples and tests that depend on allele-calling APIs.

Preferred end state:

- No top-level package docs or exports mention allele calling.
- The analysis flow in `darlinpy/api.py` is straightforward: align, annotate, assemble results.
- Internal naming reflects the supported domain rather than historical allele terminology.

## 4. Documentation and Examples

Documentation should state the package purpose precisely.

Required changes:

- Rewrite README summary text so it describes alignment and mutation annotation only.
- Remove examples centered on allele calling or dominant-allele interpretation.
- Update supported result descriptions so they match the simplified `AnalysisResult`.
- Keep minimal examples focused on the stable high-level API and DataFrame output.

The package should read as a tool for sequence alignment and edit annotation, not as a partially retained allele-calling framework.

## 5. Testing and Verification Scope

Tests should move from allele-calling correctness to supported library behavior.

Required test coverage areas:

- Empty-input and invalid-input validation.
- Minimum-length filtering behavior.
- Alignment result availability for valid sequences.
- Mutation annotation correctness for representative aligned sequences.
- Stable DataFrame output columns and empty-mutation handling.
- Public API checks proving that removed allele-calling parameters and result fields are no longer part of the supported contract.

Tests dedicated only to allele-calling methods, dominant-threshold behavior, or coarse-grain versus exact mode comparison should be removed or replaced.

## Error Handling

The current high-level error contract should remain explicit:

- Empty input collections should still raise a clear error.
- A batch that yields no valid sequences after filtering should still raise a clear error.
- Alignment or annotation failures that represent unrecoverable analysis errors should still surface as exceptions rather than being silently downgraded.

This change simplifies scope, but it does not soften correctness requirements.

## Acceptance Criteria

This simplification is complete when all of the following are true:

- Public API documentation no longer describes allele calling or dominant alleles.
- `analyze_sequences()` no longer accepts allele-calling parameters.
- `AnalysisResult` no longer exposes allele-oriented fields or summary metrics.
- The main analysis path no longer imports or executes allele-calling code.
- The maintained repository no longer includes tests and examples whose purpose is to validate allele-calling behavior.
- README and example code present the package as an alignment-and-annotation library.
- Verification covers the supported behavior that remains after the contraction.

## Risks and Trade-Offs

### Risk: Breaking downstream callers

Removing parameters and result fields will break consumers that depend on the old interface. This is accepted by design. The mitigation is to make the new scope explicit in docs, tests, and release notes or commit history.

### Risk: Incomplete cleanup leaves mixed terminology

If docs or exports still refer to alleles after the code path is removed, the package contract will remain confusing. The mitigation is to treat terminology cleanup as part of acceptance, not as optional polish.

### Risk: Removing a module exposes hidden coupling

Code outside `darlinpy/api.py` may still import allele-calling utilities. The mitigation is to use tests and repository search to remove or rewrite those references as part of the implementation.

## Verification Strategy

Verification for this work should show that the remaining supported contract is intact and that the removed contract is truly gone.

Required verification:

- Run the supported test suite for high-level analysis behavior.
- Confirm that no supported README or example path depends on allele-calling APIs.
- Confirm by code search that public package documentation and exports no longer advertise allele calling.
- Confirm that `analyze_sequences()` and `AnalysisResult` reflect only alignment and mutation-annotation concerns.
