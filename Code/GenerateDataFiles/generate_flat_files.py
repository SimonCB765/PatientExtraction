"""Generate flat file representations of the QICKD SQL data dumps."""

# Python imports.
import collections
import datetime
import json
import operator


def main(filePatients, fileOutput):
    """Generate the flat files to use for the patient extraction.

    The SQL file that the data is read from is assumed to have all patient entries listed consecutively.

    :param filePatients:    The location of the patient data file (in SQL insert format).
    :type filePatients:     str
    :param fileOutput:      The location of the file where the patient data should be saved.
    :type fileOutput:       str

    """

    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientData = collections.defaultdict(list)  # The data for the current patient.
    with open(filePatients, 'r') as fidPatients:
        for line in fidPatients:
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
                    save_patient(currentPatient, patientData, fileOutput)  # Record the old patient's data.
                    patientData = collections.defaultdict(list)  # Clear the patient data.

                # Update the patient's data.
                currentPatient = patientID
                if code:
                    # There was a code recorded for this association.
                    patientData[code].append({"Date": date, "Val1": value1, "Val2": value2, "Text": freeText})
                else:
                    # There was no code recorded for this association. For example, the association looks like:
                    # 3123336,'','2004-11-01',0.0000,0.0000,null
                    continue

    # Record the final patient's data.
    save_patient(currentPatient, patientData, fileOutput)


def save_patient(patientID, patientData, fileOutput):
    """Save a single patient's medical history in JSON format on a single line.

    :param patientID:           The ID of the patient
    :type patientID:            str
    :param patientData:         The patient's medical history. Each entry is a dictionary with the format:
                                    {"Date": date, "Val1": value1, "Val2": value2, "Text": freeText}
    :type patientData:          dict
    :param fileOutput:          The location of the file to save the patient's data to.
    :type fileOutput:           str

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
    with open(fileOutput, 'a') as fidOutput:
        fidOutput.write("{0:s}\t{1:s}\n".format(patientID, json.dumps(patientData)))
