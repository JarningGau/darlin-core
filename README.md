# darlinpy

`darlinpy` is a library-only Python package for DARLIN/CARLIN sequence analysis. It aligns edited lineage-tracing amplicons to locus-specific references and converts edits into HGVS-like mutation annotations.

## Repository Layout

- `darlinpy/`: supported library package
- `tests/`: maintained pytest coverage for the supported library contract
- `benchmarks/`: maintainer-only performance experiments, not part of default verification
- `scripts/`: maintainer-only helper scripts, not supported user interfaces

## Installation

```bash
pip install -e .

## Verify installation
python -c "from darlinpy.alignment.cas9_align import HAS_CPP_IMPL; assert HAS_CPP_IMPL is True"
```

## Quick Start

```python
from darlinpy import analyze_sequences
from darlinpy.config.amplicon_configs import load_carlin_config_by_locus

## check the reference sequence
reference = load_carlin_config_by_locus("Col1a1").get_full_reference_sequence()

## align and annotate the lineage barcodes
sequences = [
    "CGCCGGACTGCACGACAGTCGACCGATGGAGTCGACACGACTCGCGCATATTCGATGGAGTCGACTACAGTCGCTACGAGTATGGAGTCGATACGTAGCACGCAGAACGATGGGAGCT",
    "CGCCGGACTGCACGACAGTCGACGATGGAGTCGACACGACTCGCGCATACGATGGAGTCGACTACAGTCGCTACGACGATGGAGTCGCGAGCGCTATGAGCGACTATGGAGTCGATACGATACGCGCACGCTATGGAGTCGAGAGCGCGCTCGTCGACTATGGAGTCGCGACTGTACGCACACGCGATGGAGTCGATAGTATGCGTACACGCGATGGAGTCGAGTCGAGACGCTGACGATATGGAGTCGATACGTAGCACGCAGACGATGGGAGCT"
]
results = analyze_sequences(sequences, config="Col1a1")
results.to_df()
```

The supported DataFrame columns are:

- `query`
- `query_len`
- `aligned_query`
- `aligned_ref`
- `scores`
- `mutations`

## Build Your Customized Arrays
```python
from darlinpy import analyze_sequences, AmpliconConfig, build_carlin_config

# Custom amplicon configuration
## Col1a1 array (CA)
## segments = conserved site (13bp) + cut site (7bp)
## pam = PAM (TGG) + linker (4bp)
## the reference is prefix + (segments+pam)x10 + postfix
## the sequencing library contains:
## primer5 + prefix + (segments+pam)x10 + postfix + secondary sequence + primer3
template = {
    "segments" : [
        "GACTGCACGACAGTCGACGA",
        "GACACGACTCGCGCATACGA",
        "GACTACAGTCGCTACGACGA",
        "GCGAGCGCTATGAGCGACTA",
        "GATACGATACGCGCACGCTA",
        "GAGAGCGCGCTCGTCGACTA",
        "GCGACTGTACGCACACGCGA",
        "GATAGTATGCGTACACGCGA",
        "GAGTCGAGACGCTGACGATA",
        "GATACGTAGCACGCAGACGA"
        ],
    "pam" : "TGGAGTC",
    "prefix" : "CGCCG",
    "postfix" : "TGGGAGCT",
    "Primer5" : "GAGCTGTACAAGTAAGCGGC",
    "Primer3" : "CGACTGTGCCTTCTAGTTGC",
    "SecondarySequence" : "AGAATTCTAACTAGAGCTCGCTGATCAGCCT"
}
build_carlin_config(template, output_path="custom_array.json")
```

## Supported Arrays

- `Col1a1`
- `Rosa`
- `Tigre`


## Developers

See [DEVELOPERS.md](DEVELOPERS.md)

## Citation

If you use this tool, please cite the paper:

1. L. Li#, S. Bowling#, H. Lin, D. Chen, S.-W. Wang*, F. D. Camargo*, DARLIN mouse for in vivo lineage tracing at high efficiency and clonal diversity. Nature Protocols, doi: 10.1038/s41596-025-01141-z (2025).

2. L. Li, S. Bowling, S. E. McGeary, Q. Yu, B. Lemke, K. Alcedo, Y. Jia, X. Liu, M. Ferreira, A. M. Klein, S.-W. Wang*, F. D. Camargo*, A mouse model with high clonal barcode diversity for joint lineage, transcriptomic, and epigenomic profiling in single cells. Cell 186, 5183-5199.e22 (2023). 

3. S. Bowling*, D. Sritharan*, F. G. Osorio, M. Nguyen, P. Cheung, 
A. Rodriguez-Fraticelli, S. Patel, W-C. Yuan, Y. Fujiwara, B. E. Li, S. H. Orkin, 
S. Hormoz, F. D. Camargo. "An Engineered CRISPR-Cas9 Mouse Line for 
Simultaneous Readout of Lineage Histories and Gene Expression Profiles 
in Single Cells." Cell (2020), https://doi.org/10.1016/j.cell.2020.04.048 
