"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
from collections import defaultdict
import json
import os
import sys

# User imports.
from . import conditon_code_mappings
from Utilities import json_to_ascii

# Globals.
PYVERSION = sys.version_info[0]  # Determine major version number.
VALIDMODECHOICES = ["earliest", "last", "all", "max", "min"]  # Initialise the valid code selection modes.
VALIDOUTPUTCHOICES = {"code", "date", "count", "value"}  # Initialise the valid output options.


def main(fileInput, dirOutput, fileConfig):
    """

    :param fileInput:   The location of the input file containing the case definitions.
    :type fileInput:    str
    :param dirOutput:   The location of the directory to write the program output to.
    :type dirOutput:    str
    :param fileConfig:  The location of the configuration file.
    :type fileConfig:   str

    """

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

    # Setup the log file.
    fileLog = os.path.join(dirOutput, "PatientExtraction.log")

    # Setup the flat file representation files.
    filePatientData = os.path.join(dirFlatFiles, "PatientData.tsv")
    filePatientsWithCodes = os.path.join(dirFlatFiles, "PatientsWithCodes.tsv")

    #-------------------------------------------------#
    # Determine Mappings Between Conditions and Codes #
    #-------------------------------------------------#
    # Create the output file to hold the input file enhanced with all codes (including descendants) and their
    # descriptions.
    fileAnnotatedInput = os.path.split(fileInput)[1]
    fileAnnotatedInput = fileAnnotatedInput.split('.')[0] + "_Annotated." + fileAnnotatedInput.split('.')[1]
    fileAnnotatedInput = os.path.join(dirOutput, fileAnnotatedInput)

    # Generate the mapping.
    mapCodeToCondition, conditionData = conditon_code_mappings.main(
        fileInput, fileCodeDescriptions, fileAnnotatedInput, fileLog, VALIDMODECHOICES, VALIDOUTPUTCHOICES)

    #----------------------------------#
    # Load the Code to Patient Mapping #
    #----------------------------------#
    mapCodeToPatients = {}
    with open(filePatientsWithCodes, 'r') as fidPatientsWithCodes:
        for line in fidPatientsWithCodes:
            line = line.strip()
            chunks = line.split('\t')
            mapCodeToPatients[chunks[0]] = set(chunks[1].split(','))
