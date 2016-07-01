"""Code to initiate the generating of the flat file representations of the QICKD data set."""

# Python imports.
import argparse
import datetime
import logging
import json
import os
import sys

# User imports.
from Utilities import json_to_ascii
if __package__ == "PatientExtraction":
    # If the package is PatientExtraction, then relative imports are needed.
    from . import patient_extraction
else:
    # The code was not called from within the Code directory using 'python -m PatientExtraction'.
    # Therefore, we need to add the top level Code directory to the search path and use absolute imports.
    currentDir = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
    codeDir = os.path.abspath(os.path.join(currentDir, os.pardir))
    sys.path.append(codeDir)
    from PatientExtraction import patient_extraction

# Globals.
PYVERSION = sys.version_info[0]  # Determine major version number.


#------------------------#
# Create Argument Parser #
#------------------------#
parser = argparse.ArgumentParser(description="Extract patients meeting user-defined case definitions.",
                                 epilog="For additional information on the expected format and contents of the input "
                                        "and output files please see the README.")

# Mandatory arguments.
parser.add_argument("input", help="The location of the file containing the case definitions.", type=str)

# Optional arguments.
parser.add_argument("-c", "--config", help="The location of the configuration file to use.", type=str)
parser.add_argument("-o", "--output",
                    help="The location of the directory to write the output files to. Default: a timestamped "
                         "subdirectory in the Results directory.",
                    type=str)
parser.add_argument("-w", "--overwrite",
                    action="store_true",
                    help="Whether the output directory should be overwritten if it exists. Default: do not overwrite.")

#------------------------------#
# Parse and Validate Arguments #
#------------------------------#
args = parser.parse_args()
dirTop = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)  # The directory containing all program files.
errorsFound = []  # Container for any error messages generated during the validation.

# Validate the input file.
fileInput = args.input
if not os.path.isfile(fileInput):
    errorsFound.append("The input file location does not contain a file.")

# Validate the configuration file.
fileConfig = args.config
if fileConfig:
    # A configuration file was provided.
    if not os.path.isfile(fileConfig):
        errorsFound.append("The configuration file location does not contain a file.")
else:
    # Use the default configuration file.
    dirConfig = os.path.join(os.path.abspath(dirTop), "ConfigFiles")
    fileConfig = os.path.join(dirConfig, "PatientExtractionConfig.json")

# Validate the output directory.
dirResults = os.path.join(os.path.abspath(dirTop), "Results")  # The default results directory.
dirDefaultOutput = os.path.join(dirResults,
                                "PatientExtraction_{0:s}".format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
dirOutput = args.output if args.output else dirDefaultOutput
overwrite = args.overwrite
if overwrite:
    try:
        os.rmdir(dirOutput)
    except FileNotFoundError:
        # Can't remove the directory as it doesn't exist.
        pass
    except Exception as e:
        # Can't remove the directory for another reason.
        errorsFound.append("Could not overwrite the default output directory location - {0:s}".format(str(e)))
elif os.path.exists(dirOutput):
    errorsFound.append("The default output directory location already exists and overwriting is not enabled.")

# Display errors if any were found.
if errorsFound:
    print("\n\nThe following errors were encountered while parsing the input arguments:\n")
    print('\n'.join(errorsFound))
    sys.exit()

# Only create the output directory if there were no errors encountered.
try:
    os.makedirs(dirOutput, exist_ok=True)  # Attempt to make the output directory. Don't care if it already exists.
except Exception as e:
    print("\n\nThe following errors were encountered while parsing the input arguments:\n")
    print("The output directory could not be created - {0:s}".format(str(e)))
    sys.exit()

#------------------#
# Setup the Logger #
#------------------#
# Create the logger.
logger = logging.getLogger("PatientExtraction")
logger.setLevel(logging.DEBUG)

# Create the logger file handler.
fileLog = os.path.join(dirOutput, "PatientExtraction.log")
logFileHandler = logging.FileHandler(fileLog)
logFileHandler.setLevel(logging.DEBUG)

# Create a console handler for higher level logging.
logConsoleHandler = logging.StreamHandler()
logConsoleHandler.setLevel(logging.ERROR)

# Create formatter and add it to the handlers.
formatter = logging.Formatter("%(name)s\t%(levelname)s\t%(message)s")
logFileHandler.setFormatter(formatter)
logConsoleHandler.setFormatter(formatter)

# Add the handlers to the logger.
logger.addHandler(logFileHandler)
logger.addHandler(logConsoleHandler)

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
elif not os.path.isdir(parsedArgs["FlatFileDirectory"]):
    errorsFound.append("The input data directory does not exist.")

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

#--------------------------------#
# Perform the Patient Extraction #
#--------------------------------#
dirFlatFiles = parsedArgs["FlatFileDirectory"]
filePatientData = os.path.join(dirFlatFiles, "PatientData.tsv")
fileCodeDescriptions = parsedArgs["CodeDescriptionFile"]

logger.info("Starting patient extraction.")
patient_extraction.main(fileInput, dirOutput, filePatientData, fileCodeDescriptions)
