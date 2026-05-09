#!/usr/bin/env python3

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup


setup(
    ext_modules=[
        Pybind11Extension(
            "darlinpy.alignment._cas9_align",
            ["darlinpy/alignment/_cas9_align.cpp"],
            cxx_std=17,
        )
    ],
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
)
