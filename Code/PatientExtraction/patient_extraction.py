"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import datetime
import json
import operator
import os

# User imports.
from . import conditon_code_mappings

# Globals.
VALIDMODECHOICES = ["earliest", "latest", "all", "max", "min"]  # Initialise the valid code selection modes.
VALIDOUTPUTCHOICES = {"code", "count", "date", "max", "mean", "min", "value"}  # Initialise the valid output options.


def main(fileInput, dirOutput, filePatientData, fileCodeDescriptions):
    """Run the patient extraction.

    :param fileInput:               The location of the input file containing the case definitions.
    :type fileInput:                str
    :param dirOutput:               The location of the directory to write the program output to.
    :type dirOutput:                str
    :param filePatientData:         The location of the file containing the patient data.
    :type filePatientData:          str
    :param fileCodeDescriptions:    The location of the file containing the mapping from codes to their descriptions.
    :type fileCodeDescriptions:     str

    """

    #-------------------------------------------------#
    # Determine Mappings Between Conditions and Codes #
    #-------------------------------------------------#
    # Create the output file to hold the input file enhanced with all codes (including descendants) and their
    # descriptions.
    fileAnnotatedInput = os.path.split(fileInput)[1]
    fileAnnotatedInput = fileAnnotatedInput.split('.')[0] + "_Annotated." + fileAnnotatedInput.split('.')[1]
    fileAnnotatedInput = os.path.join(dirOutput, fileAnnotatedInput)

    # Generate the mapping.
    mapConditionToCode, conditionData, conditionsFound = conditon_code_mappings.main(
        fileInput, fileCodeDescriptions, fileAnnotatedInput, VALIDMODECHOICES, VALIDOUTPUTCHOICES)

    #---------------------------------------------------#
    # Select and Output the Desired Patient Information #
    #---------------------------------------------------#
    fileExtractedData = os.path.join(dirOutput, "ExtractedData.tsv")
    with open(filePatientData, 'r') as fidPatientData, open(fileExtractedData, 'w') as fidExtractedData:
        # Write out the header for the output file.
        header = "PatientID\t{0:s}\n".format(
            '\t'.join(
                ['\t'.join(
                    ["{0:s}__MODE:{1:s}__OUT:{2:s}".format(i, j, k) for j in conditionData[i]["Mode"]
                     for k in conditionData[i]["Out"]])
                 for i in conditionsFound]))
        fidExtractedData.write(header)

        for line in fidPatientData:
            # Load the patient's data.
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]
            medicalRecord = json.loads(chunks[1])
            patientRecordSubset = {}  # The subset of the patient's medical record that meets condition criteria.
            codesAssociatedWith = set(medicalRecord)  # The codes the patient is associated with.

            # Convert all dates to datetime objects.
            for i in medicalRecord:
                for j in medicalRecord[i]:
                    j["Date"] = datetime.datetime.strptime(j["Date"], "%Y-%m-%d")

            for i in conditionsFound:
                # Get the positive and negative indicator codes for the current condition.
                positiveCodes = mapConditionToCode[i]["Positive"]  # Positive indicator codes for the condition.
                negativeCodes = mapConditionToCode[i]["Negative"]  # Negative indicator codes for the condition.

                patientPosCondCodes = codesAssociatedWith & positiveCodes  # Positive indicator codes the patient has.
                patientNegCondCodes = codesAssociatedWith & negativeCodes  # Negative indicator codes the patient has.

                if patientPosCondCodes and not patientNegCondCodes:
                    # If the patient contains at least one positive code for the condition and no negative codes for
                    # the condition, then the patient has the condition.

                    # Extract the needed code association records.
                    selectedRecords = select_associations(medicalRecord, patientPosCondCodes,
                                                          conditionData[i]["Restrictions"], conditionData[i]["Mode"])

                    # Only update the patient's record subset if there are any modes that contain positive indicator
                    # codes for the condition meeting the condition's restriction criteria.
                    selectedRecords = {j: selectedRecords[j] for j in selectedRecords if selectedRecords[j]}
                    if selectedRecords:
                        patientRecordSubset[i] = selectedRecords

            # Generate the required output.
            generatedOutput = generate_patient_output(patientID, patientRecordSubset, conditionsFound, conditionData)

            # Write out the patient's data.
            fidExtractedData.write("{0:s}\n".format(generatedOutput))


def generate_patient_output(patientID, patientRecordSubset, conditions, conditionData):
    """Generate the output string for a given patient.

    :param patientID:           The patient's ID.
    :type patientID:            str
    :param patientRecordSubset: The subset of the patient's medical record containing codes indicating a condition.
                                    This maps conditions to a dictionary where the keys are the codes the patient
                                    has that positively indicate for the condition, and the entries contain the data
                                    about the associations between the code and the patient.
    :type patientRecordSubset:  dict
    :param conditions:          The conditions that the user wants patients for.
    :type conditions:           list
    :param conditionData:       The data about the conditions (mode, output choices and restrictions).
    :type conditionData         dict
    :return:                    The extracted patient data.
    :rtype:                     str

    """

    generatedOutput = patientID  # The output string for the patient.

    for i in conditions:
        if i in patientRecordSubset:
            # If the patient has the condition.
            for mode in conditionData[i]["Mode"]:
                if mode in patientRecordSubset[i]:
                    # If using the given mode managed to collect any associations.
                    for out in conditionData[i]["Out"]:
                        if out == "count":
                            lengths = map(len, [patientRecordSubset[i][mode][k] for k in patientRecordSubset[i][mode]])
                            count = sum(lengths)
                            generatedOutput += "\t{0:d}".format(count)
                        elif out == "max":
                            maxValue = max([l for k in patientRecordSubset[i][mode]
                                            for l in patientRecordSubset[i][mode][k]],
                                           key=operator.itemgetter("Val1"))["Val1"]
                            generatedOutput += "\t{0:.2f}".format(maxValue)
                        elif out == "mean":
                            associations = [l for k in patientRecordSubset[i][mode]
                                            for l in patientRecordSubset[i][mode][k]]
                            meanValue = sum([k["Val1"] for k in associations]) / len(associations)
                            generatedOutput += "\t{0:.2f}".format(meanValue)
                        elif out == "min":
                            minValue = min([l for k in patientRecordSubset[i][mode]
                                            for l in patientRecordSubset[i][mode][k]],
                                           key=operator.itemgetter("Val1"))["Val1"]
                            generatedOutput += "\t{0:.2f}".format(minValue)
                        else:
                            # Output choices where a positive indicator code is required to be selected first, so get an
                            # arbitrary positive indicator code for the condition that the patient is associated with.
                            code = next(iter(patientRecordSubset[i][mode]))
                            if out == "value":
                                # Get an arbitrary value associated with the code.
                                value = patientRecordSubset[i][mode][code][0]["Val1"]
                                generatedOutput += "\t{0:.2f}".format(value)
                            elif out == "date":
                                # Get an arbitrary date associated with the code.
                                date = patientRecordSubset[i][mode][code][0]["Date"]
                                generatedOutput += "\t{0:s}".format(date.strftime("%Y-%m-%d"))
                            else:
                                # Output choice is CODE.
                                generatedOutput += "\t{0:s}".format(code)
                else:
                    # Add blanks for each column associated with this mode, as using it we didn't get any association.
                    generatedOutput += ''.join(['\t' for j in conditionData[i]["Out"]])
        else:
            # Add blanks for each column if the patient doesn't have the condition.
            generatedOutput += ''.join(['\t' for j in conditionData[i]["Mode"] for k in conditionData[i]["Out"]])

    return generatedOutput


def select_associations(medicalRecord, patientPosCondCodes, conditionRestrictions, modes=("all")):
    """Select information about the associations between a patient and their codes according to a mode and restrictions.

    :param medicalRecord:           A patient's medical record.
    :type medicalRecord:            dict
    :param patientPosCondCodes:     The positive indicator codes that a patient has for a given condition.
    :type patientPosCondCodes:      set
    :param conditionRestrictions:   The data about the condition restrictions.
    :type conditionRestrictions     dict
    :param modes:                   The method(s) for selecting which associations between the patient and their codes
                                        should be selected.
    :type modes:                    list
    :return:                        The selected associations between patients and codes that meet the criteria.
                                        There is one entry in the dictionary per mode used. For each mode key in the
                                        dictionary, the associated value is the dictionary of associations between
                                        the patient and codes that meet the criteria, selected based on the mode.
                                        An example of the return dictionary is:
                                        {
                                            'ALL':
                                                {
                                                    'C10E': [{'Date': datetime, 'Text': '..', 'Val1': 0.0, 'Val2': 0.0},
                                                             {'Date': datetime, 'Text': '..', 'Val1': 0.0, 'Val2': 0.0},
                                                             ...
                                                            ]
                                                    'C10F': [{'Date': datetime, 'Text': '..', 'Val1': 0.0, 'Val2': 0.0},
                                                             {'Date': datetime, 'Text': '..', 'Val1': 0.0, 'Val2': 0.0},
                                                             ...
                                                            ],
                                                    ...
                                                }
                                            'MAX': {'XXX': [{'Date': datetime, 'Text': '..', 'Val1': 5.5, 'Val2': 0.0}]}
                                            ...
                                        }
    :rtype:                         dict

    """

    # Select all associations between the positive indicator codes and the patient.
    selectedRecords = {i: medicalRecord[i] for i in patientPosCondCodes}

    # Remove associations that do not meet the restriction criteria.
    for i in conditionRestrictions:
        # Go through each possible category of restrictions (dates, values, etc.).
        for j in conditionRestrictions[i]:
            # Apply each individual restriction to the set of selected records to filter out those records not
            # meeting the present restriction.
            selectedRecords = {k: [l for l in selectedRecords[k] if j(l[i])] for k in selectedRecords}

    # Filter out the codes that have no associations with the patient that satisfy the restriction criteria (i.e.
    # remove all codes that now contain no associations in the selected records).
    selectedRecords = {i: selectedRecords[i] for i in selectedRecords if selectedRecords[i]}

    if not selectedRecords:
        # If there are no records with positive indicator codes that meet the restriction criteria, then return empty
        # dictionaries for each mode.
        return {i: {} for i in modes}

    modeSelectedRecords = {}  # The records selected for each mode.
    for mode in modes:
        if mode == "earliest":
            # Select the earliest association between one of the positive indicator codes and the patient.

            # First find the code that has the earliest association with the patient. This will return not just
            # the earliest association, but all associations between the patient and the earliest occurring code.
            earliestRecord = min(selectedRecords.items(), key=lambda x: x[1][0]["Date"])

            # Determine the code that occurred earliest, and its association with the patient that caused it to be
            # the earliest occurring code. Due to the way associations are stored (chronologically) the first
            # association in the record is the earliest.
            earliestCode = earliestRecord[0]
            earliestAssociation = earliestRecord[1][0]  # The first (and therefore earliest) association with the code.
            modeSelectedRecords[mode] = {earliestCode: [earliestAssociation]}
        elif mode == "latest":
            # Select the latest association between one of the positive indicator codes and the patient.

            # First find the code that has the latest association with the patient. This will return not just
            # the latest association, but all associations between the patient and the latest occurring code.
            latestRecord = max(selectedRecords.items(), key=lambda x: x[1][-1]["Date"])

            # Determine the code that occurred latest, and its association with the patient that caused it to be
            # the latest occurring code. Due to the way associations are stored (chronologically) the last
            # association in the record is the latest.
            latestCode = latestRecord[0]
            latestAssociation = latestRecord[1][-1]  # The last (and therefore latest) association with the code.
            modeSelectedRecords[mode] = {latestCode: [latestAssociation]}
        elif mode == "max":
            # Select the positive indicator code that has an association with the patient that contains the
            # greatest value.
            maxRecord = max(selectedRecords.items(), key=lambda x: max([i["Val1"] for i in x[1]]))

            # Determine the code associated with the max value and its association with the patient that actually has
            # the max value.
            maxCode = maxRecord[0]
            maxAssociation = max(maxRecord[1], key=lambda x: x["Val1"])
            modeSelectedRecords[mode] = {maxCode: [maxAssociation]}
        elif mode == "min":
            # Select the association between one of the positive indicator codes and the patient that
            # contains the smallest value.
            minRecord = min(selectedRecords.items(), key=lambda x: min([i["Val1"] for i in x[1]]))

            # Determine the code associated with the min value and its association with the patient that actually has
            # the min value.
            minCode = minRecord[0]
            minAssociation = min(minRecord[1], key=lambda x: x["Val1"])
            modeSelectedRecords[mode] = {minCode: [minAssociation]}
        else:
            # Selecting all codes.
            modeSelectedRecords[mode] = dict(selectedRecords)

    return modeSelectedRecords
