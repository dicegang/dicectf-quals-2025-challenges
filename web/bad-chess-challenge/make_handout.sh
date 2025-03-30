#!/bin/sh
rm -f bad-chess-challenge.tar.gz
tar --exclude='.DS_Store' --owner="root" --group="root" -H v7 --no-xattr --mtime=1970-01-01T00:00Z -czvf bad-chess-challenge.tar.gz -C handout .
