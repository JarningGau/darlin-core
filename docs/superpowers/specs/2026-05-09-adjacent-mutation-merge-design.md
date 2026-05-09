# Adjacent Mutation Merge Design

## Goal

Enhance mutation reporting so adjacent mutation events are merged when the reference-space gap between them is less than or equal to a configurable threshold.

The new behavior must apply consistently across all mutation annotation paths, not only through `analyze_sequences()`.

## Motivation

The current mutation scanner emits one event per contiguous mismatch block in the alignment. This produces over-fragmented output for some biologically related edits when short matched islands separate neighboring mutation blocks.

The repository already exposes merge-related parameters in public APIs and already contains a dormant merge hook in `MutationIdentifier.merge_adjacent_mutations()`, but the current implementation does not apply any real merge behavior. The benchmark file `tests/data/CA_benchmark.tsv` includes examples where the current output is more fragmented than the expected truth set.

## Scope

This change covers:

- mutation merging behavior in the annotation layer
- public API plumbing for a configurable merge distance
- unit and benchmark-driven regression tests for the merge rule

This change does not cover:

- changing the alignment algorithm
- changing allele-calling logic
- introducing benchmark-only reconciliation logic

## Recommended Approach

Use a post-processing merge pass on top of the existing raw mutation scanner.

`identify_sequence_events()` should remain the raw event extractor. `annotate_mutations()` should become the canonical mutation-policy layer that:

1. collects raw events from the scanner
2. optionally merges adjacent events using a configurable distance threshold
3. returns the final reported mutations

This keeps event extraction and reporting policy separate, minimizes churn, and makes the merge rule available to every caller that uses mutation annotation.

## Alternatives Considered

### 1. Merge inside the scanner

The scanner could continue across short matched islands and emit a single larger event. This was rejected because it mixes raw event detection with reporting policy and makes the scanner harder to reason about and test.

### 2. Benchmark-only output reconciliation

The benchmark path could add a special merge step without changing general mutation annotation. This was rejected because the desired behavior must apply to all mutation annotation paths, not just benchmark evaluation.

## Public API Changes

### `analyze_sequences()`

Add a new parameter:

- `space: int = 3`

Behavior:

- `merge_adjacent_mutations=False` returns raw scanner output
- `merge_adjacent_mutations=True` merges adjacent mutations when the reference-space gap is less than or equal to `space`

### `annotate_mutations()`

Add the same new parameter:

- `space: int = 3`

This keeps direct annotation callers aligned with `analyze_sequences()` behavior.

## Merge Semantics

### Definition of distance

“Space” means the number of reference bases between two reported mutation events.

For two events `current` and `next`:

- for events that consume reference bases, use `next.loc_start - current.loc_end - 1`
- for insertions anchored at position `p`, treat the event as occurring at `p`

The merge rule is:

- merge when computed space is less than or equal to `max_distance`
- do not merge when computed space is greater than `max_distance`

### Chained merges

Merging is iterative. If `A` merges with `B`, and merged `(A+B)` is still within threshold of `C`, all three collapse into one event.

### Boundary cases

- empty mutation list: unchanged
- single-mutation list: unchanged
- `space=0`: only directly adjacent events merge
- `space<0`: invalid input, raise `ValueError`

## Merge Output Construction

When two events merge:

- `loc_start` is the minimum of the two starts
- `loc_end` is the maximum of the two ends
- `seq_old` is the concatenation of the two `seq_old` fragments in order
- `seq_new` is the concatenation of the two `seq_new` fragments in order

Type resolution:

- if both events share the same non-insertion type, keep that type
- otherwise emit `MutationType.INDEL`

This preserves the current simple type-resolution rule and avoids adding type-specific special cases that are not required for this feature.

## Internal Flow

### `MutationIdentifier.identify_sequence_events()`

No merge-distance logic is added here. It continues to emit raw mutation blocks from the alignment scan.

### `MutationIdentifier.merge_adjacent_mutations()`

Implement the actual merge pass here. Responsibilities:

- sort mutations by `loc_start`
- compute distance between consecutive events
- merge when distance is within threshold
- support chained merges

### `annotate_mutations()`

Responsibilities:

1. instantiate `MutationIdentifier`
2. collect raw events with `identify_sequence_events()`
3. if `merge_adjacent` is true, call `merge_adjacent_mutations(..., max_distance=space)`
4. return the final event list

### `analyze_sequences()`

Responsibilities:

- expose `space: int = 3`
- pass `merge_adjacent_mutations` and `space` through to `annotate_mutations()`
- avoid implementing merge logic locally

## Testing Strategy

### Unit tests

Add focused tests in `tests/test_mutations.py` for:

- no merge when distance is greater than `space`
- merge when distance equals `space`
- chained merges across three events
- `annotate_mutations(..., merge_adjacent=False)` preserving raw scanner output
- `annotate_mutations(..., merge_adjacent=True, space=3)` applying merged output
- negative `space` raising `ValueError`

### Benchmark-driven regression tests

Use `tests/data/CA_benchmark.tsv` as benchmark coverage for the merge rule.

Recommended implementation:

- add a test that loads the TSV rows
- run `analyze_sequences(..., merge_adjacent_mutations=True, space=3)`
- compare produced HGVS strings against the `truth` column for rows chosen to specifically exercise adjacent-event merging

The benchmark coverage should start with rows whose mismatch between current output and truth is clearly attributable to short-gap merge behavior. This avoids coupling the feature test to unrelated alignment or normalization discrepancies.

## Expected Outcome

The feature should reduce over-fragmented mutation output in cases where short matched islands split what should be reported as one larger event.

Representative example:

- current fragmented output: `50_263del,265_265delinsG`
- expected merged output with `space=3`: `50_265delinsG`

## Files Expected To Change

- `darlinpy/api.py`
- `darlinpy/mutations/mutation.py`
- `tests/test_mutations.py`
- `tests/test_api.py` for direct API-level coverage of the new `space` parameter
