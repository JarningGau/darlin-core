#!/usr/bin/env python3
"""
DARLIN Main API Module

Provides simplified high-level interface for CARLIN sequence analysis
"""

from typing import List, Dict, Any, Union
from dataclasses import dataclass, field
import time
import pandas as pd

from .config.amplicon_configs import AmpliconConfig
from .alignment.carlin_aligner import CARLINAligner
from .mutations.mutation import Mutation, annotate_mutations


@dataclass
class AnalysisResult:
    """
    CARLIN sequence analysis results

    Contains alignment, mutation annotation, and summary statistics for each
    valid input sequence.
    """
    mutations: List[List[Mutation]]
    alignment_scores: List[float]
    summary_stats: Dict[str, Any] = field(default_factory=dict)
    aligned_query: List[str] = field(default_factory=list)
    aligned_reference: List[str] = field(default_factory=list)
    valid_sequences: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    config_used: str = "Col1a1"

    def __post_init__(self):
        """Validate result data consistency"""
        expected = len(self.mutations)
        if expected == 0:
            return
        for field_name, values in (
            ("alignment_scores", self.alignment_scores),
            ("aligned_query", self.aligned_query),
            ("aligned_reference", self.aligned_reference),
            ("valid_sequences", self.valid_sequences),
        ):
            if values and len(values) != expected:
                raise ValueError(f"mutations and {field_name} must have the same length")
    
    @property
    def num_sequences(self) -> int:
        """Return total number of analyzed sequences"""
        return len(self.alignment_scores)
    
    @property
    def total_mutations(self) -> int:
        """Return total number of detected mutations"""
        return sum(len(muts) for muts in self.mutations)
    
    @property
    def average_alignment_score(self) -> float:
        """Return average alignment score"""
        if not self.alignment_scores:
            return 0.0
        return sum(self.alignment_scores) / len(self.alignment_scores)
    
    def get_mutation_summary(self) -> Dict[str, int]:
        """Get mutation type statistics"""
        mutation_counts = {}
        for mut_list in self.mutations:
            for mut in mut_list:
                mut_type = mut.type.value
                mutation_counts[mut_type] = mutation_counts.get(mut_type, 0) + 1
        return mutation_counts

    def to_df(self) -> pd.DataFrame:
        """Convert analysis results to pandas DataFrame
        
        Returns:
            pd.DataFrame: DataFrame containing analysis results with columns:
                - query: Original input sequences
                - query_len: Length of each sequence
                - aligned_query: Aligned query sequences
                - aligned_ref: Aligned reference sequences
                - scores: Alignment scores
                - mutations: Comma-separated list of mutations in HGVS format
        """
        mutation_strings = []
        for mut_list in self.mutations:
            mutation_strings.append(
                ",".join(m.to_hgvs() for m in mut_list) if mut_list else ""
            )

        results_df = pd.DataFrame({
            'query': self.valid_sequences,
            'query_len': [len(s) for s in self.valid_sequences],
            'aligned_query': self.aligned_query,
            'aligned_ref': self.aligned_reference,
            'scores': self.alignment_scores,
            'mutations': mutation_strings,
        })
        return results_df
    
    def print_summary(self):
        """Print analysis results summary"""
        print(self.format_summary())

    def format_summary(self) -> str:
        """Return the analysis summary as formatted text."""
        lines = [
            "CARLIN Sequence Analysis Results Summary",
            "=" * 40,
            f"Configuration: {self.config_used}",
            f"Processing time: {self.processing_time:.2f} seconds",
            "",
            "Sequence statistics:",
            f"  Total sequences: {self.num_sequences}",
            f"  Average alignment score: {self.average_alignment_score:.2f}",
            "",
            "Mutation statistics:",
            f"  Total mutations: {self.total_mutations}",
        ]
        mut_summary = self.get_mutation_summary()
        for mut_type, count in mut_summary.items():
            lines.append(f"  {mut_type} type: {count}")
        return "\n".join(lines)


def analyze_sequences(
    sequences: List[str],
    config: Union[str, AmpliconConfig] = 'Col1a1',
    annotate_mutations_flag: bool = True,
    merge_adjacent_mutations: bool = True,
    space: int = 3,
    verbose: bool = False,
    sanitize: bool = True,
    min_sequence_length: int = 50
) -> AnalysisResult:
    """
    Analyze CARLIN sequences
    
    Args:
        sequences: List of sequences to analyze
        config: Configuration, can be locus name string or AmpliconConfig object, defaults to 'Col1a1', options: "Col1a1", "Rosa", "Tigre"
        annotate_mutations_flag: Whether to annotate mutations
        merge_adjacent_mutations: Whether to merge adjacent mutations
        space: Maximum reference-space gap allowed when merging adjacent mutations
        verbose: Whether to show detailed information
        sanitize: Whether to normalize aligned sequences (prefix/postfix and conserved regions) before mutation annotation
        min_sequence_length: Minimum sequence length threshold, sequences shorter than this will be filtered
        
    Returns:
        Analysis results
    """
    start_time = time.time()
    
    if verbose:
        print(f"Starting analysis of {len(sequences)} sequences...")
    
    # Process configuration parameters
    if isinstance(config, str):
        # If string, treat as locus
        if config == 'OriginalCARLIN':
            # Backward compatibility: if user explicitly specifies OriginalCARLIN, use the original way
            from .config.amplicon_configs import get_original_carlin_config
            amplicon_config = get_original_carlin_config()
        else:
            # Treat as locus
            from .config.amplicon_configs import load_carlin_config_by_locus
            amplicon_config = load_carlin_config_by_locus(config)
    else:
        # Directly use the provided AmpliconConfig
        amplicon_config = config
    
    if verbose:
        print(f"Using configuration: {config}")

    if not sequences:
        raise ValueError("Sequence list cannot be empty")
    
    # Filter sequences (remove sequences that are too short or empty)
    valid_sequences = [seq for seq in sequences if seq and len(seq) >= min_sequence_length]
    if len(valid_sequences) < len(sequences):
        if verbose:
            print(f"Filtered {len(sequences) - len(valid_sequences)} short sequences (< {min_sequence_length}bp)")
    
    if not valid_sequences:
        raise ValueError("No valid sequences available for analysis")
    
    try:
        # 2. Sequence alignment
        if verbose:
            print("Performing sequence alignment...")
        
        aligner = CARLINAligner(amplicon_config=amplicon_config)
        alignment_results = aligner.align_sequences(valid_sequences, sanitize=sanitize)
        
        # Extract alignment scores and sequences
        alignment_scores = [result['alignment_score'] for result in alignment_results]
        aligned_sequences = [result.get('aligned_seq_obj') for result in alignment_results]
        
        if verbose:
            avg_score = sum(alignment_scores) / len(alignment_scores)
            print(f"Alignment completed, average score: {avg_score:.2f}")

        # 3. Mutation annotation
        mutations_list = []
        if annotate_mutations_flag:
            if verbose:
                print("Performing mutation annotation...")
            
            # Get CARLIN cut site information
            cut_sites = _get_cut_sites(amplicon_config)

            for aligned_seq in aligned_sequences:
                if aligned_seq is None:
                    mutations = []
                else:
                    mutations = annotate_mutations(
                        aligned_seq,
                        cas9_mode=True,
                        cut_sites=cut_sites,
                        merge_adjacent=merge_adjacent_mutations,
                        space=space,
                    )
                mutations_list.append(mutations)

            if verbose:
                total_mutations = sum(len(muts) for muts in mutations_list)
                print(f"Mutation annotation completed, detected {total_mutations} mutations")
        else:
            mutations_list = [[] for _ in aligned_sequences]

        # 4. Generate statistics
        summary_stats = _generate_summary_stats(
            valid_sequences, alignment_results, mutations_list
        )

        # 5. Build result object
        processing_time = time.time() - start_time

        result = AnalysisResult(
            mutations=mutations_list,
            alignment_scores=alignment_scores,
            summary_stats=summary_stats,
            aligned_query=[seq.get_seq() if seq is not None else "" for seq in aligned_sequences],
            aligned_reference=[seq.get_ref() if seq is not None else "" for seq in aligned_sequences],
            valid_sequences=valid_sequences,
            processing_time=processing_time,
            config_used=str(config),
        )
        
        if verbose:
            print(f"Analysis completed, time taken: {processing_time:.2f} seconds")
            result.print_summary()
        
        return result
        
    except Exception as e:
        raise RuntimeError(f"Error occurred during analysis: {str(e)}") from e


def _get_cut_sites(amplicon_config: AmpliconConfig) -> List[int]:
    """Get CARLIN Cas9 cut sites
    
    Uses the cutsite intervals (last 7bp) of each segment in the configuration, takes the center of each interval and converts to 1-based coordinates.
    """
    # positions['cutsites'] are 0-based half-open intervals (start, end) relative to CARLIN
    # Here we take the center point of each interval and convert to 1-based coordinates to match mutation positioning
    cutsite_intervals = amplicon_config.positions.get('cutsites', [])
    centers_1_based: List[int] = []
    for start_0_based, end_0_based in cutsite_intervals:
        # Interval is [start, end), last base index is end-1
        last_index = end_0_based - 1
        center_0_based = start_0_based + (last_index - start_0_based) // 2
        centers_1_based.append(center_0_based + 1)
    return centers_1_based


def _generate_summary_stats(
    sequences: List[str],
    alignment_results: List,
    mutations_list: List[List[Mutation]]
) -> Dict[str, Any]:
    """Generate summary statistics"""

    # Basic statistics
    stats = {
        'total_sequences': len(sequences),
        'avg_sequence_length': sum(len(seq) for seq in sequences) / len(sequences),
    }

    # Alignment statistics
    scores = [r['alignment_score'] for r in alignment_results]
    stats.update({
        'avg_alignment_score': sum(scores) / len(scores),
        'min_alignment_score': min(scores),
        'max_alignment_score': max(scores),
    })

    # Mutation statistics
    mutation_counts = {}
    total_mutations = 0
    for mut_list in mutations_list:
        total_mutations += len(mut_list)
        for mut in mut_list:
            mut_type = mut.type.value
            mutation_counts[mut_type] = mutation_counts.get(mut_type, 0) + 1

    stats.update({
        'total_mutations': total_mutations,
        'avg_mutations_per_sequence': total_mutations / len(mutations_list) if mutations_list else 0,
        'mutation_type_distribution': mutation_counts
    })

    return stats
