"""
vn.py - By Traders, For Traders.

The vn.py project is an open-source quantitative trading framework
that is developed by traders, for traders.

The project is mainly written in Python and uses C++ for low-layer
and performance sensitive infrastructure.

Using the vn.py project, institutional investors and professional
traders, such as hedge funds, prop trading firms and investment banks,
can easily develop complex trading strategies with the Event Engine
Strategy Module, and automatically route their orders to the most
desired destinations, including equity, commodity, forex and many
other financial markets.
"""

import ast
import os
import platform
import re
import sys

from setuptools import Extension, find_packages, setup


def gather_autocxxpy_generated_files(root: str):
    fs = [os.path.join(root, "module.cpp")]
    for root, dirs, filenames in os.walk(root):
        for filename in filenames:
            filebase, ext = os.path.splitext(filename)
            if ext == ".cpp" and filebase.startswith("generated_functions_"):
                path = os.path.join(root, filename)
                fs.append(path)
    return fs

def get_install_requires():
    install_requires = [
        "PyQt5",
        "qdarkstyle",
        "requests",
        "websocket-client",
        "mongoengine",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "rqdatac",
        "ta-lib",
        "deap"
    ]
    if sys.version_info.minor < 7:
        install_requires.append("dataclasses")
    return install_requires


def get_version_string():
    global version
    with open("vnpy/__init__.py", "rb") as f:
        version_line = re.search(
            r"__version__\s+=\s+(.*)", f.read().decode("utf-8")
        ).group(1)
        return str(ast.literal_eval(version_line))

parallel = os.environ.get('VNPY_BUILD_PARALLEL', None)
if parallel:
    if parallel == 'auto':
        parallel = os.cpu_count()
    if parallel != 'no':
        from ci.parallel_build_distutils import patch_distutils

        patch_distutils(int(parallel))

setup(
    name="vnpy",
    version=get_version_string(),
    author="vn.py team",
    author_email="vn.py@foxmail.com",
    license="MIT",
    url="https://www.vnpy.com",
    description="A framework for developing quant trading systems.",
    long_description=__doc__,
    keywords='quant quantitative investment trading algotrading',
    include_package_data=True,
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"": [
        "*.ico",
        "*.ini",
        "*.dll",
        "*.so",
        "*.pyd",
    ]},
    install_requires=get_install_requires(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Operating System :: Microsoft :: Windows :: Windows 7",
        "Operating System :: Microsoft :: Windows :: Windows 8",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows Server 2008",
        "Operating System :: Microsoft :: Windows :: Windows Server 2012",
        "Operating System :: Microsoft :: Windows :: Windows Server 2012",
        "Operating System :: POSIX :: Linux"
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: Implementation :: CPython",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Chinese (Simplified)",
        "Natural Language :: Chinese (Simplified)"
    ],
    ext_modules=[],
)
