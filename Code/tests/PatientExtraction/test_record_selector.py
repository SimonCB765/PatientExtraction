"""Tests for the record_selector module."""

# Python imports.
import operator
import unittest

# User imports.
from PatientExtraction import restriction_comparator_generators


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
