"""Tests for the record_selector module."""

# Python imports.
import datetime
import json
import os
import unittest

# User imports.
from PatientExtraction import conf
from PatientExtraction.patient_extraction import apply_restrictions
from PatientExtraction import restriction_comparator_generators


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
        fileData = os.path.join(dirData, "ApplyRestrictions", "Data.json")
        fileOutput = os.path.join(dirData, "ApplyRestrictions", "ExpectedOutput.json")

        # Load the patient data (replacing all dates in their string format with datetime.datetime objects) and the
        # restriction information (replacing all value by restriction comparison functions).
        fidData = open(fileData, 'r')
        inputData = json.load(fidData)
        fidData.close()
        cls.medicalRecords = {}
        cls.restrictions = {}
        for i in inputData:
            # Process the patient medical record data.
            for j in inputData[i]["Record"]:
                for k in inputData[i]["Record"][j]:
                    k["Date"] = datetime.datetime.strptime(k["Date"], "%Y-%m-%d")
            cls.medicalRecords[i] = inputData[i]["Record"]

            # Save the restrictions.
            cls.restrictions[i] = inputData[i]["Restrictions"]

            # Create date comparisons.
            cls.restrictions[i]["Date"] = [
                [datetime.datetime.strptime(k, "%Y-%m-%d") for k in j] for j in cls.restrictions[i]["Date"]
            ]
            cls.restrictions[i]["Date"] = [
                restriction_comparator_generators.date_generator(*j) for j in cls.restrictions[i]["Date"]
            ]

            # Convert Val1 values to value comparisons.
            cls.restrictions[i]["Val1"] = [
                restriction_comparator_generators.value_generator(j[1], conf.validChoices["Operators"][j[0]])
                for j in cls.restrictions[i]["Val1"]
            ]

            # Convert Val2 values to value comparisons.
            cls.restrictions[i]["Val2"] = [
                restriction_comparator_generators.value_generator(j[1], conf.validChoices["Operators"][j[0]])
                for j in cls.restrictions[i]["Val2"]
            ]

        # Load the expected results of performing the selections (replacing all dates in their string format with
        # datetime.datetime objects).
        fidOutput = open(fileOutput, 'r')
        cls.expectedOutput = json.load(fidOutput)
        fidOutput.close()
        for i in cls.expectedOutput:
            for j in cls.expectedOutput[i]:
                for k in cls.expectedOutput[i][j]:
                    k["Date"] = datetime.datetime.strptime(k["Date"], "%Y-%m-%d")

    def test_apply_restrictions(self):
        # Loop through all patients and test that the result of applying the restriction to their record is correct.
        for i in self.medicalRecords:
            # Get the patient information.
            patientRecord = self.medicalRecords[i]
            patientRestrictions = self.restrictions[i]

            # Apply the restrictions.
            restrictedRecord = apply_restrictions(patientRecord, patientRestrictions)

            # Check that the result is as expected.
            self.assertEqual(restrictedRecord, self.expectedOutput[i])
