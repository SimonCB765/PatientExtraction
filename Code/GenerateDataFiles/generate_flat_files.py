"""Generate flat file representations of the QICKD SQL data dumps."""

# Python imports.
import collections
import datetime
import json
import operator
import os
import sys

# User imports.
from Utilities import json_to_ascii

# Globals.
PYVERSION = sys.version_info[0]  # Determine major version number.


def main(fileConfig):
    """Generate the flat files to use for the patient extraction.

    The SQL file that the data is read from is assumed to have all patient entries listed consecutively.

    :param fileConfig:   The location of the file containing the flat file generation arguments in JSON format.
    :type fileConfig:    str

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

    # Check the input directory parameter is correct.
    if "SQLDataDirectory" not in parsedArgs:
        errorsFound.append("There must be a parameter field called SQLDataDirectory.")
    elif not os.path.isdir(parsedArgs["SQLDataDirectory"]):
        errorsFound.append("The input data directory does not exist.")

    # Check the output directory parameter is correct.
    if "FlatFileDirectory" not in parsedArgs:
        errorsFound.append("There must be a parameter field called FlatFileDirectory.")
    try:
        os.makedirs(parsedArgs["FlatFileDirectory"])
    except FileExistsError:
        # Directory already exists.
        pass

    # Print error messages.
    if errorsFound:
        print("\n\nThe following errors were encountered while parsing the input parameters:\n")
        print('\n'.join(errorsFound))
        sys.exit()

    # Extract parameters.
    dirSQLFiles = parsedArgs["SQLDataDirectory"]
    dirOutput = parsedArgs["FlatFileDirectory"]

    # Get the files for the SQL table we're interested in the journal table).
    fileJournalTable = os.path.join(dirSQLFiles, "journal.sql")

    # Setup the output file for the patient data.
    filePatientData = os.path.join(dirOutput, "PatientData.tsv")
    try:
        os.remove(filePatientData)
    except FileNotFoundError:
        # The file does not exist so no need to do anything.
        pass

    #----------------------------------#
    # Extract Data from the SQL Files  #
    #----------------------------------#
    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientData = collections.defaultdict(list)  # The data for the current patient.
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            if line[:6] == "insert":
                # The line contains information about a row in the journal table.
                line = line[75:]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.

                # Some codes are recorded as '2469,v=130,w=80'. In this case the code has its two values recorded
                # as part of the code. It's also possible that the free text has commas in it (which is used as the
                # delimiter in the insert statement). Simply splitting the insert statement on a comma to get the
                # different values is therefore not feasible. Instead, the line has to be read character by character
                # to make sure that the line parsing is done correctly.
                # Any values that are treated in a European manner with a comma in place of the decimal point will
                # cause the parsing to fail, unless they are quoted.
                entries = []
                currentEntry = ""
                inQuoteBlock = False
                for i in line:
                    if i == ',' and not inQuoteBlock:
                        # Found a separator and we aren't in a quote block. Therefore, record the end of the current
                        # entry and initialise for the next entry.
                        entries.append(currentEntry)
                        currentEntry = ""
                    elif i in ["'", '"']:
                        # Either found the end or the start of a quote block.
                        inQuoteBlock = not inQuoteBlock
                    else:
                        # Either current character is not a comma or we are currently in a quote block as are
                        # ignoring commas.
                        currentEntry += i
                entries.append(currentEntry)  # Add the final entry.

                patientID = entries[0]
                code = entries[1].split(',')[0]  # If the code is recorded with its values, then just get the code.
                date = datetime.datetime.strptime(entries[2], "%Y-%m-%d")
                value1 = float(entries[3])
                value2 = float(entries[4])
                freeText = entries[5] if entries[5] != "null" else ''

                if patientID != currentPatient and currentPatient:
                    # A new patient has been found and this is not the first line of the file.
                    save_patient(currentPatient, patientData, filePatientData)  # Record the old patient's data.
                    patientData = collections.defaultdict(list)  # Clear the patient data.

                # Update the patient's data.
                currentPatient = patientID
                patientData[code].append({"Date": date, "Val1": value1, "Val2": value2, "Text": freeText})

    # Record the final patient's data.
    save_patient(currentPatient, patientData, filePatientData)


def save_patient(patientID, patientData, filePatientData):
    """Save a single patient's medical history in JSON format on a single line.

    :param patientID:           The ID of the patient
    :type patientID:            str
    :param patientData:         The patient's medical history. Each entry is a dictionary with the format:
                                    {"Date": date, "Val1": value1, "Val2": value2, "Text": freeText}
    :type patientData:          dict
    :param filePatientData:     The location of the file to save the patient's data to.
    :type filePatientData:      str

    """

    # When the patient has multiple entries for a given code, make sure those entries are saved in
    # chronological order.
    for code in patientData:
        # Sort the entries by date.
        patientData[code] = sorted(patientData[code], key=operator.itemgetter("Date"))

        # Turn the date back into a string for writing out.
        for j in patientData[code]:
            j["Date"] = j["Date"].strftime("%Y-%m-%d")

    # Output the current patient's data.
    with open(filePatientData, 'a') as fidPatientData:
        fidPatientData.write("{0:s}\t{1:s}\n".format(patientID, json.dumps(patientData)))
