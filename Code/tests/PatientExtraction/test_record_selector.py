"""Tests for the record_selector module."""

# Python imports.
import datetime
import json
import os
import unittest

# User imports.
from PatientExtraction import record_selector


class TestSelectors(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Perform setup needed for all tests.

        This just consists of processing the test data into the correct format.

        """

        # Determine the files needed to load the data and the expected results of the tests.
        dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
        dirData = os.path.abspath(os.path.join(dirCurrent, "TestData"))
        fileData = os.path.join(dirData, "RecordSelectorData.json")
        fileOutput = os.path.join(dirData, "RecordSelectorOutput.json")

        # Load the patient data (replacing all dates in their string format with datetime.datetime objects).
        fidData = open(fileData, 'r')
        cls.medicalRecords = json.load(fidData)
        fidData.close()
        for i in cls.medicalRecords:
            for j in cls.medicalRecords[i]:
                for k in cls.medicalRecords[i][j]:
                    k["Date"] = datetime.datetime.strptime(k["Date"], "%Y-%m-%d")

        # Load the expected results of performing the selections (replacing all dates in their string format with
        # datetime.datetime objects).
        fidOutput = open(fileOutput, 'r')
        cls.expectedOutput = json.load(fidOutput)
        fidOutput.close()
        for i in cls.expectedOutput:
            for j in cls.expectedOutput[i]:
                for k in cls.expectedOutput[i][j]:
                    for l in cls.expectedOutput[i][j][k]:
                        l["Date"] = datetime.datetime.strptime(l["Date"], "%Y-%m-%d")

    def test_all_selector(self):
        """Test the mode selector that extracts all associations in the patient's history."""

        for i in self.medicalRecords:
            self.assertDictEqual(record_selector.all_selector(self.medicalRecords[i]), self.medicalRecords[i])

    def test_earliest_selector(self):
        """Test the mode extractor that extracts the earliest association in the patient's history."""

        for i in self.medicalRecords:
            self.assertDictEqual(record_selector.earliest_selector(self.medicalRecords[i]),
                                 self.expectedOutput["earliest"][i])

    def test_latest_selector(self):
        """Test the mode extractor that extracts the most recent association in the patient's history."""

        for i in self.medicalRecords:
            self.assertDictEqual(record_selector.latest_selector(self.medicalRecords[i]),
                                 self.expectedOutput["latest"][i])

    def test_max_selector(self):
        """Test the mode extractor that extracts the association in the patient's history with the maximum value."""

        # Create max selectors for Val1 and Val2.
        max1Selector = record_selector.max_selector("Val1")
        max2Selector = record_selector.max_selector("Val2")

        # Max selection for Val1.
        for i in self.medicalRecords:
            self.assertDictEqual(max1Selector(self.medicalRecords[i]), self.expectedOutput["max1"][i])

        # Max selection for Val2.
        for i in self.medicalRecords:
            self.assertDictEqual(max2Selector(self.medicalRecords[i]), self.expectedOutput["max2"][i])

    def test_min_selector(self):
        """Test the mode extractor that extracts the association in the patient's history with the minimum value."""

        # Create min selectors for Val1 and Val2.
        min1Selector = record_selector.min_selector("Val1")
        min2Selector = record_selector.min_selector("Val2")

        # Max selection for Val1.
        for i in self.medicalRecords:
            self.assertDictEqual(min1Selector(self.medicalRecords[i]), self.expectedOutput["min1"][i])

        # Max selection for Val2.
        for i in self.medicalRecords:
            self.assertDictEqual(min2Selector(self.medicalRecords[i]), self.expectedOutput["min2"][i])
