"""Tests for the record_outputter module."""

# Python imports.
import datetime
import json
import os
import unittest

# User imports.
from PatientExtraction import conf


class TestRestrictionApplication(unittest.TestCase):

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
        filePatientData = os.path.join(dirData, "RecordOutputter", "FlatPatientData.tsv")
        fileOutputChoices = os.path.join(dirData, "RecordOutputter", "OutputChoices.json")
        fileExpectedOutput = os.path.join(dirData, "RecordOutputter", "ExpectedOutput.json")

        # Load the patient records.
        cls.patientRecords = {}
        with open(filePatientData, 'r') as fidData:
            for line in fidData:
                chunks = (line.strip()).split('\t')
                patientID = chunks[0]  # The ID of the patient whose record appears on the line.
                patientRecord = json.loads(chunks[1])  # The patient's medical history in JSON format.

                # Convert all dates to datetime objects.
                for i in patientRecord:
                    for j in patientRecord[i]:
                        j["Date"] = datetime.datetime.strptime(j["Date"], "%Y-%m-%d")

                # Save the record.
                cls.patientRecords[patientID] = patientRecord

        # Load the output choices.
        fidOutputChoices = open(fileOutputChoices, 'r')
        cls.outputChoices = json.load(fidOutputChoices)
        fidOutputChoices.close()

        # Load the expected output.
        fidExpectedOutput = open(fileExpectedOutput, 'r')
        cls.expectedOutput = json.load(fidExpectedOutput)
        fidExpectedOutput.close()

    def test_record_outputter(self):
        # Loop through all patients and test that the output for the patient is as expected.
        for i in self.patientRecords:
            # Get the patient information.
            patientRecord = self.patientRecords[i]
            patientOutputChoices = self.outputChoices[i]
            patientExpectedOutput = self.expectedOutput[i]

            # Generate the output for each method and check that it is correct.
            for j in patientOutputChoices:
                generatedOutput = conf.validChoices["Outputs"][j](patientRecord)
                self.assertEqual(generatedOutput, patientExpectedOutput[j])
