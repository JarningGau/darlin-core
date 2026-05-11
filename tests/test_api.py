#!/usr/bin/env python3
"""
DARLIN public API tests.
"""

import csv
import inspect
from pathlib import Path

import pytest

from darlin_core.api import AnalysisResult, analyze_sequences
from darlin_core.mutations.mutation import Mutation, MutationType


class TestAnalysisResult:
    """Tests for the supported AnalysisResult contract."""

    def test_top_level_exports_are_library_entry_points(self):
        import darlin_core

        assert "analyze_sequences" in darlin_core.__all__
        assert "AmpliconConfig" in darlin_core.__all__
        assert "build_carlin_config" in darlin_core.__all__

    def test_analysis_result_creation(self):
        result = AnalysisResult(
            mutations=[],
            alignment_scores=[85.5, 92.1, 78.3],
            summary_stats={"total_sequences": 3},
            aligned_query=["AAA", "CCC", "GGG"],
            aligned_reference=["AAA", "CCC", "GGG"],
            valid_sequences=["AAA", "CCC", "GGG"],
            config_used="Col1a1",
        )

        assert result.num_sequences == 3
        assert result.total_mutations == 0
        assert abs(result.average_alignment_score - 85.3) < 0.1
        assert sorted(result.__dataclass_fields__) == [
            "aligned_query",
            "aligned_reference",
            "alignment_scores",
            "config_used",
            "mutations",
            "processing_time",
            "summary_stats",
            "valid_sequences",
        ]

    def test_analysis_result_validation(self):
        with pytest.raises(ValueError):
            AnalysisResult(
                mutations=[[], []],
                alignment_scores=[85.5],
                valid_sequences=["ACGT"],
            )

    def test_analysis_result_properties(self):
        mutation = Mutation(
            type=MutationType.INDEL,
            loc_start=5,
            loc_end=5,
            seq_old="A",
            seq_new="T",
        )

        result = AnalysisResult(
            mutations=[[mutation]],
            alignment_scores=[85.5],
            summary_stats={"total_sequences": 1},
            aligned_query=["ACGTACGT"],
            aligned_reference=["ACGTACGT"],
            valid_sequences=["ACGTACGT"],
        )

        assert result.num_sequences == 1
        assert result.total_mutations == 1
        assert result.get_mutation_summary()["DI"] == 1

    def test_to_df_method(self):
        mutation = Mutation(
            type=MutationType.INDEL,
            loc_start=5,
            loc_end=5,
            seq_old="A",
            seq_new="T",
        )

        result = AnalysisResult(
            mutations=[[mutation], []],
            alignment_scores=[85.5, 92.1],
            aligned_query=["ACGTACGT", "TTGGTTGG"],
            aligned_reference=["ACGTACGT", "TTGGTTGG"],
            valid_sequences=["ACGTACGT", "TTGGTTGG"],
            summary_stats={"total_sequences": 2},
        )

        df = result.to_df()

        assert len(df) == 2
        assert "query" in df.columns
        assert "query_len" in df.columns
        assert "aligned_query" in df.columns
        assert "aligned_ref" in df.columns
        assert "scores" in df.columns
        assert "mutations" in df.columns
        assert "confidence" not in df.columns
        assert df["query"].iloc[0] == "ACGTACGT"
        assert df["query_len"].iloc[0] == 8
        assert df["scores"].iloc[0] == 85.5
        assert "5_5delinsT" in df["mutations"].iloc[0]
        assert df["query"].iloc[1] == "TTGGTTGG"
        assert df["query_len"].iloc[1] == 8
        assert df["scores"].iloc[1] == 92.1
        assert df["mutations"].iloc[1] == ""

    def test_print_summary(self, capsys):
        result = AnalysisResult(
            mutations=[],
            alignment_scores=[85.5],
            summary_stats={},
            config_used="Col1a1",
        )

        result.print_summary()
        captured = capsys.readouterr()

        assert "CARLIN Sequence Analysis Results Summary" in captured.out
        assert "Col1a1" in captured.out
        assert "Average alignment score" in captured.out
        assert "Successfully called alleles" not in captured.out

    def test_analysis_result_format_summary_returns_text_without_printing(self, capsys):
        result = AnalysisResult(
            mutations=[],
            alignment_scores=[85.5],
            summary_stats={},
            config_used="Col1a1",
        )

        summary = result.format_summary()
        captured = capsys.readouterr()

        assert "CARLIN Sequence Analysis Results Summary" in summary
        assert "Configuration: Col1a1" in summary
        assert captured.out == ""

    def test_analysis_result_to_df_uses_stable_empty_mutation_string(self):
        result = AnalysisResult(
            mutations=[[]],
            alignment_scores=[0.0],
            aligned_query=["ACGT"],
            aligned_reference=["ACGT"],
            valid_sequences=["ACGT"],
        )

        df = result.to_df()
        assert list(df.columns) == [
            "query",
            "query_len",
            "aligned_query",
            "aligned_ref",
            "scores",
            "mutations",
        ]
        assert df.loc[0, "mutations"] == ""


class TestAnalyzeSequences:
    """Tests for analyze_sequences."""

    def test_analyze_sequences_signature_excludes_allele_calling_parameters(self):
        assert list(inspect.signature(analyze_sequences).parameters) == [
            "sequences",
            "config",
            "annotate_mutations_flag",
            "merge_adjacent_mutations",
            "space",
            "verbose",
            "min_sequence_length",
        ]

    def test_analyze_sequences_is_quiet_by_default(self, capsys):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        ref = load_carlin_config_by_locus("Col1a1").get_full_reference_sequence()
        analyze_sequences([ref], config="Col1a1", verbose=False)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_analyze_empty_sequences(self):
        with pytest.raises(ValueError, match="Sequence list cannot be empty"):
            analyze_sequences([])

    def test_analyze_invalid_config(self):
        sequences = ["ACGTACGTACGTACGTACGT" * 10]

        with pytest.raises(ValueError, match="Unsupported locus"):
            analyze_sequences(sequences, config="InvalidConfig")

    def test_analyze_short_sequences(self):
        short_sequences = ["ACGT", "TTGG", "AAAA"]

        with pytest.raises(ValueError, match="No valid sequences available for analysis"):
            analyze_sequences(short_sequences)

    def test_analyze_valid_sequences_basic(self):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        carlin_config = load_carlin_config_by_locus("Col1a1")
        carlin_ref = carlin_config.get_full_reference_sequence()
        sequences = [
            carlin_ref[:200],
            carlin_ref[50:250],
            carlin_ref[-200:],
        ]

        result = analyze_sequences(
            sequences,
            config="Col1a1",
            verbose=False,
        )

        assert isinstance(result, AnalysisResult)
        assert len(result.mutations) == len(sequences)
        assert len(result.alignment_scores) == len(sequences)
        assert len(result.aligned_query) == len(sequences)
        assert len(result.aligned_reference) == len(sequences)
        assert result.config_used == "Col1a1"
        assert result.processing_time > 0
        assert sorted(result.__dict__) == [
            "aligned_query",
            "aligned_reference",
            "alignment_scores",
            "config_used",
            "mutations",
            "processing_time",
            "summary_stats",
            "valid_sequences",
        ]

    def test_analyze_sequences_space_parameter_controls_merging(self):
        query = "CGCCGGACTGCACGACAGTCGAAACGATGGAGTCGACACGACTCGCGCATAGGCGATGGGAGCT"

        merged = analyze_sequences(
            [query],
            config="Col1a1",
            min_sequence_length=20,
            verbose=False,
            merge_adjacent_mutations=True,
            space=3,
        )
        split = analyze_sequences(
            [query],
            config="Col1a1",
            min_sequence_length=20,
            verbose=False,
            merge_adjacent_mutations=True,
            space=0,
        )

        assert [m.to_hgvs() for m in merged.mutations[0]] == ["22_23insAA", "50_265delinsGG"]
        assert [m.to_hgvs() for m in split.mutations[0]] == ["22_23insAA", "50_263del", "265_265delinsG"]

    def test_align_sequence_sanitization_failure_is_quiet_by_default(self, monkeypatch, capsys):
        from darlin_core.alignment import create_default_aligner

        aligner = create_default_aligner()

        def explode(_aligned_seq):
            raise ValueError("synthetic sanitization failure")

        monkeypatch.setattr(aligner, "_perform_sanitization", explode)
        result = aligner.align_sequence(aligner.reference_sequence, verbose=False, sanitize=True)
        captured = capsys.readouterr()

        assert captured.out == ""
        assert result["sanitized"] is False

    def test_ca_benchmark_rows_match_truth_for_adjacent_merge_cases(self):
        benchmark_path = Path("tests/data/CA_benchmark.tsv")
        selected_queries = {
            "CGCCGGACTGCACGACAGTCGAAACGATGGAGTCGACACGACTCGCGCATAGGCGATGGGAGCT",
            "CGCCGGACTGCACGACAGTCGAACGATGGAGTCGACACGACTCGCGCATAGGAAAACGATGGGAGCT",
        }

        with benchmark_path.open() as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))

        for row in rows:
            if row["query"] not in selected_queries:
                continue

            result = analyze_sequences(
                [row["query"]],
                config="Col1a1",
                min_sequence_length=20,
                verbose=False,
                merge_adjacent_mutations=True,
                space=3,
            )

            observed = ",".join(m.to_hgvs() for m in result.mutations[0])
            assert observed == row["truth"]

    def test_analyze_sequences_expected_delins_annotation(self):
        from darlin_core import analyze_sequences as analyze_sequences_public

        sequences = [
            "CGCCGGACTGCACGACAGTCGAGCGATGGGAGCT",
            "CGCCGGACTGCACGACAGTCGACGATGGAGTCGACACGACTCGCGCATACGATGGAGTCGACTACAGTCGCTACGACGATGGAGTCGCGAGCGCTATGAGCGACTATGGAGTCGATACGATACGCGCACGCTATGGAGTCGAGAGCGCGCTCGTCGACTATGGAGTCGCGACTGTACGCACACGCGATGGAGTCGATAGTATGCGTACACGCGATGGAGTCGAGTCGAGACGCTGACGATATGGAGTCGATACGTAGCACGCAGACGATGGGAGCT",
        ]

        results = analyze_sequences_public(
            sequences,
            config="Col1a1",
            min_sequence_length=20,
            verbose=False,
        )
        df = results.to_df()
        assert df["mutations"].tolist() == ["23_265delinsG", ""]

    def test_analyze_sequences_no_mutations(self):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        carlin_config = load_carlin_config_by_locus("Col1a1")
        carlin_ref = carlin_config.get_full_reference_sequence()
        sequences = [carlin_ref[:200]]

        result = analyze_sequences(
            sequences,
            annotate_mutations_flag=False,
            verbose=False,
        )

        assert all(len(muts) == 0 for muts in result.mutations)

    def test_analyze_sequences_verbose(self, capsys):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        carlin_config = load_carlin_config_by_locus("Col1a1")
        carlin_ref = carlin_config.get_full_reference_sequence()
        sequences = [carlin_ref[:200]]

        analyze_sequences(sequences, verbose=True)

        captured = capsys.readouterr()
        assert "Starting analysis" in captured.out
        assert "Alignment completed" in captured.out
        assert "Allele calling completed" not in captured.out

    def test_analyze_different_configs(self):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        carlin_config = load_carlin_config_by_locus("Col1a1")
        carlin_ref = carlin_config.get_full_reference_sequence()
        sequences = [carlin_ref[:200]]

        for config in ["Col1a1", "Rosa"]:
            result = analyze_sequences(sequences, config=config, verbose=False)
            assert result.config_used == config

    def test_analyze_custom_parameters(self):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        carlin_config = load_carlin_config_by_locus("Col1a1")
        carlin_ref = carlin_config.get_full_reference_sequence()
        sequences = [carlin_ref[:200]]

        result = analyze_sequences(
            sequences,
            merge_adjacent_mutations=False,
            verbose=False,
        )

        assert isinstance(result, AnalysisResult)


class TestConfigLoading:
    """Tests for configuration loading helpers."""

    def test_load_config_by_locus(self):
        from darlin_core.config.amplicon_configs import load_carlin_config_by_locus

        assert load_carlin_config_by_locus("Col1a1") is not None
        assert load_carlin_config_by_locus("Rosa") is not None
        assert load_carlin_config_by_locus("Tigre") is not None


class TestStatistics:
    """Tests for summary statistics generation."""

    def test_generate_summary_stats(self):
        from darlin_core.api import _generate_summary_stats

        sequences = ["ACGTACGT" * 25, "TGCATGCA" * 25]
        alignment_results = [
            {"alignment_score": 85.5},
            {"alignment_score": 92.1},
        ]
        mutations_list = [[
            Mutation(
                type=MutationType.INDEL,
                loc_start=5,
                loc_end=5,
                seq_old="A",
                seq_new="T",
            )
        ], []]

        stats = _generate_summary_stats(
            sequences,
            alignment_results,
            mutations_list,
        )

        assert stats["total_sequences"] == 2
        assert stats["avg_sequence_length"] == 200.0
        assert stats["avg_alignment_score"] == (85.5 + 92.1) / 2
        assert stats["total_mutations"] == 1
        assert stats["avg_mutations_per_sequence"] == 0.5
        assert stats["mutation_type_distribution"]["DI"] == 1


class TestErrorHandling:
    """Tests for error propagation."""

    def test_analyze_sequences_runtime_error(self):
        sequences = ["ACGT"]

        with pytest.raises(ValueError):
            analyze_sequences(sequences)


class TestComplexMutationCases:
    """Complex mutation cases derived from repository fixtures."""

    def test_case_1_delins_identification(self):
        query = "CGCCGGACTGCACGACAGTCGAGTCGATGGAGTCGCGAGCGCTATGAGCGACGATGGAGTCGAGTCGAGACGCTGACGAAATATGGAGTCGATACGTAGCACGCAGAACGATGGGAGCT"

        results = analyze_sequences(
            [query],
            config="Col1a1",
            min_sequence_length=20,
            verbose=False,
            merge_adjacent_mutations=True,
        )

        observed_hgvs = [m.to_hgvs() for m in results.mutations[0]]
        assert observed_hgvs == [
            "23_76delinsGT",
            "104_211del",
            "238_239insAA",
            "265_266insA",
        ]
