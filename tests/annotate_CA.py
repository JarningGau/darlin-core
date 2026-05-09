#!/usr/bin/env python3
"""
Compare darlinpy calls to MATLAB truth for Col1a1 (CA).

Input: tests/data/CA_matlab.tsv with columns:
  - query
  - matlab

Output TSV columns:
  1) query
  2) matlab
  3) darlinpy (mutation)
  4) aligned_query
  5) aligned_ref
"""

from pathlib import Path

import pandas as pd

from darlinpy import analyze_sequences


def main() -> None:
    data_path = Path(__file__).resolve().parent / "data" / "CA_matlab.tsv"
    in_df = pd.read_csv(data_path, sep="\t", dtype=str).fillna("")
    if "query" not in in_df.columns or "matlab" not in in_df.columns:
        raise ValueError(f"Expected columns ['query', 'matlab'] in {data_path}")

    # Keep only sequences that will be analyzed to preserve 1:1 row alignment.
    min_sequence_length = 20
    in_df["query"] = in_df["query"].astype(str)
    in_df["matlab"] = in_df["matlab"].astype(str)
    in_df = in_df.loc[in_df["query"].str.len() >= min_sequence_length, ["query", "matlab"]].reset_index(drop=True)
    sequences = in_df["query"].tolist()

    results = analyze_sequences(
        sequences,
        config="Col1a1",
        verbose=False,
        min_sequence_length=min_sequence_length,
    )
    df = results.to_df()

    out_df = pd.DataFrame(
        {
            "query": df["query"],
            "matlab": in_df["matlab"],
            "darlinpy": df["mutations"],
            "aligned_query": df["aligned_query"],
            "aligned_ref": df["aligned_ref"],
        }
    )

    out_path = Path(__file__).resolve().parents[1] / "temp" / "CA_matlab_compare.tsv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False, sep="\t")
    print(str(out_path))


if __name__ == "__main__":
    main()
