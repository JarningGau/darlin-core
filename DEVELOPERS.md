# Developer Overview

This repo is a Python package for DARLIN/CARLIN amplicon analysis: it aligns edited CRISPR lineage-tracing sequences to a locus-specific reference, calls a dominant allele, and converts edits into HGVS-like mutation annotations. The public entry point is `analyze_sequences()` in `darlinpy/api.py`, with top-level exports from `darlinpy/__init__.py`. Installation uses `setuptools` with a `pyproject.toml` build backend; the `pybind11` C++ extension in `darlinpy/alignment/_cas9_align.cpp` is a required part of the packaged distribution rather than an optional speedup. In a local `venv`, `pip install -e .` should build the extension automatically, and `darlinpy.alignment.cas9_align.HAS_CPP_IMPL` should be `True` after a successful install.

The code is organized around four main layers. Config loading lives in `darlinpy/config/amplicon_configs.py` and JSON templates under `darlinpy/config/data`, which define the CARLIN array structure and position-specific gap penalties for `Col1a1`, `Rosa`, and `Tigre`. Alignment lives in `darlinpy/alignment/carlin_aligner.py` and `darlinpy/alignment/aligned_seq.py`; it produces motif-aware aligned objects and applies sanitization for likely sequencing/PCR artifacts. Allele calling is in `darlinpy/calling/allele_caller.py`, with both `exact` and `coarse_grain` strategies. Mutation extraction and HGVS-style formatting are in `darlinpy/mutations/mutation.py`.

For developers, the likely paths are:

- Use the library API from `darlinpy/api.py` if you want sequence-in, dataframe-out analysis.
- Add new array designs with `darlinpy/utils/build_config.py` plus a JSON config.
- Use `bin/run_DARLIN_bulk.py` for an end-to-end bulk FASTQ workflow; it wraps PEAR assembly, UMI handling, barcode extraction, and then calls `darlinpy`.
- Look at `examples/` for usage patterns and `tests/` for expected behavior.

A few practical notes: the repo is partly polished as a library and partly still research-tool style. There are build artifacts and local env directories checked in, test/docstrings are mixed English/Chinese, and some modules print directly to stdout during normal object construction. This description is based on reading the code and package layout.

## Compatibility Testing

The project officially supports Python 3.8 through 3.11. Compatibility CI also runs one exploratory Python 3.12 job as non-blocking signal only.

The required compatibility jobs are:

- `py38-min`
- `py39-max`
- `py311-min`
- `py311-max`

The exploratory compatibility job is:

- `py312-max`

`py38-min` uses the declared runtime floor from `requirements-min-py38.txt`.
`py311-min` uses the earliest dependency set that still supports Python 3.11 from `requirements-min-py311.txt`.
`max` means the latest versions resolved by `pip` at test time.

Run a local compatibility job with `tox`:

```bash
tox -e py39-max
tox -e py311-min
tox -e py311-max
tox -e py312-max
```

If the matching interpreter is not installed locally, `pixi` can provide a temporary one without changing the repo layout:

```bash
pixi exec -s python=3.8 -s tox tox -e py38-min
pixi exec -s python=3.11 -s tox tox -e py311-min
pixi exec -s python=3.11 -s tox tox -e py311-max
pixi exec -s python=3.12 -s tox tox -e py312-max
```
