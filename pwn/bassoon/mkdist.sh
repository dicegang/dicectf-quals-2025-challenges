#!/bin/bash
BASE=$(basename "$(pwd)")
FILES=(
	"Dockerfile"
	"Makefile"
	"bzImage"
	"intel-hda.c.patch"
	"qemu.dockerfile"
	"qemu-system-x86_64"
	"initramfs.cpio.gz"
	"bios"
	"run"
)
DIST=$(for FILE in "${FILES[@]}"; do echo "$BASE/$FILE"; done)
cd ..
tar -czf "$BASE/dist.tar.gz" $DIST
