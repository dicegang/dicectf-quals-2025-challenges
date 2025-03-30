resort: resort.c
	clang -Wl,-z,relro,-z,now resort.c -O2 -o resort

clean:
	rm -rf resort

all: resort
.PHONY: clean
