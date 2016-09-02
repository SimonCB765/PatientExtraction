"""Tests for the restriction_comparator_generators module."""

# Python imports.
import calendar
import datetime
import operator
import random
import unittest

# User imports.
from PatientExtraction import restriction_comparator_generators


class TestDateComparator(unittest.TestCase):

    @staticmethod
    def generate_date(startYear=1900, endYear=2010):
        """Generate a random date between two years.

        :param startYear:   The minimum year in which the date can occur.
        :type startYear:    int
        :param endYear:     The maximum year in which the date can occur.
        :type endYear:      int
        :return:            The generated date.
        :rtype:             datetime.datetime

        """

        year = random.randint(startYear, endYear)
        month = random.randint(1, 12)
        daysInMonth = calendar.monthrange(year, month)[1]
        day = random.randint(1, daysInMonth)
        return datetime.datetime(year, month, day)

    def test_comp_func_generation(self):
        # Generate dates that should work.
        for i in range(100):
            startDate = self.generate_date(startYear=1900, endYear=2000)
            endDate = self.generate_date(startYear=startDate.year + 10, endYear=2010)
            compFunc = restriction_comparator_generators.date_generator(startDate, endDate)
            testDate = self.generate_date(startYear=startDate.year + 1, endYear=endDate.year - 1)
            self.assertTrue(compFunc(testDate))

        # Generate dates that should fail as they occur before the start year.
        for i in range(100):
            startDate = self.generate_date(startYear=1900, endYear=2000)
            endDate = self.generate_date(startYear=startDate.year + 10, endYear=2010)
            compFunc = restriction_comparator_generators.date_generator(startDate, endDate)
            testDate = self.generate_date(startYear=1800, endYear=startDate.year - 1)
            self.assertFalse(compFunc(testDate))

        # Generate dates that should fail as they occur after the end year.
        for i in range(100):
            startDate = self.generate_date(startYear=1900, endYear=2000)
            endDate = self.generate_date(startYear=startDate.year + 10, endYear=2010)
            compFunc = restriction_comparator_generators.date_generator(startDate, endDate)
            testDate = self.generate_date(startYear=endDate.year + 1, endYear=3000)
            self.assertFalse(compFunc(testDate))

        # Test some random dates.
        for i in range(100):
            startDate = self.generate_date()
            endDate = self.generate_date()
            compFunc = restriction_comparator_generators.date_generator(startDate, endDate)
            testDate = self.generate_date()
            if startDate <= testDate <= endDate:
                self.assertTrue(compFunc(testDate))
            else:
                self.assertFalse(compFunc(testDate))


class TestValueComparator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Define operators as they are in __main__.py
        cls.validOperators = {'>': operator.gt, ">=": operator.ge, '<': operator.lt, "<=": operator.le}

    def test_comp_func_generation(self):
        # Test less than generation, e.g. x < 3, x < 10.
        for i in range(-10, 20):
            compFunc = restriction_comparator_generators.value_generator(i, self.validOperators['<'])
            for j in range(-15, 25):
                if j < i:
                    self.assertTrue(compFunc(j))
                else:
                    self.assertFalse(compFunc(j))

        # Test less than or equal to generation, e.g. x <= 3, x <= 10.
        for i in range(-10, 20):
            compFunc = restriction_comparator_generators.value_generator(i, self.validOperators['<='])
            for j in range(-15, 25):
                if j <= i:
                    self.assertTrue(compFunc(j))
                else:
                    self.assertFalse(compFunc(j))

        # Test greater than generation, e.g. x > 3, x > 10.
        for i in range(-10, 20):
            compFunc = restriction_comparator_generators.value_generator(i, self.validOperators['>'])
            for j in range(-15, 25):
                if j > i:
                    self.assertTrue(compFunc(j))
                else:
                    self.assertFalse(compFunc(j))

        # Test greater than or equal to generation, e.g. x >= 3, x >= 10.
        for i in range(-10, 20):
            compFunc = restriction_comparator_generators.value_generator(i, self.validOperators['>='])
            for j in range(-15, 25):
                if j >= i:
                    self.assertTrue(compFunc(j))
                else:
                    self.assertFalse(compFunc(j))
