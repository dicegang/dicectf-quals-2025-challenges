#!/bin/bash

# Create sequence and convert to base64
SEQ="ESNSDPCAEEIUMDTUAERH"
INPUT=$(printf "%s" "${SEQ:0:8}" | base64)

echo "Base64 input: $INPUT"

make run_all INPUT="${INPUT}"