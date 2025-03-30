import grpc
import sys
import os

# Add the bioarm directory to the Python path to import the generated protobuf files
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'bioarm'))

import bioarm_pb2
import bioarm_pb2_grpc

def run_test():
    # Create a channel to the server
    with grpc.insecure_channel('localhost:50051') as channel:
        # Create a stub (client)
        stub = bioarm_pb2_grpc.BioArmStub(channel)
        
        # Test 1: Initialize System
        print("\n=== Testing InitializeSystem ===")
        sbml_model = """
        <?xml version="1.0" encoding="UTF-8"?>
        <sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
            <model id="simple_model">
                <listOfCompartments>
                    <compartment id="cell" size="1"/>
                </listOfCompartments>
                <listOfSpecies>
                    <species id="A" compartment="cell" initialConcentration="0"/>
                    <species id="B" compartment="cell" initialConcentration="0"/>
                </listOfSpecies>
                <listOfReactions>
                    <reaction id="r1" reversible="false">
                        <listOfReactants>
                            <speciesReference species="A" stoichiometry="1"/>
                        </listOfReactants>
                        <listOfProducts>
                            <speciesReference species="B" stoichiometry="1"/>
                        </listOfProducts>
                        <kineticLaw>
                            <math xmlns="http://www.w3.org/1998/Math/MathML">
                                <apply>
                                    <times/>
                                    <ci>k1</ci>
                                    <ci>A</ci>
                                </apply>
                            </math>
                            <listOfLocalParameters>
                                <localParameter id="k1" value="0.1"/>
                            </listOfLocalParameters>
                        </kineticLaw>
                    </reaction>
                </listOfReactions>
            </model>
        </sbml>
        """
        response = stub.InitializeSystem(bioarm_pb2.InitializeRequest(sbml_string=sbml_model))
        print(f"Initialize response: success={response.success}, error={response.error_message}")

        # Test 2: Pipette In
        print("\n=== Testing PipetteIn ===")
        response = stub.PipetteIn(bioarm_pb2.PipetteRequest(species=["A"]))
        print("Pipetted in species A")

        # Test 3: Delay
        print("\n=== Testing Delay ===")
        response = stub.Delay(bioarm_pb2.DelayRequest(seconds=1.0))
        print("Delayed for 1 second")

        # Test 4: ReadOut
        print("\n=== Testing ReadOut ===")
        response = stub.ReadOut(bioarm_pb2.ReadOutRequest(species=["A", "B"]))
        print("Concentrations:")
        for species, concentration in response.concentrations.items():
            print(f"{species}: {concentration}")

if __name__ == '__main__':
    run_test()
