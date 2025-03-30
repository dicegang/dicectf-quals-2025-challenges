FROM ubuntu:22.04 AS app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -yq --no-install-recommends \
		qemu-system-x86 \
	&& rm -rf /var/lib/apt/lists/*

FROM pwn.red/jail

COPY --from=app / /srv
COPY run /srv/app/run
COPY initramfs.cpio.gz bzImage /srv/app/
RUN chmod 755 /srv/app/run

ENV JAIL_TIME=300 JAIL_CPU=2000 JAIL_PIDS=20 JAIL_MEM=256M
