"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import json
import os
import sys

# User imports.
from Utilities import json_to_ascii

# Globals.
PYVERSION = sys.version_info[0]  # Determine major version number.


def main(fileInput, dirOutput, fileConfig):

    #---------------------------------------------#
    # Parse and Validate Configuration Parameters #
    #---------------------------------------------#
    errorsFound = []

    # Parse the JSON file of parameters.
    readParams = open(fileConfig, 'r')
    parsedArgs = json.load(readParams)
    if PYVERSION == 2:
        parsedArgs = json_to_ascii.json_to_ascii(parsedArgs)  # Convert all unicode characters to ascii for Python < v3.
    readParams.close()

    # Check that the flat file input directory parameter is correct.
    if "FlatFileDirectory" not in parsedArgs:
        errorsFound.append("There must be a parameter field called FlatFileDirectory.")
    try:
        os.makedirs(parsedArgs["FlatFileDirectory"])
    except FileExistsError:
        # Directory already exists.
        pass

    # Check that the file containing the mapping from codes to descriptions is present.
    if "CodeDescriptionFile" not in parsedArgs:
        errorsFound.append("There must be a parameter field called CodeDescriptionFile.")
    elif not os.path.isfile(parsedArgs["CodeDescriptionFile"]):
        errorsFound.append("The file of code to description mappings does not exist.")

    # Print error messages.
    if errorsFound:
        print("\n\nThe following errors were encountered while parsing the input parameters:\n")
        print('\n'.join(errorsFound))
        sys.exit()

    # Extract parameters.
    dirFlatFiles = parsedArgs["FlatFileDirectory"]
    fileCodeDescriptions = parsedArgs["CodeDescriptionFile"]
