# Developer Overview

This repo is a Python package for DARLIN/CARLIN amplicon analysis: it aligns edited CRISPR lineage-tracing sequences to a locus-specific reference, calls a dominant allele, and converts edits into HGVS-like mutation annotations. The public entry point is `analyze_sequences()` in `darlinpy/api.py`, with top-level exports from `darlinpy/__init__.py`. Installation uses `setuptools` with a `pyproject.toml` build backend; the `pybind11` C++ extension in `darlinpy/alignment/_cas9_align.cpp` is a required part of the packaged distribution rather than an optional speedup. In a local `venv`, `pip install -e .` should build the extension automatically, and `darlinpy.alignment.cas9_align.HAS_CPP_IMPL` should be `True` after a successful install.

The code is organized around four main layers. Config loading lives in `darlinpy/config/amplicon_configs.py` and JSON templates under `darlinpy/config/data`, which define the CARLIN array structure and position-specific gap penalties for `Col1a1`, `Rosa`, and `Tigre`. Alignment lives in `darlinpy/alignment/carlin_aligner.py` and `darlinpy/alignment/aligned_seq.py`; it produces motif-aware aligned objects and applies sanitization for likely sequencing/PCR artifacts. Allele calling is in `darlinpy/calling/allele_caller.py`, with both `exact` and `coarse_grain` strategies. Mutation extraction and HGVS-style formatting are in `darlinpy/mutations/mutation.py`.

For developers, the likely paths are:

- Use the library API from `darlinpy/api.py` if you want sequence-in, dataframe-out analysis.
- Add new array designs with `darlinpy/utils/build_config.py` plus a JSON config.
- Use `bin/run_DARLIN_bulk.py` for an end-to-end bulk FASTQ workflow; it wraps PEAR assembly, UMI handling, barcode extraction, and then calls `darlinpy`.
- Look at `examples/` for usage patterns and `tests/` for expected behavior.

A few practical notes: the repo is partly polished as a library and partly still research-tool style. There are build artifacts and local env directories checked in, test/docstrings are mixed English/Chinese, and some modules print directly to stdout during normal object construction. This description is based on reading the code and package layout.
