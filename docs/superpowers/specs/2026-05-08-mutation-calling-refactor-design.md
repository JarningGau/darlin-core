# Mutation Calling Refactor Design

Date: 2026-05-08

## Goal

Refactor mutation calling so it infers mutation events directly from the full alignment rather than from motif-local heuristics.

The new mutation caller should be simpler and more predictable:

- scan the full aligned query/reference strings left to right
- emit each mutation block directly from the alignment
- do not merge nearby events after the fact
- report only three mutation types: `del`, `ins`, and `delins`
- treat mismatch-only blocks as `delins`
- do not compute or report mutation confidence

## Current Problem

The current implementation identifies mutations per motif and then tries to recover larger biological events by:

- extending motif-local events outward
- handling many special cases for gaps and nearby substitutions
- merging adjacent events later with a generic sequence concatenation step

This has made the mutation-calling logic difficult to reason about. It also means motif boundaries influence mutation calling even though the desired behavior should come from the alignment itself.

## Design Summary

Replace motif-first mutation inference with a single full-alignment event scanner.

The scanner will:

1. Flatten `AlignedSEQ` into one aligned query string and one aligned reference string.
2. Walk alignment columns from left to right.
3. Start a mutation event at the first column where query and reference differ.
4. Continue collecting columns until aligned matching resumes.
5. Build one `Mutation` object from that contiguous edited block.
6. Classify the block as `del`, `ins`, or `delins` from the collected reference/query bases.

Motif boundaries are ignored during event inference.

## Event Model

An event is defined by one contiguous run of alignment columns where the aligned query and aligned reference are not equal.

For each event:

- collect reference non-gap bases into `seq_old`
- collect query non-gap bases into `seq_new`
- derive positions from reference coordinates only

Classification:

- `del`: `seq_old` is non-empty and `seq_new` is empty
- `ins`: `seq_old` is empty and `seq_new` is non-empty
- `delins`: both `seq_old` and `seq_new` are non-empty

This means all mismatch-only regions become `delins`. There is no separate substitution type.

## Coordinates And HGVS Surface

Mutation coordinates remain 1-based and reference-oriented.

- `loc_start` is the first affected reference base position
- `loc_end` is the last affected reference base position

For deletions and delins, the coordinate span covers the replaced reference interval directly represented by the event block.

For insertions:

- keep the existing internal convention that insertions use `loc_start == loc_end`
- keep the current HGVS rendering style of `N_(N+1)insSEQ`

No additional proximity-based normalization or post hoc event merging should be applied.

## Confidence Removal

Mutation calling should not compute or expose confidence for now.

Implications:

- mutation identification should not assign confidence values or labels
- Cas9-specific mutation filtering should not modify or annotate mutation confidence
- public mutation reporting should be based only on inferred event content and coordinates

If confidence is needed later, it should be introduced as a separate design rather than preserved implicitly in this refactor.

## Component Changes

### `darlinpy/mutations/mutation.py`

Refactor `MutationIdentifier` so that:

- `identify_sequence_events()` uses a full-alignment scanner
- motif-local mutation inference is removed or reduced to compatibility helpers only if still needed internally
- mutation type output is restricted to `DELETION`, `INSERTION`, and `INDEL`
- mismatch-only aligned blocks are emitted as `INDEL`
- adjacency merging is no longer part of the default reporting path

`MutationType.SUBSTITUTION`, `MutationType.COMPLEX`, and confidence-related behavior should be removed from active mutation-calling flow. If enum cleanup causes too much churn, the implementation may keep legacy enum values temporarily but must not emit them from the refactored caller.

### `annotate_mutations()`

Simplify `annotate_mutations()` so that:

- it returns the direct event list from the scanner
- `merge_adjacent` no longer changes the result in normal usage and should be removed or deprecated
- `cas9_mode` must not add confidence annotations

If API compatibility requires keeping parameters temporarily, they should become no-op compatibility shims and be marked for later cleanup.

### Cas9-Specific Flow

Cas9-related logic should not affect event inference.

Possible implementation choices:

- keep the existing method but make it a thin wrapper over the same event list without confidence handling
- or remove special-case mutation post-processing entirely if nothing else depends on it

The preferred direction is to avoid duplicated event logic.

## Testing

Update tests to validate the new simplified behavior.

Required coverage:

- pure deletion block -> `del`
- pure insertion block -> `ins`
- mismatch-only block -> `delins`
- mixed mismatch/gap block -> `delins`
- cross-motif edited block -> one event when the aligned mismatch/gap run is contiguous
- separate edited blocks divided by matching alignment columns -> separate events
- no confidence fields or confidence-based expectations in mutation-calling behavior

Existing integration cases should be reviewed and updated where they currently depend on:

- substitution-specific output
- complex mutation labeling
- adjacency merging
- confidence labels or confidence scores

## Out Of Scope

This refactor does not attempt to:

- redesign the alignment algorithm
- redefine insertion HGVS formatting
- add a new normalization layer beyond direct event extraction from the alignment
- preserve every historical internal heuristic if it conflicts with the simpler full-alignment model

## Risks

The main risk is expectation drift in existing tests and downstream code that currently assumes:

- substitution events exist as a separate mutation type
- nearby events are merged after calling
- confidence labels are present

That is acceptable for this refactor. The implementation should update tests and any affected public outputs to match the new simpler contract explicitly.

## Recommended Implementation Direction

Implement the scanner first and make tests pass against its raw output before removing compatibility code. Once the scanner behavior is covered, delete obsolete motif-growth and merge-heavy logic rather than adapting it further.
