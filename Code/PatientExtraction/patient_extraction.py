"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import datetime
import json
import logging
import os

# User imports.
from . import annotate_case_definitions
from . import conf
from . import parse_case_definitions

# Globals.
LOGGER = logging.getLogger(__name__)


def main(fileCaseDefs, dirOutput, filePatientData, fileCodeDescriptions, filePatientSubset):
    """Run the patient extraction.

    :param fileCaseDefs:            The location of the input file containing the case definitions.
    :type fileCaseDefs:             str
    :param dirOutput:               The location of the directory to write the program output to.
    :type dirOutput:                str
    :param filePatientData:         The location of the file containing the patient data.
    :type filePatientData:          str
    :param fileCodeDescriptions:    The location of the file containing the mapping from codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param filePatientSubset:       The location of the file containing the IDs of the subset of patients to use
                                        in the extraction.
    :type filePatientSubset:        str

    """

    # Create a version of the input file with expanded codes and added code descriptions.
    annotatedCaseDefsName = os.path.split(fileCaseDefs)[1]
    annotatedCaseDefsName = annotatedCaseDefsName.split('.')[0] + "_Annotated." + annotatedCaseDefsName.split('.')[1]
    fileAnnotatedCaseDefs = os.path.join(dirOutput, annotatedCaseDefsName)
    annotate_case_definitions.main(fileCaseDefs, fileCodeDescriptions, fileAnnotatedCaseDefs)

    # Extract the case definitions from the file of case definitions.
    caseDefinitions, caseNames = parse_case_definitions.main(fileAnnotatedCaseDefs)

    # Identify the patient to restrict the extraction to.
    patientExtractionSubset = set()
    with open(filePatientSubset, 'r') as fidPatientSubset:
        for line in fidPatientSubset:
            line = line.strip()
            patientExtractionSubset.add(line)

    # Extract the patient data.
    fileExtractIon = os.path.join(dirOutput, "DataExtraction.tsv")
    with open(filePatientData, 'r') as fidPatientData, open(fileExtractIon, 'w') as fidExtraction:
        # Write out the header.
        extractions = '\t'.join(
            ["{:s}__MODE_{:s}__OUT_{:s}".format(i, j, k)
             for i in caseNames for j in caseDefinitions[i]["Modes"] for k in caseDefinitions[i]["Outputs"]]
        )
        header = "PatientID\t{:s}\n".format(extractions)
        fidExtraction.write(header)

        # Extract the data for each patient.
        for line in fidPatientData:
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]  # The ID of the patient whose record appears on the line.
            if patientExtractionSubset and patientID not in patientExtractionSubset:
                # Skip this patient if they aren't in the extraction subset (and the extraction subset is being used).
                continue
            patientRecord = json.loads(chunks[1])  # The patient's medical history in JSON format.
            extractedHistory = {}  # The subset of the patient's medical history to be extracted and output.

            # Convert all dates to datetime objects.
            for i in patientRecord:
                for j in patientRecord[i]:
                    j["Date"] = datetime.datetime.strptime(j["Date"], "%Y-%m-%d")

            # Select the portion of the patient's record (i.e. code associations) meeting the requirements for each
            # case definition.
            for i in caseNames:
                # Select the patient's associations that involve a positive indicator code.
                caseSubset = {i: patientRecord[i] for i in caseDefinitions[i]["Codes"] if i in patientRecord}
                # Apply the restrictions for this case to the patient's associations with positive indicator codes
                # in order to remove associations that can not indicate that the case applies to the patient.
                caseSubset = apply_restrictions(caseSubset, caseDefinitions[i]["Restrictions"])
                if not caseSubset:
                    # If there are no associations remaining, then return an empty dictionary for each mode.
                    extractedHistory[i] = {j: {} for j in conf.validChoices["Modes"]}
                else:
                    # Associations remain, so the case applies to the patient. Therefore, extract the subset of the
                    # restricted set of associations that the user desires (according to modes specified for the case).
                    extractedHistory[i] = select_associations(caseSubset, caseDefinitions[i]["Modes"])

            # Generate and record the output for the patient.
            generatedOutput = generate_patient_output(extractedHistory, caseNames, caseDefinitions)
            fidExtraction.write("{:s}\t{:s}\n".format(patientID, generatedOutput))


def apply_restrictions(medicalRecord, caseRestrictions):
    """Remove associations from a patient's medical history not meeting the restriction criteria for a case definition.

    :param medicalRecord:       A patient's medical record. This should have the format:
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
    :type medicalRecord:        dict
    :param caseRestrictions:    The data about the case's restrictions. This has the format:
                                    {"Date": [], "Val1": [], "Val2": []}
                                    where each list contains functions that apply the restrictions of the given
                                    type (i.e. the "Date" list contains functions to implement the date-based
                                    restrictions).
    :type caseRestrictions:     dict
    :return:                    The restricted patient's medical history in the same format as the input history.
    :rtype:                     dict

    """

    # Remove associations that do not meet the restriction criteria.
    for i in caseRestrictions:
        # Go through each category of restrictions (values, dates, etc.).
        for j in caseRestrictions[i]:
            # Filter the patient's record by the current restriction, leaving only those associations
            # that meet the current restriction.
            medicalRecord = {k: [l for l in medicalRecord[k] if j(l[i])] for k in medicalRecord}

    # Filter out codes that have had all associations with the patient removed by the restrictions.
    medicalRecord = {i: medicalRecord[i] for i in medicalRecord if medicalRecord[i]}

    return medicalRecord


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
                        generatedOutput.append(conf.validChoices["Outputs"][out](extractedModeData))
                else:
                    # Add blanks for each column associated with this mode, as using it we didn't get any association.
                    generatedOutput.extend(['' for _ in caseDefinitions[i]["Outputs"]])
        else:
            # Add blanks for each column if the case does not apply to the patient.
            generatedOutput.extend(
                ['' for _ in caseDefinitions[i]["Modes"] for _ in caseDefinitions[i]["Outputs"]]
            )

    return '\t'.join(generatedOutput)


def select_associations(medicalRecord, modes):
    """Select information about the associations between a patient and their codes according to modes and restrictions.

    :param medicalRecord:           A patient's medical record. See the module docstring for its format.
    :type medicalRecord:            dict
    :param modes:                   The method(s) for selecting associations between the patient and their codes.
    :type modes:                    list
    :return:                        The selected associations between patients and codes that meet the criteria.
                                        There is one entry in the dictionary per mode used. For each mode key in the
                                        dictionary, the associated value is the dictionary of associations between
                                        the patient and codes that meet the criteria, selected based on the mode.
                                        An example of the return dictionary is:
                                        {
                                            "all":
                                                {
                                                    "C10E": [{"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             {"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             ...
                                                            ]
                                                    "C10F": [{"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             {"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             ...
                                                            ],
                                                    ...
                                                }
                                            "max": {"XXX": [{"Date": datetime, "Text": "..", "Val1": 5.5, "Val2": 0.0}]}
                                            ...
                                        }
    :rtype:                         dict

    """

    # Select a subset of the patient's medical record for each mode.
    modeMedicalRecords = {}  # The medical record subsets.
    for mode in modes:
        modeMedicalRecords[mode] = conf.validChoices["Modes"][mode](medicalRecord)

    return modeMedicalRecords
