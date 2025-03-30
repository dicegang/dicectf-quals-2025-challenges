VERILOG_OUTPUTS := ../verilog/outputs
SIMULATOR := ./src/cli.py

# Pattern rule for running any synthesized circuit
%: $(VERILOG_OUTPUTS)/%.json
	uv run $(SIMULATOR) $< $(ARGS)

.PHONY: clean test

test:
	uv pip install -e .[dev]
	uv run python -m pytest tests/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete 