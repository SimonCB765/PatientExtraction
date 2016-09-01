"""Functions to select the contents of a medical history to output.

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


def code_outputter(record):
    """Function to output an arbitrary code in the patient's record.

    This function is primarily used when the record contains only one record, i.e. when the mode is one of max, min,
    earliest, latest, etc., as this makes the arbitrariness of the choice immaterial.

    :param record:  A patient's medical record selected for outputting.
    :type record:   dict
    :return:        The contents of the record that should be output.
    :rtype:         str

    """

    # Get an arbitrary code from the patient's record. This will extract the 'first' code from the record dictionary.
    code = next(iter(record))
    return "{:s}".format(code)


def count_outputter(record):
    """Function to output the number of associations in the patient's record.

    This function is primarily used when the record may contain multiple records, i.e. when the mode is all.

    :param record:  A patient's medical record selected for outputting.
    :type record:   dict
    :return:        The contents of the record that should be output.
    :rtype:         str

    """

    # Get the number of associations between the patient and each code in their record (via len), and then sum these
    # numbers.
    count = sum(map(len, record.values()))
    return "{:d}".format(count)


def date_outputter(record):
    """Function to output an arbitrary date in the patient's record.

    This function is primarily used when the record contains only one record, i.e. when the mode is one of max, min,
    earliest, latest, etc., as this makes the arbitrariness of the choice immaterial.

    :param record:  A patient's medical record selected for outputting.
    :type record:   dict
    :return:        The contents of the record that should be output.
    :rtype:         str

    """

    # Get an arbitrary code from the patient's record. This will extract the 'first' code from the record dictionary.
    code = next(iter(record))

    # Get an arbitrary date associated with the code. As records are sorted chronologically, this will get the
    # earliest date in the record that the code was associated with the patient.
    date = record[code][0]["Date"]
    return "{:s}".format(date.strftime("%Y-%m-%d"))


def max_outputter(valType):
    """Generate a function that will output the maximum valType value in the patient's record.

    :param valType:     The type of value to output (i.e. Val1 or Val2).
    :type valType:      str
    :return:            A function that outputs the maximum valType value in the patient's record.
    :rtype:             function

    """

    def outputter(record):
        """Function to output te maximum valType value in the patient's record.

        This function is primarily used when the record may contain multiple records, i.e. when the mode is all.

        :param record:  A patient's medical record selected for outputting.
        :type record:   dict
        :return:        The contents of the record that should be output.
        :rtype:         str

        """

        # Combine all code associations into one list.
        associations = [k for j in record.values() for k in j]

        # Get the code association with the maximum value.
        maxAssociation = max(associations, key=lambda x: x[valType])

        # Return the valType value from this maximum association.
        return "{:.2f}".format(maxAssociation[valType])

    return outputter


def mean_outputter(valType):
    """Generate a function that will output the mean valType value in the patient's record.

    :param valType:     The type of value to output (i.e. Val1 or Val2).
    :type valType:      str
    :return:            A function that outputs the mean valType value in the patient's record.
    :rtype:             function

    """

    def outputter(record):
        """Function to output te mean valType value in the patient's record.

        This function is primarily used when the record may contain multiple records, i.e. when the mode is all.

        :param record:  A patient's medical record selected for outputting.
        :type record:   dict
        :return:        The contents of the record that should be output.
        :rtype:         str

        """

        # Combine all the valType values of the code associations into one list.
        associationValues = [k[valType] for j in record.values() for k in j]

        # Get the mean value over the associations.
        meanValue = sum(associationValues) / len(associationValues)

        # Return the valType value from this mean association.
        return "{:.2f}".format(meanValue)

    return outputter


def median_outputter(valType):
    """Generate a function that will output the median valType value in the patient's record.

    :param valType:     The type of value to output (i.e. Val1 or Val2).
    :type valType:      str
    :return:            A function that outputs the median valType value in the patient's record.
    :rtype:             function

    """

    def outputter(record):
        """Function to output te median valType value in the patient's record.

        This function is primarily used when the record may contain multiple records, i.e. when the mode is all.

        :param record:  A patient's medical record selected for outputting.
        :type record:   dict
        :return:        The contents of the record that should be output.
        :rtype:         str

        """

        # Combine all the valType values of the code associations into one list and sort them.
        associationValues = sorted([k[valType] for j in record.values() for k in j])

        # If there is only one record, then return that record.
        if len(associationValues) == 1:
            return "{:.2f}".format(associationValues[0])

        # Get the median value over the associations.
        middleIndex = len(associationValues) // 2
        if len(associationValues) % 2 == 0:
            # There are an even number of code associations in the patient's record, so the median is the mean of the
            # middle two values
            medianValue = sum(associationValues[middleIndex - 1:middleIndex + 1]) / 2
        else:
            # There are an odd number of code associations in the patient's record, so te median is the middle one.
            medianValue = associationValues[middleIndex]

        # Return the valType value from this median association.
        return "{:.2f}".format(medianValue)

    return outputter


def min_outputter(valType):
    """Generate a function that will output the minimum valType value in the patient's record.

    :param valType:     The type of value to output (i.e. Val1 or Val2).
    :type valType:      str
    :return:            A function that outputs the minimum valType value in the patient's record.
    :rtype:             function

    """

    def outputter(record):
        """Function to output te minimum valType value in the patient's record.

        This function is primarily used when the record may contain multiple records, i.e. when the mode is all.

        :param record:  A patient's medical record selected for outputting.
        :type record:   dict
        :return:        The contents of the record that should be output.
        :rtype:         str

        """

        # Combine all code associations into one list.
        associations = [k for j in record.values() for k in j]

        # Get the code association with the minimum value.
        minAssociation = min(associations, key=lambda x: x[valType])

        # Return the valType value from this minimum association.
        return "{:.2f}".format(minAssociation[valType])

    return outputter


def value_outputter(valType):
    """Generate a function that will output an arbitrary valType value in the patient's record.

    :param valType:     The type of value to output (i.e. Val1 or Val2).
    :type valType:      str
    :return:            A function that outputs an arbitrary valType value in the patient's record.
    :rtype:             function

    """

    def outputter(record):
        """Function to output an arbitrary value in the patient's record.

        This function is primarily used when the record contains only one record, i.e. when the mode is one of max, min,
        earliest, latest, etc., as this makes the arbitrariness of the choice immaterial.

        :param record:  A patient's medical record selected for outputting.
        :type record:   dict
        :return:        The contents of the record that should be output.
        :rtype:         str

        """

        # Get an arbitrary code from the patient's record. This will extract the 'first' code from the record
        # dictionary.
        code = next(iter(record))

        # Get an arbitrary value associated with the code. As records are sorted chronologically, this will get the
        # value associated with the earliest association in the record between the code and the patient.
        value = record[code][0]["Val1"]
        return "{:.2f}".format(value)

    return outputter
