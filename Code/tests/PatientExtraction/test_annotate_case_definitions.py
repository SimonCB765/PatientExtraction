"""Tests for the record_selector module."""

# Python imports.
import os
import unittest

# User imports.
from PatientExtraction import conf
from PatientExtraction import annotate_case_definitions


class TestAnnotateCaseDefinitions(unittest.TestCase):

    longMessage = False  # Do not display te normal failure message when a custom one is given.

    @classmethod
    def setUpClass(cls):
        """Perform setup needed for all tests.

        This just consists of processing the test data into the correct format.

        """

        # Setup global settings-like variables.
        conf.init()

        # Determine the files needed to load the data and the expected results of the tests.
        dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
        dirData = os.path.abspath(os.path.join(dirCurrent, "TestData"))
        fileData = os.path.join(dirData, "CaseDefinitions", "CaseDefinitions.txt")
        fileOutput = os.path.join(dirData, "CaseDefinitions", "AnnotatedCaseDefinitions.txt")
        fileCodeDescriptions = os.path.join(dirData, "CaseDefinitions", "CodeDescriptions.tsv")

        # Load the case definitions.
        fileCaseDefinitions = os.path.join(dirData, "TempData", "TempAnnotations.txt")
        annotate_case_definitions.main(fileData, fileCodeDescriptions, fileCaseDefinitions, isLoggingEnabled=False)
        fidCaseDefs = open(fileCaseDefinitions, 'r')
        cls.annotatedCaseDefs = fidCaseDefs.read()
        fidCaseDefs.close()

        # Load the expected output.
        fidOutput = open(fileOutput, 'r')
        cls.expectedOutput = fidOutput.read()
        fidOutput.close()

    def test_annotation(self):
        # Split the annotation and the expected output into lists containing their lines.
        annotated = self.annotatedCaseDefs.split('\n')
        expected = self.expectedOutput.split('\n')
        minLength = min(len(annotated), len(expected))  # Determine the shortest of the two lists.

        # Test that each individual line of the annotation is the same.
        for i in range(minLength):
            self.assertEqual(annotated[i], expected[i], "Line {:d} is not the same.".format(i + 1))

        # Test that the annotations are the same length.
        self.assertCountEqual(annotated, expected)

        # Test that the entire annotated file is equal as a string in one go.
        self.assertEqual(self.annotatedCaseDefs, self.expectedOutput)
