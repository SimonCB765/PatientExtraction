"""Code to initiate the generating of the flat file representations of the QICKD data set."""

# Python imports.
import os
import sys

# User imports.
if __package__ == "GenerateDataFiles":
    # If the package is GenerateDataFiles, then relative imports are needed.
    from . import generate_flat_files
else:
    # The code was not called from within the Code directory using 'python -m GenerateDataFiles'.
    # Therefore, we need to add the top level Code directory to the search path and use absolute imports.
    currentDir = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
    codeDir = os.path.abspath(os.path.join(currentDir, os.pardir))
    sys.path.append(codeDir)
    from GenerateDataFiles import generate_flat_files


# Determine the default configuration file to use.
codeDir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
configDir = os.path.join(codeDir, "ConfigFiles")
defaultConfigFile = os.path.join(configDir, "FlatFileGenerationConfig.json")

configFile = defaultConfigFile if len(sys.argv) < 2 else sys.argv[1]
generate_flat_files.main(configFile)
