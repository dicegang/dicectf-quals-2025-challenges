.PHONY := clean solve

debugalyzer.zip: main dwarf
	zip -9 debugalyzer.zip main dwarf

dwarf: dwarf.c
	gcc dwarf.c -lelf -o dwarf -O1

# Install the flag checker program into `main.orig`
main: main.orig ./gen_elf/Cargo.toml ./gen_elf/src/lib.rs ./gen_elf/src/bin/solve_rev.rs
	RELEASE=1 cargo run --bin solve_rev -- main.orig main

# Empty binary with DWARF enabled
main.orig: main.c
	gcc main.c -o main.orig -gdwarf-4

clean:
	rm -f dwarf main main.orig solved pwned
	cargo clean

# Patches the binary to evaluate with the correct flag for testing
solved: main.orig ./gen_elf/Cargo.toml ./gen_elf/src/lib.rs ./gen_elf/src/bin/solve_rev.rs
	cargo run --bin solve_rev -- main.orig solved

# Patches the binary to evaluate with the correct flag for testing
pwned: main.orig dwarf ./gen_elf/Cargo.toml ./gen_elf/src/lib.rs ./gen_elf/src/bin/solve_pwn.rs
	cargo run --bin solve_pwn -- main.orig pwned dwarf

# Uses z3 to solve the actual binary
solve: main
	cargo run --bin solve -- ./main
