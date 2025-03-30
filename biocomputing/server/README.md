# BioARM HTTP Server

This is a FastAPI-based HTTP server that provides a REST API interface to the BioARM gRPC service.

## Setup

1. Make sure you have Python 3.8+ installed
2. Install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

## Running the Server

1. First, make sure the BioARM gRPC server is running (should be on port 50051)
2. Run the HTTP server:
   ```bash
   python main.py
   ```
   The server will start on port 8000.

## API Endpoints

### Initialize System
- **POST** `/initialize`
- Request body:
  ```json
  {
    "sbml_string": "string"  // Raw SBML string
  }
  ```
- Response:
  ```json
  {
    "success": true,
    "error_message": ""  // Populated if success is false
  }
  ```

### Pipette In
- **POST** `/pipette`
- Request body:
  ```json
  {
    "species": ["string"],  // List of species to pipette in
    "scavengers": ["string"]  // Optional list of scavengers
  }
  ```

### Delay
- **POST** `/delay`
- Request body:
  ```json
  {
    "seconds": 0.0  // Duration to delay
  }
  ```

### Read Out
- **POST** `/readout`
- Request body:
  ```json
  {
    "species": ["string"]  // List of species to read concentrations for
  }
  ```
- Response:
  ```json
  {
    "concentrations": {
      "species_name": 0.0  // Mapping of species to concentrations
    }
  }
  ```

## Interactive Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 