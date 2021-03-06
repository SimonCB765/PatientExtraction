"""Functions to select a subset of records from a patient's medical history based on a specified mode.

A typical record will be a dictionary with contents along the lines of:

{
    "Code1": [
        {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
        {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
    ],
    "Code2": [{"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}],
    "Code3": [
        {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""},
        {"Val1": 0, "Val2": 0, "Date": datetime, "Text": ""}
    ]
}

"""


def all_selector(records):
    """Select all associations between a patient and their codes.

    :param records: A patient's medical records. See the module docstring for its format.
    :type records:  dict
    :return:        All associations between a patient and their codes.
    :rtype:         dict

    """

    return dict(records)


def earliest_selector(records):
    """Select the association between a patient and a code that occurred the longest ago.

    This relies on the associations being sorted chronologically, thereby enabling additional loops to be
    bypassed as the earliest association between a given code and a patient is first in the record of associations with
    that code. For example code "A" may have a record of associations like
    "A": [{"Date": "1990-10-30"}, {"Date": "1995-2-8"}, {"Date": "2001-7-23"}]. You can therefore just get the
    association at index 0 to get the earliest association between the patient and code.

    :param records: A patient's medical records. See the module docstring for its format.
    :type records:  dict
    :return:        The association between the patient and code that occurred the longest ago.
    :rtype:         dict

    """

    # Select the earliest association between one of the positive indicator codes and the patient.

    # First find the code that has the earliest association with the patient. This will return not just
    # the earliest association, but all associations between the patient and the earliest occurring code.
    earliestRecord = min(records.items(), key=lambda x: (x[1][0]["Date"], x[0]))

    # Determine the code that occurred earliest, and its association with the patient that caused it to be
    # the earliest occurring code. Due to the way associations are stored (chronologically) the first
    # association in the record is the earliest.
    earliestCode = earliestRecord[0]
    earliestAssociation = earliestRecord[1][0]  # The first (and therefore earliest) association with the code.
    return {earliestCode: [earliestAssociation]}


def latest_selector(records):
    """Select the association between a patient and a code that occurred most recently.

    This relies on the associations being sorted chronologically, thereby enabling additional loops to be
    bypassed as the latest association between a given code and a patient is last in the record of associations with
    that code. For example code "A" may have a record of associations like
    "A": [{"Date": "1990-10-30"}, {"Date": "1995-2-8"}, {"Date": "2001-7-23"}]. You can therefore just get the
    association at index -1 to get the latest association between the patient and code.

    :param records: A patient's medical records. See the module docstring for its format.
    :type records:  dict
    :return:        The association between the patient and code that occurred most recently.
    :rtype:         dict

    """

    # Select the latest association between one of the positive indicator codes and the patient.

    # First find the code that has the latest association with the patient. This will return not just
    # the latest association, but all associations between the patient and the latest occurring code.
    latestRecord = max(records.items(), key=lambda x: (x[1][-1]["Date"], x[0]))

    # Determine the code that occurred latest, and its association with the patient that caused it to be
    # the latest occurring code. Due to the way associations are stored (chronologically) the last
    # association in the record is the latest.
    latestCode = latestRecord[0]
    latestAssociation = latestRecord[1][-1]  # The last (and therefore latest) association with the code.
    return {latestCode: [latestAssociation]}


def max_selector(valType):
    """Generate a function that will perform the selection based on the maximum valType value.

    :param valType:     The type of value to select within the record (i.e. Val1 or Val2). See the module docstring
                            for its format.
    :type valType:      str
    :return:            A function that selects the association between a patient and code that contains the largest
                            valType value.
    :rtype:             function

    """

    def selector(records):
        """Select the association between a patient and a code that contains the largest value.

        :param records: A patient's medical records.
        :type records:  dict
        :return:        The association between the patient and code with the largest value.
        :rtype:         dict

        """

        # Select the positive indicator code that has an association with the patient that contains the
        # greatest valType value.
        maxRecord = max(records.items(), key=lambda x: (max([i[valType] for i in x[1]]), x[0]))

        # Determine the code associated with the max value and its association with the patient that actually has
        # the maximum value.
        maxCode = maxRecord[0]
        maxAssociation = max(maxRecord[1], key=lambda x: x[valType])
        return {maxCode: [maxAssociation]}

    return selector


def min_selector(valType):
    """Generate a function that will perform the selection based on the minimum valType value.

    :param valType:     The type of value to select within the record (i.e. Val1 or Val2). See the module docstring
                            for its format.
    :type valType:      str
    :return:            A function that selects the association between a patient and code that contains the smallest
                            valType value.
    :rtype:             function

    """

    def selector(records):
        """Select the association between a patient and a code that contains the smallest value.

        :param records: A patient's medical records. See the module docstring for its format.
        :type records:  dict
        :return:        The association between the patient and code with the smallest value.
        :rtype:         dict

        """

        # Select the positive indicator code that has an association with the patient that contains the
        # smallest valType value.
        minRecord = min(records.items(), key=lambda x: (min([i[valType] for i in x[1]]), x[0]))

        # Determine the code associated with the min value and its association with the patient that actually has
        # the minimum value.
        minCode = minRecord[0]
        minAssociation = min(minRecord[1], key=lambda x: x[valType])
        return {minCode: [minAssociation]}

    return selector
