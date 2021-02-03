#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from os import path

from setuptools import setup, find_packages


# Required packages to install.
requirements = [line.rstrip() for line in open(path.join(path.dirname(__file__), 'requirements.txt'))]

setup_requirements = ["pytest-runner", ]

test_requirements = ["pytest>=3", ]

# Description from readme.
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    author="Javier Ferrer Gómez",
    author_email="jferrer@ebi.ac.uk",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="HCA Ingest Service neo4j graph validator package",
    entry_points={
        'console_scripts': [
            "ingest-graph-validator=ingest_graph_validator.ingest_graph_validator:entry_point",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="ingest-graph-validator",
    name="ingest-graph-validator",
    packages=find_packages(include=["ingest_graph_validator", "ingest_graph_validator.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ebi-ait/ingest-graph-validator",
    version="0.6.3",
    zip_safe=False,
)
