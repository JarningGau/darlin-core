# Developer Overview

This repository is maintained as a Python library, not as a supported CLI tool. The stable user-facing API is the top-level `darlinpy` package, especially `analyze_sequences`, `AmpliconConfig`, and `build_carlin_config`.

## Support Boundary

- The maintained user interface is the Python library API.
- Internal submodules may change unless they are explicitly re-exported from `darlinpy`.
- `bin/` is legacy/internal and should not be documented as a supported user entry point.

## Verification

Run the main test suite:

```bash
conda run -n darlinpy-test python -m pytest -q
```

Run the maintained quality checks:

```bash
pixi run quality
```

## Compatibility Matrix

Compatibility jobs remain in `tox`:

```bash
tox -e py39-max
tox -e py311-min
tox -e py311-max
tox -e py312-max
```

If the matching interpreter is not installed locally, `pixi` can provide one without changing repository layout:

```bash
pixi exec -s python=3.8 -s tox tox -e py38-min
pixi exec -s python=3.11 -s tox tox -e py311-min
pixi exec -s python=3.11 -s tox tox -e py311-max
pixi exec -s python=3.12 -s tox tox -e py312-max
```

## Build Notes

The compiled extension in `darlinpy/alignment/_cas9_align.cpp` is required. If you need to rebuild it manually:

```bash
python setup.py build_ext --inplace
```
