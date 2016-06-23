"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import datetime
import json
import operator
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
    mapConditionToCode, conditionData, conditionsFound = conditon_code_mappings.main(
        fileInput, fileCodeDescriptions, fileAnnotatedInput, fileLog, VALIDMODECHOICES, VALIDOUTPUTCHOICES)

    #TODO - add a check for the mode and outputs being compatible, and if not change them, log them, output warnings

    #---------------------------------------------------#
    # Select and Output the Desired Patient Information #
    #---------------------------------------------------#
    with open(filePatientData, 'r') as fidPatientData:
        for line in fidPatientData:
            # Load the patient's data.
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]
            medicalRecord = json.loads(chunks[1])
            codesAssociatedWith = set(medicalRecord)  # The codes the patient is associated with.

            for i in mapConditionToCode:
                # Get the positive and negative indicator codes for the current condition.
                positiveCodes = mapConditionToCode[i]["Positive"]  # Positive indicator codes for the condition.
                negativeCodes = mapConditionToCode[i]["Negative"]  # Negative indicator codes for the condition.

                patientPosCondCodes = codesAssociatedWith & positiveCodes  # Positive indicator codes the patient has.
                patientNegCondCodes = codesAssociatedWith & negativeCodes  # Negative indicator codes the patient has.

                if patientPosCondCodes and not patientNegCondCodes:
                    # If the patient contains at least one positive code for the condition and no negative codes for
                    # the condition, then the patient has the condition.
                    print(patientID, i, patientPosCondCodes)

                    # Extract the needed code association records.
                    selectedRecords = select_associations(medicalRecord, patientPosCondCodes, conditionData[i]["Mode"])

                    print(patientID, selectedRecords)
                    print("\n")

                    conditionsFound

                    # Generate the required output.
                    if conditionData[i]["Out"] == "code":
                        pass
                    if conditionData[i]["Out"] == "date":
                        pass
                    if conditionData[i]["Out"] == "count":
                        pass
                    if conditionData[i]["Out"] == "value":
                        pass

        print("\n\n")
        print(conditionData)


def select_associations(medicalRecord, patientPosCondCodes, mode="all"):
    """Select information about the associations between a patient and their codes according to a specified mode.

    :param medicalRecord:       A patient's medical record.
    :type medicalRecord:        dict
    :param patientPosCondCodes: The positive indicator codes that a patient has for a given condition.
    :type patientPosCondCodes:  set
    :param mode:                The method for selecting which associations between the patient and their codes should
                                be selected.
    :type mode:                 str
    :return:                    The selected associations between patients and codes that meet the criteria.
    :rtype:                     dict

    """

    selectedRecords = {}  # The selected associations between patients and codes that meet the criteria.

    if mode == "all":
        # Select all associations between the positive indicator codes and the patient.
        selectedRecords = {i: medicalRecord[i] for i in patientPosCondCodes}
    elif mode == "earliest":
        # Select the earliest association between one of the positive indicator codes and the patient.
        for i in patientPosCondCodes:
            selectedRecords[i] = medicalRecord[i][0]
            selectedRecords[i]["Date"] = datetime.datetime.strptime(selectedRecords[i]["Date"], "%Y-%m-%d")
        earliestRecord = min(selectedRecords.items(), key=lambda x: x[1]["Date"])
        selectedRecords = {earliestRecord[0]: [earliestRecord[1]]}
        for i in selectedRecords:
            selectedRecords[i][0]["Date"] = selectedRecords[i][0]["Date"].strftime("%Y-%m-%d")
    elif mode == "last":
        # Select the latest association between one of the positive indicator codes and the patient.
        for i in patientPosCondCodes:
            selectedRecords[i] = medicalRecord[i][0]
            selectedRecords[i]["Date"] = datetime.datetime.strptime(selectedRecords[i]["Date"], "%Y-%m-%d")
        latestRecord = min(selectedRecords.items(), key=lambda x: x[1]["Date"])
        selectedRecords = {latestRecord[0]: [latestRecord[1]]}
        for i in selectedRecords:
            selectedRecords[i][0]["Date"] = selectedRecords[i][0]["Date"].strftime("%Y-%m-%d")
    elif mode == "max":
        # Select the association between one of the positive indicator codes and the patient that
        # contains the greatest value.
        keyFunction = operator.itemgetter("Val1")
        for i in patientPosCondCodes:
            selectedRecords[i] = max(medicalRecord[i], key=keyFunction)
        maxRecord = max(selectedRecords.items(), key=lambda x: x[1]["Val1"])
        selectedRecords = {maxRecord[0]: [maxRecord[1]]}
    elif mode == "min":
        # Select the association between one of the positive indicator codes and the patient that
        # contains the smallest value.
        keyFunction = operator.itemgetter("Val1")
        for i in patientPosCondCodes:
            selectedRecords[i] = min(medicalRecord[i], key=keyFunction)
        minRecord = min(selectedRecords.items(), key=lambda x: x[1]["Val1"])
        selectedRecords = {minRecord[0]: [minRecord[1]]}

    return selectedRecords
