"""Code to initiate the generating of the flat file representations of the QICKD data set."""

# Python imports.
import argparse
import datetime
import logging
import os
import shutil
import sys

# User imports.
if __package__ != "PatientExtraction":
    # The code was not called from within the Code directory using 'python -m PatientExtraction'.
    # Therefore, we need to add the top level Code directory in order to use absolute imports.
    currentDir = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
    codeDir = os.path.abspath(os.path.join(currentDir, os.pardir))
    sys.path.append(codeDir)
from PatientExtraction import conf
from PatientExtraction import patient_extraction


# ====================== #
# Create Argument Parser #
# ====================== #
parser = argparse.ArgumentParser(description="Extract patients meeting user-defined case definitions.",
                                 epilog="For additional information on the expected format and contents of the input "
                                        "and output files please see the README. If the output of the program is not "
                                        "as expected, then examine the log file in the results directory used to "
                                        "determine where case definition errors might have occurred.")

# Mandatory arguments.
parser.add_argument("input", help="The location of the file containing the case definitions.", type=str)

# Optional arguments.
parser.add_argument("-c", "--coding",
                    help="The location of the file containing the mapping from codes to their descriptions. Default: "
                         "a file Coding.tsv in the Data directory",
                    type=str)
parser.add_argument("-d", "--histories",
                    help="The location of the file containing the patient medical history data in flat file format. "
                         "Default: a file FlatPatientData.tsv in the Data directory.",
                    type=str)
parser.add_argument("-o", "--output",
                    help="The location of the directory to write the output files to. Default: a timestamped "
                         "subdirectory in the Results directory.",
                    type=str)
parser.add_argument("-p", "--patient",
                    help="The location of the file containing the IDs' of the patients that the extraction should be "
                         "restricted to. Default: a file PatientSubset.txt in the Data directory.",
                    type=str)
parser.add_argument("-w", "--overwrite",
                    action="store_true",
                    help="Whether the output directory should be overwritten if it exists. Default: do not overwrite.")

# ============================ #
# Parse and Validate Arguments #
# ============================ #
args = parser.parse_args()
dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
dirTop = os.path.abspath(os.path.join(dirCurrent, os.pardir, os.pardir))
dirData = os.path.abspath(os.path.join(dirTop, "Data"))
dirResults = os.path.join(os.path.abspath(dirTop), "Results")
errorsFound = []  # Container for any error messages generated during the validation.

# Validate the input file.
fileInput = args.input
if not os.path.isfile(fileInput):
    errorsFound.append("The input file location does not contain a file.")

# Validate the location of the code mapping file.
fileCodeDescriptions = os.path.join(dirData, "Coding.tsv")
fileCodeDescriptions = args.coding if args.coding else fileCodeDescriptions
if not os.path.isfile(fileCodeDescriptions):
    errorsFound.append("The file containing the code to description mappings could not be found.")

# Validate the output directory.
dirOutput = os.path.join(
    dirResults, "PatientExtraction_{0:s}".format(datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
dirOutput = args.output if args.output else dirOutput
overwrite = args.overwrite
if overwrite:
    try:
        shutil.rmtree(dirOutput)
    except FileNotFoundError:
        # Can't remove the directory as it doesn't exist.
        pass
    except Exception as e:
        # Can't remove the directory for another reason.
        errorsFound.append("Could not overwrite the output directory location - {0:s}".format(str(e)))
elif os.path.exists(dirOutput):
    errorsFound.append("The output directory location already exists and overwriting is not enabled.")

# Validate the patient medical history data file.
filePatientData = os.path.join(dirData, "FlatPatientData.tsv")
filePatientData = args.histories if args.histories else filePatientData
if not os.path.isfile(filePatientData):
    errorsFound.append("The file containing the patient data could not be found.")

# Validate the file containing the patient subset to use.
filePatientSubset = os.path.join(dirData, "PatientSubset.txt")
filePatientSubset = args.patient if args.patient else filePatientSubset
if not os.path.isfile(filePatientSubset):
    errorsFound.append("The location containing the subset of patients to use is not a file.")

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

# ================ #
# Setup the Logger #
# ================ #
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

# ============================== #
# Perform the Patient Extraction #
# ============================== #
logger.info("Starting patient extraction.")
conf.init()  # Initialise the settings-like global variables.
patient_extraction.main(fileInput, dirOutput, filePatientData, fileCodeDescriptions, filePatientSubset)
