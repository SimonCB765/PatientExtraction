"""Perform the extraction of patients according to supplied case definitions."""

# Python imports.
import os

# User imports.
from . import annotate_case_definitions


def main(fileInput, dirOutput, filePatientData, fileCodeDescriptions, validChoices):
    """Run the patient extraction.

    :param fileInput:               The location of the input file containing the case definitions.
    :type fileInput:                str
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
    fileAnnotatedInput = os.path.split(fileInput)[1]
    fileAnnotatedInput = fileAnnotatedInput.split('.')[0] + "_Annotated." + fileAnnotatedInput.split('.')[1]
    fileAnnotatedInput = os.path.join(dirOutput, fileAnnotatedInput)
    annotate_case_definitions.main(fileInput, fileCodeDescriptions, fileAnnotatedInput)
