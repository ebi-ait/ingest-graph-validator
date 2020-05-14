#!/bin/sh
# Generate graph_test_set/README.md document with updated tests and add it to commit.

python3 .readme/update_test_index.py
git add graph_test_set/README.md
