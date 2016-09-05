"""Closures to generate comparison functions for the value- and date-based restrictions."""

# Python imports.
import datetime


def date_generator(startDate, endDate=None):
    """Generate a function for restricting extracted data based on the date of the code's association with a patient.

    :param startDate:   The beginning date for the restriction.
    :type startDate:    datetime.datetime
    :param endDate:     The end date for the restriction.
    :type endDate:      datetime.datetime
    :return:            A function that will return true only for dates between the two input dates.
    :rtype:             function

    """

    if not endDate:
        # If there is no end date specified, then set the end date to today's date.
        endDate = datetime.datetime.now()

    def date_comparator(date):
        """Check whether a date falls in a given range.

        :param date:    The date to check.
        :type date:     datetime.datetime
        :return:        Whether the input date falls within the range.
        :rtype:         bool

        """

        return startDate <= date <= endDate

    return date_comparator


def value_generator(comparatorValue, comparison):
    """Generate a function for restricting extracted data based on the value of the code's association with a patient.

    The comparison performed is always x OP ref, where ref is the reference/comparator value and x the variable to
    compare against it, i.e. x < 3, y >= 5, etc.

    :param comparatorValue:     The reference value to compare against.
    :type comparatorValue:      float
    :param comparison:          The comparison to perform.
    :type comparison:           function
    :return:                    A function that will return true only when its input value meets the restriction.
    :rtype:                     function

    """

    def value_comparator(value):
        """Check whether a value meets the restriction specified by the comparator value.

        :param value:   The value to compare against the reference value.
        :type value:    float
        :return:        Whether the input value meets the restriction.
        :rtype:         bool

        """

        return comparison(value, comparatorValue)

    return value_comparator
