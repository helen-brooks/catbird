import os
import subprocess
import sys
from models.monoblock import *

def main():
    # Path to executable
    app_exe="../app/dummy-opt"

    # Create a factory of available objects from our MOOSE executable
    factory=MonoblockFactory(app_exe)

    config_name="monoblock_config.json"
    factory.write_config(config_name)

    # Create a boiler plate MOOSE model from a template
    model=MonoblockModel(factory)

    # Write out our input file
    input_name="monoblock_thermal.i"
    model.write(input_name)

    # Run
    args=[app_exe,'-i',input_name]
    moose_process=subprocess.Popen(args)
    stream_data=moose_process.communicate()[0]
    retcode=moose_process.returncode

    # Return moose return code
    sys.exit(retcode)


if __name__ == "__main__":
    main()
