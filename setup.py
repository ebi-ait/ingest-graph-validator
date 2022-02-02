from setuptools import setup, find_packages

setup(
    name="ingest-graph-validator",
    version="0.1.0",
    packages=find_packages(include=["ingest_graph_validator", "ingest_graph_validator.*"]),
    entry_points={
        "console_scripts": [
            "ingest-graph-validator = ingest_graph_validator.ingest_graph_validator:entry_point"
        ]
    },
)
