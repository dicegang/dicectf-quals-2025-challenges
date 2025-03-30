#!/bin/bash

# Exit on any error
set -e

tar --exclude='*debug*' --exclude='.venv' -czf dist.tar.gz -C ./dist .
tar -tvf dist.tar.gz | grep -i "debug" && { echo "Debug files found!"; exit 1; }

rm -rf dist-testing
mkdir dist-testing
cp dist.tar.gz dist-testing/
cd dist-testing && tar -xzf dist.tar.gz && cd ..

echo "Archive created and extracted in dist-testing/"
tree -a dist-testing/