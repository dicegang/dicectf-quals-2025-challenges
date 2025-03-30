# Makefile for the assembler project: compiles .asm files from ./asm and outputs .hex files to ./bin

ASMDIR = asm
BINDIR = bin
ASM_FILES = $(wildcard $(ASMDIR)/*.asm)
HEX_FILES = $(patsubst $(ASMDIR)/%.asm, $(BINDIR)/%.hex, $(ASM_FILES))

# Debug flag support
DEBUG ?= 0
ifeq ($(DEBUG), 1)
    DEBUG_FLAG = --debug
else
    DEBUG_FLAG =
endif

.PHONY: all clean

all: $(BINDIR) $(HEX_FILES)

$(BINDIR):
	@mkdir -p $(BINDIR)

$(BINDIR)/%.hex: $(ASMDIR)/%.asm assembler.py FORCE
	uv run assembler.py $(DEBUG_FLAG) $< $@

FORCE:

clean:
	rm -rf $(BINDIR) 
	rm -rf __pycache__