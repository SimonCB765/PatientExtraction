"""Tests for the patient_extraction module."""

# Python imports.
import os
import unittest

# User imports.
from PatientExtraction import conf
from PatientExtraction import patient_extraction


class TestRestrictionApplication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Perform setup needed for all tests."""

        # Setup global settings-like variables.
        conf.init()
        conf.control_logging(False)  # Turn logging off.

        # Determine the files needed to load the data and the expected results of the tests.
        dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
        dirData = os.path.abspath(os.path.join(dirCurrent, "TestData"))
        cls.dirOutput = os.path.abspath(os.path.join(dirCurrent, "TestData", "TempData", "PatientExtraction"))
        os.makedirs(cls.dirOutput, exist_ok=True)
        cls.filePatientData = os.path.join(dirData, "PatientExtraction", "FlatPatientData.tsv")
        cls.fileCodeDescriptions = os.path.join(dirData, "PatientExtraction", "CodeDescriptions.tsv")
        cls.fileCaseDefinitions = os.path.join(dirData, "PatientExtraction", "CaseDefinitions.txt")
        cls.filePatientSubsetBlank = os.path.join(dirData, "PatientExtraction", "PatientSubsetBlank.txt")
        cls.filePatientSubset = os.path.join(dirData, "PatientExtraction", "PatientSubset.txt")
        cls.fileExpectedOutputBlank = os.path.join(dirData, "PatientExtraction", "ExpectedOutputBlank.txt")
        cls.fileExpectedOutput = os.path.join(dirData, "PatientExtraction", "ExpectedOutput.txt")

    def test_patient_extraction(self):

        # Set the test to output the entire difference between the actual and expected outputs.
        self.maxDiff = None

        # Test without a patient subset being used.
        patient_extraction.main(self.fileCaseDefinitions, self.dirOutput, self.filePatientData,
                                self.fileCodeDescriptions, self.filePatientSubsetBlank)
        fid = open(os.path.join(self.dirOutput, "DataExtraction.tsv"))
        actualOutput = fid.read()
        actualOutput = actualOutput.split('\n')
        fid.close()
        fid = open(self.fileExpectedOutputBlank, 'r')
        expectedOutput = fid.read()
        expectedOutput = expectedOutput.split('\n')
        fid.close()
        self.assertEqual(len(actualOutput), len(expectedOutput))
        for i, j in zip(actualOutput, expectedOutput):
            self.assertEqual(i, j)

        # Test with a patient subset.
        patient_extraction.main(self.fileCaseDefinitions, self.dirOutput, self.filePatientData,
                                self.fileCodeDescriptions, self.filePatientSubset)
        fid = open(os.path.join(self.dirOutput, "DataExtraction.tsv"))
        actualOutput = fid.read()
        actualOutput = actualOutput.split('\n')
        fid.close()
        fid = open(self.fileExpectedOutput, 'r')
        expectedOutput = fid.read()
        expectedOutput = expectedOutput.split('\n')
        fid.close()
        self.assertEqual(len(actualOutput), len(expectedOutput))
        for i, j in zip(actualOutput, expectedOutput):
            self.assertEqual(i, j)
