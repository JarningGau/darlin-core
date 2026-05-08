#!/usr/bin/env python3
"""
Mutation annotation tests.
"""

import pytest

from darlinpy.alignment.aligned_seq import AlignedSEQ
from darlinpy.mutations import Mutation, MutationIdentifier, MutationType, annotate_mutations


class TestMutation:
    def test_mutation_creation(self):
        mutation = Mutation(
            type=MutationType.INDEL,
            loc_start=10,
            loc_end=10,
            seq_old="A",
            seq_new="T",
            motif_index=0,
        )

        assert mutation.type == MutationType.INDEL
        assert mutation.loc_start == 10
        assert mutation.loc_end == 10
        assert mutation.seq_old == "A"
        assert mutation.seq_new == "T"
        assert mutation.motif_index == 0

    def test_mutation_validation(self):
        with pytest.raises(ValueError):
            Mutation(
                type=MutationType.INDEL,
                loc_start=0,
                loc_end=5,
                seq_old="A",
                seq_new="T",
            )

        with pytest.raises(ValueError):
            Mutation(
                type=MutationType.INDEL,
                loc_start=10,
                loc_end=5,
                seq_old="A",
                seq_new="T",
            )

    def test_mutation_properties(self):
        deletion = Mutation(
            type=MutationType.DELETION,
            loc_start=10,
            loc_end=12,
            seq_old="ATG",
            seq_new="",
        )
        assert deletion.length_change == -3
        assert deletion.is_indel is True
        assert deletion.affected_length == 3

        insertion = Mutation(
            type=MutationType.INSERTION,
            loc_start=10,
            loc_end=10,
            seq_old="",
            seq_new="GCC",
        )
        assert insertion.length_change == 3
        assert insertion.is_indel is True
        assert insertion.affected_length == 1

        delins = Mutation(
            type=MutationType.INDEL,
            loc_start=10,
            loc_end=10,
            seq_old="A",
            seq_new="T",
        )
        assert delins.length_change == 0
        assert delins.is_indel is True
        assert delins.affected_length == 1

    def test_hgvs_annotation(self):
        deletion = Mutation(
            type=MutationType.DELETION,
            loc_start=100,
            loc_end=100,
            seq_old="A",
            seq_new="",
        )
        assert deletion.to_hgvs() == "100_100del"

        multi_del = Mutation(
            type=MutationType.DELETION,
            loc_start=100,
            loc_end=102,
            seq_old="ATG",
            seq_new="",
        )
        assert multi_del.to_hgvs() == "100_102del"

        insertion = Mutation(
            type=MutationType.INSERTION,
            loc_start=100,
            loc_end=100,
            seq_old="",
            seq_new="GCC",
        )
        assert insertion.to_hgvs() == "100_101insGCC"

        delins = Mutation(
            type=MutationType.INDEL,
            loc_start=100,
            loc_end=102,
            seq_old="ATG",
            seq_new="GCC",
        )
        assert delins.to_hgvs() == "100_102delinsGCC"

    def test_string_representation(self):
        mutation = Mutation(
            type=MutationType.INDEL,
            loc_start=100,
            loc_end=100,
            seq_old="A",
            seq_new="T",
            motif_index=3,
        )

        assert str(mutation) == "100_100delinsT"
        repr_str = repr(mutation)
        assert "Mutation(type=DI" in repr_str
        assert "pos=100-100" in repr_str
        assert "'A'->'T'" in repr_str
        assert "motif=3" in repr_str


class TestMutationIdentifier:
    def test_identify_mismatch_only_block_as_delins(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACGT", "TGCA"],
            ref_segments=["ACGT", "AGCA"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert len(mutations) == 1
        mutation = mutations[0]
        assert mutation.type == MutationType.INDEL
        assert mutation.loc_start == 5
        assert mutation.loc_end == 5
        assert mutation.seq_old == "A"
        assert mutation.seq_new == "T"

    def test_identify_deletion(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACGT", "----"],
            ref_segments=["ACGT", "TTGG"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert len(mutations) == 1
        mutation = mutations[0]
        assert mutation.type == MutationType.DELETION
        assert mutation.loc_start == 5
        assert mutation.loc_end == 8
        assert mutation.seq_old == "TTGG"
        assert mutation.seq_new == ""

    def test_identify_pure_insertion_ignores_reference_gaps_for_coordinates(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["AC", "TA", "GT"],
            ref_segments=["AC", "--", "GT"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert len(mutations) == 1
        mutation = mutations[0]
        assert mutation.type == MutationType.INSERTION
        assert mutation.loc_start == 2
        assert mutation.loc_end == 2
        assert mutation.seq_old == ""
        assert mutation.seq_new == "TA"

    def test_identify_cross_motif_contiguous_block_as_single_delins(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACG-", "TTA"],
            ref_segments=["ACGT", "-TA"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert len(mutations) == 1
        mutation = mutations[0]
        assert mutation.type == MutationType.INDEL
        assert mutation.loc_start == 4
        assert mutation.loc_end == 4
        assert mutation.seq_old == "T"
        assert mutation.seq_new == "T"

    def test_identify_mixed_gap_and_mismatch_block_as_delins(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["AC", "T-GA"],
            ref_segments=["AC", "GCTA"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert len(mutations) == 1
        mutation = mutations[0]
        assert mutation.type == MutationType.INDEL
        assert mutation.loc_start == 3
        assert mutation.loc_end == 5
        assert mutation.seq_old == "GCT"
        assert mutation.seq_new == "TG"

    def test_identify_separate_blocks_without_merge(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["AC-T", "GG", "AA"],
            ref_segments=["ACGT", "GG", "TA"],
        )

        mutations = MutationIdentifier().identify_sequence_events(aligned_seq)

        assert [m.to_hgvs() for m in mutations] == ["3_3del", "7_7delinsA"]


class TestAnnotateMutations:
    def test_annotate_mutations_basic(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACGT", "TGCA"],
            ref_segments=["ACGT", "AGCA"],
        )

        mutations = annotate_mutations(aligned_seq, cas9_mode=False)

        assert len(mutations) == 1
        assert mutations[0].type == MutationType.INDEL

    def test_annotate_mutations_cas9_mode_returns_same_events(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACGT", "----"],
            ref_segments=["ACGT", "TTGG"],
        )

        basic = annotate_mutations(aligned_seq, cas9_mode=False)
        cas9 = annotate_mutations(
            aligned_seq,
            cas9_mode=True,
            cut_sites=[7],
            merge_adjacent=True,
        )

        assert [m.to_hgvs() for m in cas9] == [m.to_hgvs() for m in basic]

    def test_annotate_mutations_no_mutations(self):
        aligned_seq = AlignedSEQ(
            seq_segments=["ACGT", "TTGG"],
            ref_segments=["ACGT", "TTGG"],
        )

        mutations = annotate_mutations(aligned_seq)

        assert len(mutations) == 0
