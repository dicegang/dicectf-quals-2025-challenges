#!/bin/sh
cp -r challenge glail
tar --owner="strell" --group="strell" -H v7 --no-xattr --mtime=1970-01-01T00:00Z -czvf glail.tar.gz glail
rm -rf glail
