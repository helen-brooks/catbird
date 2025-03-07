from catbird import *
import os
import subprocess
import sys
from models.simple_breeder import *

def main():
    # Path to executable to obtain available syntax
    app_exe="../app/dummy-opt"

    # Custom factory of enabled MOOSE syntax
    factory=SimpleBreederFactory(app_exe)

    # Optionally, dump of all syntax we "pythonized" to json file
    config_name="config_simple_breeder.json"
    factory.write_config(config_name)
    
    # Custom data structure to bundle all in default inputs
    inputs=SimpleBreederInputs()

    # Update some material properties
    # Value for Eurofer steel: Esteban et al 2007
    inputs.materials["steel"].D0=4.57e-7 # m^2/2 J/mol
    inputs.materials["steel"].E_d=22300 # J/(mol K)

    # Values for LiAlO2: Roy et al 2024 
    inputs.materials["breeder"].D0=1.56e-08  # m^2/2 J/mol
    inputs.materials["breeder"].E_d=45680 # J/(mol K)
    
    # Custom MOOSE boilerplate model
    model=SimpleBreederModel(factory,inputs)

    # Update the model

    # Write out model to input file
    input_name="simple_breeder.i"
    model.write(input_name)

    # Run the model
    args=[app_exe,'-i',input_name]
    moose_process=subprocess.Popen(args)
    stream_data=moose_process.communicate()[0]
    retcode=moose_process.returncode

    # Return moose return code
    sys.exit(retcode)

if __name__ == "__main__":
    main()

