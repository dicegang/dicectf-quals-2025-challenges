# Dynamically load synthesis types from options directory
# Strip _map.v and .v from filenames to get unique types
TYPES := $(sort $(patsubst %_map.v,%,$(patsubst %.v,%,$(notdir $(wildcard verilog/options/*.v)))))

.PHONY: all clean test verilog simulator bioarm debugger

all: verilog test

# Run all Verilog synthesis
verilog:
	$(MAKE) -C verilog 

# Run simulator tests
test:
	$(MAKE) -C simulator test

# Clean everything
clean:
	$(MAKE) -C verilog clean
	$(MAKE) -C simulator clean
	$(MAKE) -C bioarm clean
	$(MAKE) -C assembler clean

# Debug target to show available types
show-types:
	@echo "Available synthesis types:"
	@echo "$(TYPES)"

bioarm_proto:
	$(MAKE) -C bioarm proto

# Run bioarm server
bioarm: bioarm_proto
	$(MAKE) -C bioarm

run_all: verilog 
	$(MAKE) -C assembler
	uv run prepare.py
	cd ./dist/biosim && uv run run_debug.py --experiment ./experiments/chall1.json --input_b64 "$(INPUT)"

run_good: verilog 
	$(MAKE) -C assembler
	uv run prepare.py
	cd ./dist/biosim && uv run run_debug.py --experiment ./experiments/debug_good.json --input_b64 "$(INPUT)"

# Run debugger with specified hex file
# Usage: make debugger HEX=path/to/file.hex CYCLES=10
debugger: verilog bioarm_proto
	$(MAKE) -C assembler
	@if [ -z "$(HEX)" ]; then \
		echo "Error: HEX file path not specified. Usage: make debugger HEX=path/to/file.hex [CYCLES=N] [AUTO=1]"; \
		exit 1; \
	fi
	@CYCLES=$${CYCLES:-1000}; \
	HEXPATH=$$(realpath $(HEX)); \
	cd bioarm_test && uv run debugger.py $$HEXPATH $$CYCLES $(if $(AUTO),--auto,)
	