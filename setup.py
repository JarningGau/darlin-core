#!/usr/bin/env python3
"""
DARLIN Python - CARLIN sequence analysis toolkit
"""

from pathlib import Path

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent


def get_version() -> str:
    init_py = ROOT / "darlinpy" / "__init__.py"
    for line in init_py.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Unable to determine darlinpy version from darlinpy/__init__.py")


def get_long_description() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


setup(
    name="darlinpy",
    version=get_version(),
    author="JarningGau",
    author_email="jarninggau@gmail.com",
    description="Python implementation of CARLIN sequence analysis tools",
    license="MIT",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/jarninggau/darlinpy",
    packages=find_packages(include=["darlinpy", "darlinpy.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "mypy>=0.900",
            "pybind11>=2.10",
        ],
        "viz": [
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    # Ensure CARLIN configuration JSON files are installed with the package
    # The patterns are relative to the "darlinpy.config" package directory.
    package_data={
        "darlinpy.config": ["data/*.json"],
    },
    ext_modules=[
        Pybind11Extension(
            "darlinpy.alignment._cas9_align",
            ["darlinpy/alignment/_cas9_align.cpp"],
            cxx_std=17,
        )
    ],
    cmdclass={"build_ext": build_ext},
)
