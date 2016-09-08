"""Tests for the parse_case_definitions module."""

# Python imports.
import datetime
import json
import os
import unittest

# User imports.
from PatientExtraction import conf
from PatientExtraction import parse_case_definitions
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
        fileData = os.path.join(dirData, "CaseDefinitions", "AnnotatedCaseDefinitions.txt")
        fileOutput = os.path.join(dirData, "CaseDefinitions", "ExpectedOutput.json")

        # Load the case definitions.
        cls.caseDefinitions, cls.caseNames = parse_case_definitions.main(fileData)

        # Load the expected output.
        fidOutput = open(fileOutput, 'r')
        cls.expectedOutput = json.load(fidOutput)
        fidOutput.close()
        for i in cls.expectedOutput:
            # Convert the list of codes to a set.
            cls.expectedOutput[i]["Codes"] = set(cls.expectedOutput[i]["Codes"])

            # Create date comparisons.
            cls.expectedOutput[i]["Restrictions"]["Date"] = [
                [datetime.datetime.strptime(k, "%Y-%m-%d") for k in j]
                for j in cls.expectedOutput[i]["Restrictions"]["Date"]
            ]
            cls.expectedOutput[i]["Restrictions"]["DateComps"] = [
                restriction_comparator_generators.date_generator(*j)
                for j in cls.expectedOutput[i]["Restrictions"]["Date"]
            ]

            # Convert Val1 values to value comparisons.
            cls.expectedOutput[i]["Restrictions"]["Val1"] = [
                restriction_comparator_generators.value_generator(j[1], conf.validChoices["Operators"][j[0]])
                for j in cls.expectedOutput[i]["Restrictions"]["Val1"]
            ]

            # Convert Val2 values to value comparisons.
            cls.expectedOutput[i]["Restrictions"]["Val2"] = [
                restriction_comparator_generators.value_generator(j[1], conf.validChoices["Operators"][j[0]])
                for j in cls.expectedOutput[i]["Restrictions"]["Val2"]
            ]

    def test_case_parsing(self):
        # First ensure that the outputs have the same case names.
        self.assertCountEqual(self.caseNames, self.caseDefinitions)
        self.assertCountEqual(self.caseDefinitions, self.expectedOutput)

        for i in self.caseNames:
            # Check that the codes are all the same for the expected and actual output.
            self.assertEqual(self.caseDefinitions[i]["Codes"], self.expectedOutput[i]["Codes"])

            # Check that the modes are all the same for the expected and actual output.
            self.assertEqual(self.caseDefinitions[i]["Modes"], self.expectedOutput[i]["Modes"])

            # Check that the output methods are all the same for the expected and actual output.
            self.assertEqual(self.caseDefinitions[i]["Outputs"], self.expectedOutput[i]["Outputs"])

            # Check that the date restrictions are all the same for the expected and actual output.
            annotatedDateComps = self.caseDefinitions[i]["Restrictions"]["Date"]
            expectedDateComps = self.expectedOutput[i]["Restrictions"]["DateComps"]
            expectedDates = self.expectedOutput[i]["Restrictions"]["Date"]
            self.assertEqual(len(annotatedDateComps), len(expectedDateComps))
            for j, k, l in zip(annotatedDateComps, expectedDateComps, expectedDates):
                annotatedCellContents = [m.cell_contents for m in j.__closure__]
                expectedCellContents = [m.cell_contents for m in k.__closure__]
                if len(l) == 2:
                    # If there were two dates specified for the comparison check them both.
                    self.assertCountEqual(annotatedCellContents, expectedCellContents)
                else:
                    # If there was only one date specified for the comparison, then the comparison is from a start date
                    # to the present. As the comparison functions being compared (the annotated and expected) are not
                    # created at the exact same moment, their end dates will be slightly different
                    # (as datetime.datetime.now() will have slightly different values for the seconds). In this case
                    # only compare the first dates.
                    # The start date is cell index 1, not 0 as might be expected.
                    self.assertEqual(annotatedCellContents[1], expectedCellContents[1])

            # Check that the Val1 restrictions are all the same for the expected and actual output.
            annotatedVal1Comps = self.caseDefinitions[i]["Restrictions"]["Val1"]
            expectedVal1Comps = self.expectedOutput[i]["Restrictions"]["Val1"]
            self.assertEqual(len(annotatedVal1Comps), len(expectedVal1Comps))
            for j, k in zip(annotatedVal1Comps, expectedVal1Comps):
                annotatedCellContents = [l.cell_contents for l in j.__closure__]
                expectedCellContents = [l.cell_contents for l in k.__closure__]
                self.assertEqual(annotatedCellContents, expectedCellContents)

            # Check that the Val2 restrictions are all the same for the expected and actual output.
            annotatedVal2Comps = self.caseDefinitions[i]["Restrictions"]["Val2"]
            expectedVal2Comps = self.expectedOutput[i]["Restrictions"]["Val2"]
            self.assertEqual(len(annotatedVal2Comps), len(expectedVal2Comps))
            for j, k in zip(annotatedVal2Comps, expectedVal2Comps):
                annotatedCellContents = [l.cell_contents for l in j.__closure__]
                expectedCellContents = [l.cell_contents for l in k.__closure__]
                self.assertEqual(annotatedCellContents, expectedCellContents)
