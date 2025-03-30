.PHONY: all clean

TYPES := all_nor dff_nor
CIRCUIT_FILES := $(wildcard circuits/*.v)
OUTPUT_FILES := $(foreach type,$(TYPES),$(patsubst circuits/%.v,outputs/%_$(type).json,$(CIRCUIT_FILES)) \
                                      $(patsubst circuits/%.v,outputs/%_$(type)_final.json,$(CIRCUIT_FILES)))

all: outputs $(OUTPUT_FILES)

outputs:
	mkdir -p outputs

$(OUTPUT_FILES): $(CIRCUIT_FILES)
	for type in $(TYPES); do \
		echo "\nSynthesizing $$type circuits..."; \
		uv run synth.py ./circuits $$type; \
	done

clean:
	rm -rf outputs/
	rm -f synth.ys 