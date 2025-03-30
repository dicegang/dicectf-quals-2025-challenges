.PHONY: all clean

all:
	docker buildx build --output type=local,dest=./ -f linux.dockerfile .

clean:
	rm -rf bzImage
