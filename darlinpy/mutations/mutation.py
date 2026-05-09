#!/usr/bin/env python3
"""
CARLIN mutation annotation module.

Implements direct mutation event identification from full alignments and
HGVS-style formatting for deletion, insertion, and delins events.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Union

from ..alignment.aligned_seq import AlignedSEQ


class MutationType(Enum):
    """Mutation type enumeration."""

    INSERTION = "I"
    DELETION = "D"
    INDEL = "DI"


@dataclass
class Mutation:
    """
    Represents a single mutation event.

    Attributes:
        type: Mutation type
        loc_start: 1-based mutation start position
        loc_end: 1-based mutation end position
        seq_old: Original reference fragment
        seq_new: Mutated query fragment
        motif_index: Legacy compatibility field; scanner sets this to -1
        confidence: Legacy compatibility field, no longer used for reporting
        confidence_label: Legacy compatibility field, no longer used for reporting
    """

    type: MutationType
    loc_start: int
    loc_end: int
    seq_old: str
    seq_new: str
    motif_index: int = -1
    confidence: float = 1.0
    confidence_label: str = "Low"

    def __post_init__(self):
        if self.loc_start < 1:
            raise ValueError("Mutation position must be 1-based positive integer")
        if self.loc_end < self.loc_start:
            raise ValueError("End position cannot be less than start position")
        if self.confidence < 0 or self.confidence > 1:
            raise ValueError("Confidence must be between 0-1")

    @property
    def length_change(self) -> int:
        return len(self.seq_new) - len(self.seq_old)

    @property
    def is_indel(self) -> bool:
        return self.type in [MutationType.INSERTION, MutationType.DELETION, MutationType.INDEL]

    @property
    def affected_length(self) -> int:
        return self.loc_end - self.loc_start + 1

    def to_hgvs(self, reference_name: str = "CARLIN") -> str:
        prefix = ""

        if self.type == MutationType.DELETION:
            return f"{prefix}{self.loc_start}_{self.loc_end}del"

        if self.type == MutationType.INSERTION:
            return f"{prefix}{self.loc_start}_{self.loc_start + 1}ins{self.seq_new}"

        if self.seq_new:
            return f"{prefix}{self.loc_start}_{self.loc_end}delins{self.seq_new}"

        return f"{prefix}{self.loc_start}_{self.loc_end}del"

    def __str__(self) -> str:
        return self.to_hgvs()

    def __repr__(self) -> str:
        return (
            f"Mutation(type={self.type.value}, "
            f"pos={self.loc_start}-{self.loc_end}, "
            f"'{self.seq_old}'->'{self.seq_new}', "
            f"motif={self.motif_index})"
        )


class MutationIdentifier:
    """
    Identifies mutation events from an AlignedSEQ by scanning the full alignment.
    """

    def __init__(self, min_confidence: float = 0.8):
        self.min_confidence = min_confidence

    def identify_sequence_events(self, aligned_seq: AlignedSEQ) -> List[Mutation]:
        query = aligned_seq.get_seq()
        ref = aligned_seq.get_ref()
        mutations: List[Mutation] = []
        ref_pos = 0
        i = 0

        while i < len(ref):
            if query[i] == ref[i]:
                if ref[i] != "-":
                    ref_pos += 1
                i += 1
                continue

            start_ref_pos: Optional[int] = None
            end_ref_pos: Optional[int] = None
            seq_old: List[str] = []
            seq_new: List[str] = []

            while i < len(ref) and query[i] != ref[i]:
                if ref[i] != "-":
                    ref_pos += 1
                    if start_ref_pos is None:
                        start_ref_pos = ref_pos
                    end_ref_pos = ref_pos
                    seq_old.append(ref[i])
                if query[i] != "-":
                    seq_new.append(query[i])
                i += 1

            seq_old_str = "".join(seq_old)
            seq_new_str = "".join(seq_new)

            if seq_old_str and seq_new_str:
                mutation_type = MutationType.INDEL
                loc_start = start_ref_pos
                loc_end = end_ref_pos
            elif seq_old_str:
                mutation_type = MutationType.DELETION
                loc_start = start_ref_pos
                loc_end = end_ref_pos
            else:
                mutation_type = MutationType.INSERTION
                anchor = max(ref_pos, 1)
                loc_start = anchor
                loc_end = anchor

            mutations.append(
                Mutation(
                    type=mutation_type,
                    loc_start=loc_start,
                    loc_end=loc_end,
                    seq_old=seq_old_str,
                    seq_new=seq_new_str,
                    motif_index=-1,
                    confidence=self.min_confidence,
                    confidence_label="Low",
                )
            )

        return mutations

    def identify_cas9_events(
        self, aligned_seq: AlignedSEQ, cut_sites: Optional[List[int]] = None
    ) -> List[Mutation]:
        return self.identify_sequence_events(aligned_seq)

    def merge_adjacent_mutations(
        self, mutations: List[Mutation], max_distance: int = 3
    ) -> List[Mutation]:
        if max_distance < 0:
            raise ValueError("max_distance must be >= 0")
        if len(mutations) <= 1:
            return list(mutations)

        ordered = sorted(mutations, key=lambda m: (m.loc_start, m.loc_end))
        merged = [ordered[0]]

        for mutation in ordered[1:]:
            current = merged[-1]
            distance = mutation.loc_start - current.loc_end - 1

            if distance <= max_distance:
                merged[-1] = self._merge_two_mutations(current, mutation)
            else:
                merged.append(mutation)

        return merged

    def _merge_two_mutations(self, mut1: Mutation, mut2: Mutation) -> Mutation:
        seq_old = mut1.seq_old + mut2.seq_old
        seq_new = mut1.seq_new + mut2.seq_new
        merged_type = (
            mut1.type
            if mut1.type == mut2.type and mut1.type != MutationType.INSERTION
            else MutationType.INDEL
        )
        return Mutation(
            type=merged_type,
            loc_start=min(mut1.loc_start, mut2.loc_start),
            loc_end=max(mut1.loc_end, mut2.loc_end),
            seq_old=seq_old,
            seq_new=seq_new,
            motif_index=min(mut1.motif_index, mut2.motif_index),
            confidence=(mut1.confidence + mut2.confidence) / 2,
            confidence_label="Low",
        )


def annotate_mutations(
    aligned_seq: AlignedSEQ,
    cas9_mode: bool = True,
    cut_sites: Optional[List[int]] = None,
    merge_adjacent: bool = True,
    space: int = 3,
) -> List[Mutation]:
    identifier = MutationIdentifier()
    mutations = identifier.identify_sequence_events(aligned_seq)
    if not merge_adjacent:
        return mutations
    return identifier.merge_adjacent_mutations(mutations, max_distance=space)
