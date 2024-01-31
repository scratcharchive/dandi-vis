#!/bin/bash

set -e

# check that DENDRO_API_KEY is set
if [ -z "$DENDRO_API_KEY" ]; then
  echo "DENDRO_API_KEY is not set"
  exit 1
fi

python dandisets/000582/run.py
