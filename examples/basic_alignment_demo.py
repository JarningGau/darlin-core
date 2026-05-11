#!/usr/bin/env python3
"""
Basic supported darlinpy workflow: alignment plus mutation annotation.
"""

from darlinpy import analyze_sequences
from darlinpy.config.amplicon_configs import load_carlin_config_by_locus


def main():
    reference = load_carlin_config_by_locus("Col1a1").get_full_reference_sequence()
    sequences = [
        reference[:200],
        "CGCCGGACTGCACGACAGTCGAAACGATGGAGTCGACACGACTCGCGCATAGGCGATGGGAGCT",
    ]

    print("Running alignment and mutation annotation...")
    results = analyze_sequences(sequences, config="Col1a1", min_sequence_length=20)
    print(results.to_df()[["query_len", "scores", "mutations"]])


if __name__ == "__main__":
    main()
