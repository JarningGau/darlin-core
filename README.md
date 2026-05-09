# darlinpy

`darlinpy` is a library-only Python package for DARLIN/CARLIN sequence analysis. It aligns edited lineage-tracing amplicons to locus-specific references, calls dominant alleles, and converts edits into HGVS-like mutation annotations.

## Support Boundary

- Supported interface: top-level Python imports such as `darlinpy.analyze_sequences`, `darlinpy.AmpliconConfig`, and `darlinpy.build_carlin_config`
- Internal modules are implementation details unless they are explicitly re-exported from `darlinpy`
- `bin/` is legacy/internal and is not part of the supported user interface

## Installation

The package requires the compiled C++ extension in `darlinpy/alignment/_cas9_align.cpp`.

```bash
pip install -e .
python -c "from darlinpy.alignment.cas9_align import HAS_CPP_IMPL; assert HAS_CPP_IMPL is True"
```

For local quality checks, this repository uses `pixi`:

```bash
pixi run quality
```

## Minimal Example

```python
from darlinpy import analyze_sequences
from darlinpy.config.amplicon_configs import load_carlin_config_by_locus

reference = load_carlin_config_by_locus("Col1a1").get_full_reference_sequence()
result = analyze_sequences([reference], config="Col1a1", method="exact")
print(result.to_df())
```

The supported DataFrame columns are:

- `query`
- `query_len`
- `aligned_query`
- `aligned_ref`
- `scores`
- `mutations`

Empty mutation results are reported as empty strings.

## Supported Arrays

- `Col1a1`
- `Rosa`
- `Tigre`

## Developer Verification

Run the full test suite in the existing development environment:

```bash
conda run -n darlinpy-test python -m pytest -q
```

Run the maintained lint + test workflow:

```bash
pixi run quality
```

## Citation

If you use this package, cite the DARLIN/CARLIN literature appropriate for your analysis workflow.
