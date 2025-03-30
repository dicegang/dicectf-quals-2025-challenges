CC = gcc
CFLAGS = -Oz -s -Wall -Wpedantic -ffunction-sections -fdata-sections -Wl,--gc-sections,--build-id=none

.PHONY: clean build

build: ono

%: %.c
	docker run --rm -u "$(shell id -u):$(shell id -g)" -v "$(CURDIR):/app" -w /app buildpack-deps:bookworm $(CC) $(CFLAGS) $< -o $@
	strip $@

ono4.h: ono4 gen.py
	python gen.py

ono3.h: ono3 gen.py
	python gen.py

ono2.h: ono2 gen.py
	python gen.py

ono3: ono4.h
ono2: ono3.h
ono: ono2.h

clean:
	rm -f ono2 ono3 ono4 ono2.h ono3.h ono4.h