FROM ubuntu:24.04 AS build

ARG KVER=6.13.8

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq --no-install-recommends \
		bc bison build-essential cpio flex libelf-dev libssl-dev python3 \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /build
ADD https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KVER}.tar.xz /build/
RUN tar -xf linux-${KVER}.tar.xz && mv linux-${KVER} linux
WORKDIR /build/linux
COPY kconfig .config
COPY af_unix.c.patch .
RUN sed -i '0,/BUG/s/BUG/\/\/BUG/' net/socket.c
RUN sed -i '0,/gets/{/gets/s/^/__attribute__((no_stack_protector)) /}' net/socket.c
RUN patch -p1 < af_unix.c.patch
RUN make -j$(nproc)

FROM scratch AS export
COPY --from=build /build/linux/arch/x86/boot/bzImage /
