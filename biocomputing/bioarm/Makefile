.PHONY: all clean proto run

all: run

# Generate Python code from proto file
proto:
	uv run -m grpc_tools.protoc \
		-I. \
		--python_out=. \
		--grpc_python_out=. \
		bioarm.proto

# Clean generated files
clean:
	rm -f bioarm_pb2.py bioarm_pb2_grpc.py
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf .venv

# Run the server
run: proto
	uv run bioarm.py