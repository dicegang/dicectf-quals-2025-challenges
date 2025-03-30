FROM ubuntu:22.04 AS build

ARG COMMIT=0f15892acaf3f50ecc20c6dad4b3ebdd701aa93e

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq --no-install-recommends \
		build-essential ca-certificates git libglib2.0-dev python3-tomli \
		libfdt-dev libpixman-1-dev zlib1g-dev ninja-build python3-venv \
	&& rm -rf /var/lib/apt/lists/*

RUN git clone https://gitlab.com/qemu-project/qemu.git /qemu
WORKDIR /qemu
COPY intel-hda.c.patch .
RUN git checkout $COMMIT && git apply intel-hda.c.patch
RUN ./configure --prefix=/usr/local --target-list=x86_64-softmmu && \
	make -j$(nproc) && make install

FROM scratch AS export
COPY --from=build /usr/local/bin/qemu-system-x86_64 /
ARG P=/usr/local/share/qemu
COPY --from=build $P/bios-256k.bin $P/efi-e1000.rom $P/kvmvapic.bin \
	$P/vgabios-stdvga.bin $P/linuxboot_dma.bin /bios/
