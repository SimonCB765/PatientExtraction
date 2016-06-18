"""Generate flat file representations of the QICKD SQL data dumps."""

# Python imports.
import collections
import json
import os
import sys

# User imports.
from Utilities import json_to_ascii

# Globals.
PYVERSION = sys.version_info[0]  # Determine major version number.


def main(fileConfig):
    """Generate the flat files to use for the patient extraction.

    :param fileConfig:   The location of the file containing the flat file generation arguments in JSON format.
    :type fileConfig:    str

    """

    #-------------------------------------#
    # Parse and Validate Input Parameters #
    #-------------------------------------#
    # Parse the JSON file of parameters.
    readParams = open(fileConfig, 'r')
    parsedArgs = json.load(readParams)
    if PYVERSION == 2:
        parsedArgs = json_to_ascii.json_to_ascii(parsedArgs)  # Convert all unicode characters to ascii for Python < v3.
    readParams.close()

    # Check the input directory parameter is correct.
    errorsFound = []
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

    #----------------------------------#
    # Extract Data from the SQL Files  #
    #----------------------------------#
    patientsWithCodes = collections.defaultdict(set)
    patientData = collections.defaultdict(lambda: collections.defaultdict(list))
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
                date = entries[2]
                value1 = float(entries[3])
                value2 = float(entries[4])
                freeText = entries[5] if entries[5] != "null" else ''

                # Update the patient record.
                patientData[patientID][code].append({"Date": date, "Val1": value1, "Val2": value2, "Text": freeText})

                # Update the record of codes associated with patients.
                patientsWithCodes[code].add(patientID)

    #--------------------#
    # Output Flat Files  #
    #--------------------#
    filePatientsWithCodes = os.path.join(dirOutput, "PatientsWithCodes.tsv")
    filePatientData = os.path.join(dirOutput, "PatientData.tsv")
    with open(filePatientsWithCodes, 'w') as fidPatientsWithCodes:
        for i in patientsWithCodes:
            fidPatientsWithCodes.write("{0:s}\t{1:s}\n".format(i, ','.join([str(j) for j in patientsWithCodes[i]])))

    with open(filePatientData, 'w') as fidPatientData:
        for i in patientData:
            fidPatientData.write("{0:s}\t{1:s}\n".format(i, json.dumps(patientData[i])))
