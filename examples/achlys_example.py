import os
import subprocess
import sys
from models.achlys import *

def main():
    # Get path to MOOSE
    moose_path=os.environ['MOOSE_DIR']

    # Path to executable and inputs
    # Need heat_transfer + reactor so use combined
    module_name="combined"
    app_name=module_name+"-opt"
    app_path=os.path.join(moose_path,"modules",module_name)
    #app_exe=os.path.join(app_path,app_name)
    app_exe="/home/ir-broo2/rds/rds-ukaea-ap001/ir-broo2/LIBRTI/dummy/dummy-opt"

    # Create a factory of available objects from our MOOSE executable
    factory=AchlysFactory(app_exe)

    config_name="achlys_config.json"
    factory.write_config(config_name)

    # Create a boiler plate MOOSE model from a template
    model=AchlysModel(factory)

    # Write out our input file
    input_name="achlys.i"
    model.write(input_name)


if __name__ == "__main__":
    main()
