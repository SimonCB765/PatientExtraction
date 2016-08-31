"""Functions to select a subset of records from a patient's medical history based on a specified mode."""


def _all_selector(records):
    """Select all associations between a patient and their codes.

    :param records: A patient's medical records.
    :type records:  dict
    :return:        All associations between a patient and their codes.
    :rtype:         dict

    """

    return dict(records)


def _earliest_selector(records):
    """Select the association between a patient and a code that occurred the longest ago.

    :param records: A patient's medical records.
    :type records:  dict
    :return:        The association between the patient and code that occurred the longest ago.
    :rtype:         dict

    """

    # Select the earliest association between one of the positive indicator codes and the patient.

    # First find the code that has the earliest association with the patient. This will return not just
    # the earliest association, but all associations between the patient and the earliest occurring code.
    earliestRecord = min(records.items(), key=lambda x: x[1][0]["Date"])

    # Determine the code that occurred earliest, and its association with the patient that caused it to be
    # the earliest occurring code. Due to the way associations are stored (chronologically) the first
    # association in the record is the earliest.
    earliestCode = earliestRecord[0]
    earliestAssociation = earliestRecord[1][0]  # The first (and therefore earliest) association with the code.
    return {earliestCode: [earliestAssociation]}


def _latest_selector(records):
    """Select the association between a patient and a code that occurred most recently.

    :param records: A patient's medical records.
    :type records:  dict
    :return:        The association between the patient and code that occurred most recently.
    :rtype:         dict

    """

    # Select the latest association between one of the positive indicator codes and the patient.

    # First find the code that has the latest association with the patient. This will return not just
    # the latest association, but all associations between the patient and the latest occurring code.
    latestRecord = max(records.items(), key=lambda x: x[1][-1]["Date"])

    # Determine the code that occurred latest, and its association with the patient that caused it to be
    # the latest occurring code. Due to the way associations are stored (chronologically) the last
    # association in the record is the latest.
    latestCode = latestRecord[0]
    latestAssociation = latestRecord[1][-1]  # The last (and therefore latest) association with the code.
    return {latestCode: [latestAssociation]}


def _max_selector(records):
    """Select the association between a patient and a code that contains the largest value.

    :param records: A patient's medical records.
    :type records:  dict
    :return:        The association between the patient and code with the largest value.
    :rtype:         dict

    """

    # Select the positive indicator code that has an association with the patient that contains the
    # greatest value.
    maxRecord = max(records.items(), key=lambda x: max([i["Val1"] for i in x[1]]))

    # Determine the code associated with the max value and its association with the patient that actually has
    # the max value.
    maxCode = maxRecord[0]
    maxAssociation = max(maxRecord[1], key=lambda x: x["Val1"])
    return {maxCode: [maxAssociation]}


def _min_selector(records):
    """Select the association between a patient and a code that contains the smallest value.

    :param records: A patient's medical records.
    :type records:  dict
    :return:        The association between the patient and code with the smallest value.
    :rtype:         dict

    """

    # Select the association between one of the positive indicator codes and the patient that
    # contains the smallest value.
    minRecord = min(records.items(), key=lambda x: min([i["Val1"] for i in x[1]]))

    # Determine the code associated with the min value and its association with the patient that actually has
    # the min value.
    minCode = minRecord[0]
    minAssociation = min(minRecord[1], key=lambda x: x["Val1"])
    return {minCode: [minAssociation]}

_selector = {"all": _all_selector,
             "earliest": _earliest_selector,
             "latest": _latest_selector,
             "max": _max_selector,
             "min": _min_selector}


def select_associations(medicalRecord, conditionRestrictions, modes=("all",)):
    """Select information about the associations between a patient and their codes according to modes and restrictions.

    :param medicalRecord:           A patient's medical record.
    :type medicalRecord:            dict
    :param conditionRestrictions:   The data about the condition restrictions.
    :type conditionRestrictions     dict
    :param modes:                   The method(s) for selecting associations between the patient and their codes.
    :type modes:                    list
    :return:                        The selected associations between patients and codes that meet the criteria.
                                        There is one entry in the dictionary per mode used. For each mode key in the
                                        dictionary, the associated value is the dictionary of associations between
                                        the patient and codes that meet the criteria, selected based on the mode.
                                        An example of the return dictionary is:
                                        {
                                            "all":
                                                {
                                                    "C10E": [{"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             {"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             ...
                                                            ]
                                                    "C10F": [{"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             {"Date": datetime, "Text": "..", "Val1": 0.0, "Val2": 0.0},
                                                             ...
                                                            ],
                                                    ...
                                                }
                                            "max": {"XXX": [{"Date": datetime, "Text": "..", "Val1": 5.5, "Val2": 0.0}]}
                                            ...
                                        }
    :rtype:                         dict

    """

    # Remove associations that do not meet the restriction criteria.
    for i in conditionRestrictions:
        # Go through each category of restrictions (values, dates, etc.).
        for j in conditionRestrictions[i]:
            # Filter the patient's record by the current restriction, leaving only those associations
            # that meet the current restriction.
            medicalRecord = {k: [l for l in medicalRecord[k] if j(l[i])] for k in medicalRecord}

    # Filter out codes that have had all associations with the patient removed by the restrictions.
    medicalRecord = {i: medicalRecord[i] for i in medicalRecord if medicalRecord[i]}

    if not medicalRecord:
        # If there are no associations remaining, then return empty dictionaries for each mode.
        return {i: {} for i in modes}

    # Select a subset of the patient's medical record for each mode.
    modeMedicalRecords = {}  # The medical record subsets.
    for mode in modes:
        modeMedicalRecords[mode] = _selector[mode](medicalRecord)

    return modeMedicalRecords
