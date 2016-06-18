"""Code to initiate the generating of the flat file representations of the QICKD data set."""

# Python imports.
import os
import sys

# User imports.
from . import generate_flat_files


# Determine the default configuration file to use.
codeDir = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
configDir = os.path.join(codeDir, "ConfigFiles")
defaultConfigFile = os.path.join(configDir, "FlatFileGenerationConfig.json")

configFile = defaultConfigFile if len(sys.argv) < 2 else sys.argv[1]
generate_flat_files.main(configFile)
