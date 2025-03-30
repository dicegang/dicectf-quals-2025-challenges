.PHONY: all clean

all:
	docker buildx build --output type=local,dest=./ -f qemu.dockerfile .

clean:
	rm -rf qemu-system-x86_64 bios
