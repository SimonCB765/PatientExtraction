"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import os

# User imports.
from . import annotate_case_definitions
from . import parse_conditions


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
    :param validChoices:            The valid mode and output flags that can appear in the case definition file.
    :type validChoices:             dict

    """

    # Create a version of the input file with expanded codes and added code descriptions.
    fileAnnotatedCaseDefs = os.path.split(fileCaseDefs)[1]
    fileAnnotatedCaseDefs = fileAnnotatedCaseDefs.split('.')[0] + "_Annotated." + fileAnnotatedCaseDefs.split('.')[1]
    fileAnnotatedCaseDefs = os.path.join(dirOutput, fileAnnotatedCaseDefs)
    annotate_case_definitions.main(fileCaseDefs, fileCodeDescriptions, fileAnnotatedCaseDefs)

    # Extract the case definitions from the file of case definitions.
    caseDefintions, caseNames = parse_conditions.main(fileAnnotatedCaseDefs, validChoices)
