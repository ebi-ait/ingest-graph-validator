from os import path

from setuptools import setup, find_packages

# Required packages to install.
base_dir = path.dirname(__file__)
install_requires = [line.rstrip() for line in open(path.join(base_dir, 'requirements.txt'))]

setup_requirements = ["pytest-runner", ]

test_requirements = ["pytest>=3", ]

setup(
    name="ingest-graph-validator",
    version="1.0.1",
    python_requires=">=3.10",
    packages=find_packages(include=["ingest_graph_validator", "ingest_graph_validator.*"]),
    description="HCA Ingest Service neo4j graph validator package",
    entry_points={
        "console_scripts": [
            "ingest-graph-validator = ingest_graph_validator.ingest_graph_validator:entry_point"
        ]
    },
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements
)
