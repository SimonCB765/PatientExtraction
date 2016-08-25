"""Code to initiate the generating of the flat file representations of the QICKD data set."""

# Python imports.
import argparse
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


# ====================== #
# Create Argument Parser #
# ====================== #
parser = argparse.ArgumentParser(description="Extract patient data according to predefined concepts.",
                                 epilog="For additional information on the expected format and contents of the input "
                                        "and output files please see the README.")

# Optional arguments.
parser.add_argument("-p", "--patient",
                    help="The location of the file containing the patient medical history data in SQL insert format. "
                         "Default: a file journal.sql in the Data directory.",
                    type=str)
parser.add_argument("-o", "--output",
                    help="The location of the file to write the output files to. Default: a file called "
                         "FlatPatientData.tsv in the Data directory.",
                    type=str)

# ============================ #
# Parse and Validate Arguments #
# ============================ #
args = parser.parse_args()
dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
dirData = os.path.abspath(os.path.join(dirCurrent, os.pardir, os.pardir, "Data"))
filePatients = os.path.join(dirData, "journal.sql")
filePatients = args.patient if args.patient else filePatients
fileOutput = os.path.join(dirData, "FlatPatientData.tsv")
fileOutput = args.output if args.output else fileOutput
if not os.path.isfile(filePatients):
    print("\n\nThe following errors were encountered while parsing the input arguments:\nThe file containing patient "
          "data could not be found.")
    sys.exit()
if os.path.isfile(fileOutput):
    os.remove(fileOutput)

# ======================= #
# Generate the Flat Files #
# ======================= #
generate_flat_files.main(filePatients, fileOutput)
