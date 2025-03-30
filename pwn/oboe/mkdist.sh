#!/bin/bash
BASE=$(basename "$(pwd)")
FILES=(
	"Dockerfile"
	"Makefile"
	"bzImage"
	"kconfig"
	"linux.dockerfile"
	"af_unix.c.patch"
	"run"
)
DIST=$(for FILE in "${FILES[@]}"; do echo "$BASE/$FILE"; done)
cd ..
tar -czf "$BASE/dist.tar.gz" $DIST \
	--transform="s|initramfs.dist|$BASE/initramfs.cpio.gz|" -C "$BASE" initramfs.dist
