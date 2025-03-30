import grpc
from concurrent import futures
import logging
import time
import gzip
import base64

# These imports will be available after running the protoc compiler
import bioarm_pb2
import bioarm_pb2_grpc

import roadrunner
from roadrunner import Config
Config.setValue(Config.LLVM_BACKEND, Config.LLJIT)
Config.setValue(Config.LLJIT_OPTIMIZATION_LEVEL, Config.NONE)
Config.setValue(Config.LOADSBMLOPTIONS_MUTABLE_INITIAL_CONDITIONS, False)


FIDELITY = 20

class BioArmServicer(bioarm_pb2_grpc.BioArmServicer):
    def __init__(self):
        self.rr = None
        self.t = 0

    def InitializeSystem(self, request, context):
        """Initialize the system with an SBML model (gzipped and base64 encoded)"""
        logging.info("Initializing system with SBML model")
        try:
            # Decode base64 and decompress gzip
            compressed_sbml = base64.b64decode(request.sbml_string)
            sbml_string = gzip.decompress(compressed_sbml).decode('utf-8')
            
            self.rr = roadrunner.RoadRunner()
            self.rr.load(sbml_string)
            self.rr.setIntegrator('cvode')
            # self.rr.getIntegrator().setValue('relative_tolerance', 1e-6)
            # self.rr.getIntegrator().setValue('absolute_tolerance', 1e-12)
            self.rr.getIntegrator().setValue("stiff", False)
            return bioarm_pb2.InitializeResponse(
                success=True,
                error_message=""
            )
        except Exception as e:
            logging.error(f"Error in InitializeSystem: {str(e)}", exc_info=True)
            return bioarm_pb2.InitializeResponse(
                success=False,
                error_message=str(e)
            )

    def PipetteIn(self, request, context):
        """Add species via pipette"""
        logging.info(f"Pipetting in species: {request}")
        try:
            self.rr.setValue('[p_0]', 0)
            for species in request.species:
                self.rr.setValue(f'[{species}]', 10)
            for scavenger in request.scavengers:
                self.rr.setValue(f'[{scavenger}]', 0)
            return bioarm_pb2.Empty()
        except Exception as e:
            logging.error(f"Error in PipetteIn: {str(e)}", exc_info=True)
            raise

    def Delay(self, request, context):
        """Wait for specified duration"""
        logging.info(f"Delaying for {request.seconds} seconds")
        try:
            self.conc = self.rr.simulate(self.t, self.t + request.seconds, int(request.seconds * FIDELITY))
            self.t += request.seconds
            return bioarm_pb2.Empty()
        except Exception as e:
            logging.error(f"Error in Delay: {str(e)}", exc_info=True)
            raise

    def ReadOut(self, request, context):
        """Read concentrations of specified species"""
        logging.info(f"Reading concentrations for species: {request.species}")
        # concentrations = {
        #     species: self.rr.getValue(f'[{species}]') for species in request.species
        # }
        concentrations = {
            species: self.conc[f'[{species}]'][-1] for species in request.species
        }
        return bioarm_pb2.ReadOutResponse(
            concentrations=concentrations
        )
    
    def ReadFull(self, request, context):
        """Read the full concentration history since last delay for specified species"""
        logging.info(f"Reading full concentration history for species: {request.species}")
        history = {}
        for species in request.species:
            species_history = bioarm_pb2.SpeciesHistory(
                concentrations=self.conc[f'[{species}]'].tolist()
            )
            history[species] = species_history
        return bioarm_pb2.ReadFullResponse(
            history=history
        )

def serve():
    # Create a gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    # Add the servicer to the server
    bioarm_pb2_grpc.add_BioArmServicer_to_server(
        BioArmServicer(), server
    )
    
    # Listen on port 50051
    server.add_insecure_port('[::]:50051')
    server.start()
    
    logging.info("BioArm gRPC server started on port 50051")
    
    try:
        while True:
            time.sleep(86400)  # One day in seconds
    except KeyboardInterrupt:
        server.stop(0)
        logging.info("Server stopped")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    serve() 
