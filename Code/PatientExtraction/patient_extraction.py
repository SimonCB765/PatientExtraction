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

            # Select the portion of the patient's record (i.e. code associations) meeting the requirements for each
            # case definition.
            for i in caseNames:
                # Select associations involving the positive indicator codes.
                caseSubset = {i: patientRecord[i] for i in caseDefinitions[i]["Codes"] if i in patientRecord}
                # Apply the restrictions to the positive indicator code associations.
                caseSubset = apply_restrictions(caseSubset, caseDefinitions[i]["Restrictions"])
                # Extract the subset of this restricted set of associations that the user desires (based on the modes).
                if not caseSubset:
                    # If there are no associations remaining, then return empty dictionaries for each mode.
                    extractedHistory[i] = {j: {} for j in validChoices["Modes"]}
                else:
                    # Select the associations needed according the modes.
                    extractedHistory[i] = record_selector.select_associations(
                        caseSubset, caseDefinitions[i]["Modes"], validChoices["Modes"]
                    )

            # Generate and record the output for the patient.
            generatedOutput = generate_patient_output(
                extractedHistory, caseNames, caseDefinitions, validChoices["Outputs"]
            )
            fidExtraction.write("{:s}\t{:s}\n".format(patientID, generatedOutput))


def apply_restrictions(medicalRecord, conditionRestrictions):
    """Remove associations from a patient's medical history not meeting the restriction criteria for a case definition.

    :param medicalRecord:           A patient's medical record. This should have the format:
                                        {
                                            "Code1": [
                                                {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
                                                {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
                                            ],
                                            "Code2": [{"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}],
                                            "Code3": [
                                                {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
                                                {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
                                            ]
                                        }
    :type medicalRecord:            dict
    :param conditionRestrictions:   The data about the condition restrictions. This has the format:
                                        {"Date": [], "Val1": [], "Val2": []}
                                        where each list contains functions that apply the restrictions of the given
                                        type (i.e. the "Date" list contains functions to implement the date-based
                                        restrictions).
    :type conditionRestrictions     dict
    :return:                        The restricted patient's medical history in the same format as the input history.
    :rtype:                         dict

    """

    # Remove associations that do not meet the restriction criteria.
    for i in conditionRestrictions:
        # Go through each category of restrictions (values, dates, etc.).
        for j in conditionRestrictions[i]:
            # Filter the patient's record by the current restriction, leaving only those associations
            # that meet the current restriction.
            medicalRecord = {k: [l for l in medicalRecord[k] if j(l[i])] for k in medicalRecord}

    # Filter out codes that have had all associations with the patient removed by the restrictions.
    medicalRecord = {i: medicalRecord[i] for i in medicalRecord if medicalRecord[i]}

    return medicalRecord


def generate_patient_output(extractedHistory, caseNames, caseDefinitions, outputFunctions):
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
    :param outputFunctions:     A mapping from valid output methods to the functions that implement them.
    :type outputFunctions:      dict
    :return:                    The extracted patient data in the correct format for outputting.
    :rtype:                     str

    """

    generatedOutput = []  # The output for the patient.

    for i in caseNames:
        # Get the modes used with this case definition that the patient has extracted data for.
        modesWithData = {j for j, k in extractedHistory[i].items() if k}
        if modesWithData:
            # The patient has a mode for this case definition for which some data was extracted.
            for mode in caseDefinitions[i]["Modes"]:
                if mode in modesWithData:
                    # If using the given mode managed to collect any associations.
                    extractedModeData = extractedHistory[i][mode]  # Data extracted using the mode.
                    for out in caseDefinitions[i]["Outputs"]:
                        generatedOutput.append(outputFunctions[out](extractedModeData))
                else:
                    # Add blanks for each column associated with this mode, as using it we didn't get any association.
                    generatedOutput.extend(['' for _ in caseDefinitions[i]["Outputs"]])
        else:
            # Add blanks for each column if the patient doesn't have the condition.
            generatedOutput.extend(
                ['' for _ in caseDefinitions[i]["Modes"] for _ in caseDefinitions[i]["Outputs"]]
            )

    return '\t'.join(generatedOutput)
