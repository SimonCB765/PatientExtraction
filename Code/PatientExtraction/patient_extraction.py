"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import datetime
import json
import operator
import os

# User imports.
from . import conditon_code_mappings
from . import record_selector

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
                    selectedRecords = record_selector.select_associations(medicalRecord, patientPosCondCodes,
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
