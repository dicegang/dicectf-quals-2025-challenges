FROM ubuntu:22.04 AS app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq --no-install-recommends \
		libpixman-1-dev libfdt-dev libglib2.0-dev \
	&& rm -rf /var/lib/apt/lists/*

FROM pwn.red/jail

COPY --from=app / /srv
COPY bzImage qemu-system-x86_64 run \
	initramfs.cpio.gz bios flag.txt /srv/app/
RUN chmod 755 /srv/app/run

ENV JAIL_TIME=400 JAIL_CPU=2000 JAIL_PIDS=50 JAIL_MEM=2G
