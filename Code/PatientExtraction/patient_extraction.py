"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import datetime
import json
import os

# User imports.
from . import annotate_case_definitions
from . import parse_conditions
from . import record_selector


def main(fileCaseDefs, dirOutput, filePatientData, fileCodeDescriptions, validChoices):
    """Run the patient extraction.

    :param fileCaseDefs:            The location of the input file containing the case definitions.
    :type fileCaseDefs:             str
    :param dirOutput:               The location of the directory to write the program output to.
    :type dirOutput:                str
    :param filePatientData:         The location of the file containing the patient data.
    :type filePatientData:          str
    :param fileCodeDescriptions:    The location of the file containing the mapping from codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param validChoices:            The valid modes, outputs and operators that can appear in the case definition file.
    :type validChoices:             dict

    """

    # Create a version of the input file with expanded codes and added code descriptions.
    annotatedCaseDefsName = os.path.split(fileCaseDefs)[1]
    annotatedCaseDefsName = annotatedCaseDefsName.split('.')[0] + "_Annotated." + annotatedCaseDefsName.split('.')[1]
    fileAnnotatedCaseDefs = os.path.join(dirOutput, annotatedCaseDefsName)
    annotate_case_definitions.main(fileCaseDefs, fileCodeDescriptions, fileAnnotatedCaseDefs, validChoices)

    # Extract the case definitions from the file of case definitions.
    caseDefinitions, caseNames = parse_conditions.main(fileAnnotatedCaseDefs, validChoices)

    # Extract the patient data.
    fileExtractIon = os.path.join(dirOutput, "DataExtraction.tsv")
    with open(filePatientData, 'r') as fidPatientData, open(fileExtractIon, 'w') as fidExtraction:
        # Write out the header.
        extractions = '\t'.join(
            ["{:s}__MODE-{:s}__OUT-{:s}".format(i, j, k)
             for i in caseNames for j in caseDefinitions[i]["Modes"] for k in caseDefinitions[i]["Outputs"]]
        )
        header = "PatientID\t{:s}\n".format(extractions)
        fidExtraction.write(header)

        # Extract the data for each patient, one per line.
        for line in fidPatientData:
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]
            patientRecord = json.loads(chunks[1])  # The patient's medical history in JSON format.
            extractedHistory = {}  # The subset of the patient's medical history to be extracted and output.

            # Convert all dates to datetime objects.
            for i in patientRecord:
                for j in patientRecord[i]:
                    j["Date"] = datetime.datetime.strptime(j["Date"], "%Y-%m-%d")

            # Select associations meeting the requirements for each case definition.
            for i in caseNames:
                # Get the portion of the patient's record (if any) that indicates that this case applies to the patient.
                caseSubset = {i: patientRecord[i] for i in caseDefinitions[i]["Codes"] if i in patientRecord}
                extractedHistory[i] = record_selector.select_associations(
                    caseSubset, caseDefinitions[i]["Restrictions"], caseDefinitions[i]["Modes"], validChoices["Modes"]
                )

            # Generate and record the output for the patient.
            generatedOutput = generate_patient_output(extractedHistory, caseNames, caseDefinitions)
            fidExtraction.write("{:s}\t{:s}\n".format(patientID, generatedOutput))


def generate_patient_output(extractedHistory, caseNames, caseDefinitions):
    """Generate the output string for a given patient.

    :param extractedHistory:    The subset of a patient's history that has been extracted for each mode and each case.
                                    This maps case names to a dictionary mapping the extraction modes used for the
                                    case to the patient's code associations that were extracted according to the mode.
                                    For example,
                                    {
                                        "Case_A": {
                                            "all": {
                                                "Code1": [
                                                    {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
                                                    {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
                                                ],
                                                "Code2": [{"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}],
                                                "Code3": [
                                                    {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
                                                    {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
                                                ]
                                            },
                                            "earliest": {
                                                "Code": [{"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}]
                                            },
                                            "max": {
                                                "Code": [{"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}]
                                            }
                                        },
                                        "Case_B": {...},
                                        ...
                                        "Case_N": {...}

                                    }
    :type extractedHistory:     dict
    :param caseNames:           The names of the case definitions in the order they appear in the definition file, which
                                    is also the order they will be output in.
    :type caseNames:            list
    :param caseDefinitions:     The case definitions (i.e. mode, output, restriction and indicator code information).
    :type caseDefinitions:      dict
    :return:                    The extracted patient data in the correct format for outputting.
    :rtype:                     str

    """

    generatedOutput = ""  # The output string for the patient.

    for i in caseNames:
        # Get the modes used with this case definition that the patient has extracted data for.
        modesWithData = {j for j, k in extractedHistory[i].items() if k}
        if modesWithData:
            # The patient has a mode for this case definition for which some data was extracted.
            for mode in caseDefinitions[i]["Modes"]:
                if mode in modesWithData:
                    # If using the given mode managed to collect any associations.
                    extractedModeData = extractedHistory[i][mode]
                    for out in caseDefinitions[i]["Outputs"]:
                        if out == "count":
                            # Get the number of associations between the patient and each code that indicates the
                            # case applies to them, and then sum these numbers.
                            count = sum(map(len, extractedModeData.values()))
                            generatedOutput += "\t{:d}".format(count)
                        elif out == "max":
                            # Get the code association with the maximum value, and then output the value itself.
                            maxAssoc = max([k for j in extractedModeData.values() for k in j], key=lambda x: x['Val1'])
                            generatedOutput += "\t{:.2f}".format(maxAssoc["Val1"])
                        elif out == "mean":
                            # Get the code associations that indicate the case applies to the patient, and then take
                            # the mean value of all these associations.
                            associationValues = [k["Val1"] for j in extractedModeData.values() for k in j]
                            meanValue = sum(associationValues) / len(associationValues)
                            generatedOutput += "\t{:.2f}".format(meanValue)
                        elif out == "min":
                            # Get the code association with the minimum value, and then output the value itself.
                            minAssoc = min([k for j in extractedModeData.values() for k in j], key=lambda x: x['Val1'])
                            generatedOutput += "\t{:.2f}".format(minAssoc["Val1"])
                        else:
                            # Output choices where a positive indicator code is required to be selected first, so get an
                            # arbitrary positive indicator code for the condition that the patient is associated with.
                            code = next(iter(extractedModeData))
                            if out == "value":
                                # Get an arbitrary value associated with the code.
                                value = extractedModeData[code][0]["Val1"]
                                generatedOutput += "\t{:.2f}".format(value)
                            elif out == "date":
                                # Get an arbitrary date associated with the code.
                                date = extractedModeData[code][0]["Date"]
                                generatedOutput += "\t{:s}".format(date.strftime("%Y-%m-%d"))
                            else:
                                # Output choice is CODE, so just output the code.
                                generatedOutput += "\t{:s}".format(code)
                else:
                    # Add blanks for each column associated with this mode, as using it we didn't get any association.
                    generatedOutput += ''.join(['\t' for _ in caseDefinitions[i]["Outputs"]])
        else:
            # Add blanks for each column if the patient doesn't have the condition.
            generatedOutput += ''.join(
                ['\t' for _ in caseDefinitions[i]["Modes"] for _ in caseDefinitions[i]["Outputs"]]
            )

    return generatedOutput
