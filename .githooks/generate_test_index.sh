#!/bin/sh
# Generate graph_test_set/README.md document with updated tests and add it to commit.
if git diff --name-only --cached | grep -Eq '*.adoc$'; then
  python3 .readme/update_test_index.py
  git add graph_test_set/README.md
fi

