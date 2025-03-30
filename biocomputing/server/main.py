from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import grpc
import sys
import os
import gzip
import base64

# Add bioarm directory to path so we can import the generated protobuf files
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bioarm'))
import bioarm_pb2
import bioarm_pb2_grpc

app = FastAPI(title="BioARM HTTP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class InitializeRequest(BaseModel):
    sbml_string: str

class InitializeResponse(BaseModel):
    success: bool
    error_message: str = ""

class PipetteRequest(BaseModel):
    species: List[str]
    scavengers: Optional[List[str]] = []

class DelayRequest(BaseModel):
    seconds: float

class ReadOutRequest(BaseModel):
    species: List[str]

class ReadOutResponse(BaseModel):
    concentrations: Dict[str, float]

# Create gRPC channel and stub
channel = grpc.insecure_channel('localhost:50051')
stub = bioarm_pb2_grpc.BioArmStub(channel)

@app.post("/initialize", response_model=InitializeResponse)
async def initialize_system(request: InitializeRequest):
    try:
        # Compress and encode SBML string
        compressed = gzip.compress(request.sbml_string.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('utf-8')
        
        # Call gRPC service
        response = stub.InitializeSystem(
            bioarm_pb2.InitializeRequest(sbml_string=encoded)
        )
        return InitializeResponse(
            success=response.success,
            error_message=response.error_message
        )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pipette", status_code=200)
async def pipette_in(request: PipetteRequest):
    try:
        stub.PipetteIn(
            bioarm_pb2.PipetteRequest(
                species=request.species,
                scavengers=request.scavengers or []
            )
        )
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/delay", status_code=200)
async def delay(request: DelayRequest):
    try:
        stub.Delay(bioarm_pb2.DelayRequest(seconds=request.seconds))
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/readout", response_model=ReadOutResponse)
async def read_out(request: ReadOutRequest):
    try:
        response = stub.ReadOut(
            bioarm_pb2.ReadOutRequest(species=request.species)
        )
        return ReadOutResponse(concentrations=response.concentrations)
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 