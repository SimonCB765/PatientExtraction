"""Function to generate the mappings between conditions and codes from the user supplied case definitions."""

# Python imports.
from collections import defaultdict
import datetime
import operator
import re


def main(fileInput, fileCodeDescriptions, fileOutput, fileLog, validModeChoices, validOutputChoices):
    """

    :param fileInput:               The location of the input file containing the case definitions.
    :type fileInput:                str
    :param fileCodeDescriptions:    The location of the file containing the mapping of codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param fileOutput:              The location of the file to write the annotated input file to.
    :type fileOutput:               str
    :param fileLog:                 The location of the log file.
    :type fileLog:                  str
    :param validModeChoices:        The valid modes for choosing selecting codes.
    :type validModeChoices:         list
    :param validOutputChoices:      The valid output options for writing out the results of the patient extraction.
    :type validOutputChoices:       set
    :return:                        1) A mapping from conditions to the codes that are positive and negative indicators
                                        of it. Each condition in the dictionary has as its entry a dictionary
                                        containing two sets:
                                        "Positive" - the codes that are positive indicators for the condition
                                        "Negative" - the codes that are negative indicators for the condition
                                    2) A mapping from conditions to information about the mde, output and restrictions
                                        to be used when finding patients with the condition. The three entries for each
                                        condition are:
                                        "Mode" - a string indicating the patient's codes that should be selected
                                        "Out" - a list of strings indicating what should be output about the patient
                                        "Restrictions" - a list of restrictions on which patients should be deemed to
                                            have the condition
                                    3) The conditions that the user has requested patients data for in the order that
                                        they appear in the input file.
    :rtype:                         dict, dict, list

    """

    #--------------------------------------#
    # Load the Code to Description Mapping #
    #--------------------------------------#
    mapCodeToDescription = {}
    with open(fileCodeDescriptions, 'r') as fidCodeDescriptions:
        for line in fidCodeDescriptions:
            line = line.strip()
            chunks = line.split('\t')
            mapCodeToDescription[chunks[0]] = chunks[1]

    #--------------------------------------------------------------#
    # Generate Code Condition Mappings and Annotate the Input File #
    #--------------------------------------------------------------#
    conditionsFound = []  # List of the conditions the user requested patient data for.
    # Create the mapping from conditions to the codes that are positive and negative indicators of it.
    mapConditionToCode = defaultdict(lambda: {"Positive": set(), "Negative": set()})
    # Create the mapping from conditions to information about the extraction mode, desired output and the
    # restrictions on patients having the condition (e.g. date ranges, values, etc.).
    conditionData = {}
    currentCondition = ""  # The condition for which the codes are currently being gathered.
    with open(fileInput, 'r') as fidInput, open(fileOutput, 'w') as fidOutput, open(fileLog, 'a') as fidLog:
        for line in fidInput:
            line = line.strip()
            if not line:
                # The line is empty.
                pass
            elif line[0] == '#':
                # Found the start of a condition.
                fidOutput.write(line)
                line = line[1:].strip()
                currentCondition = re.sub("\s+", '_', line)
                conditionsFound.append(currentCondition)

                # Initialise the mapping recording mode, output and patient restrictions for this condition.
                conditionData[currentCondition] = {"Mode": "all",
                                                   "Out": ["count"],
                                                   "Restrictions": {"Date": [], "Val1": []}}
            elif line[0] == '>':
                # Found the start of mode, output or restriction information.
                fidOutput.write(line)
                controlInfo = line[1:].strip().lower()

                if controlInfo[:4] == "mode":
                    # A line recording the mode to use for the condition was found.
                    chunks = controlInfo.split()
                    mode = chunks[1]
                    if mode not in validModeChoices:
                        # An invalid mode choice was found.
                        fidLog.write(
                            "WARNING: Mode {0:s} for condition {1:s} is not recognised. Replacing with mode 'ALL'.\n"
                                .format(mode, currentCondition))
                        conditionData[currentCondition]["Mode"] = "all"
                    else:
                        # The mode is valid.
                        conditionData[currentCondition]["Mode"] = chunks[1]
                elif controlInfo[:3] == "out":
                    # A line recording the output to use for the condition was found.
                    chunks = controlInfo.split()
                    outChoices = [i for i in chunks[1:]]
                    invalidOutputChoices = set(outChoices).difference(validOutputChoices)
                    if invalidOutputChoices:
                        # An invalid output choice was supplied.
                        fidLog.write(
                            "WARNING: Invalid output choice(s) {0:s} for condition {1:s} were not recognised and have "
                            "been ignored.\n"
                                .format(','.join([str(i) for i in invalidOutputChoices]), currentCondition))
                        conditionData[currentCondition]["Out"] = set(outChoices).intersection(validOutputChoices)
                    else:
                        # There are no invalid output choices specified.
                        conditionData[currentCondition]["Out"] = outChoices
                else:
                    # A line recording a restriction to use for the condition was found.
                    chunks = re.split("\s+", controlInfo)
                    if "from" in controlInfo:
                        # The restriction involves dates.
                        startDate = datetime.datetime.strptime(chunks[1], "%Y-%m-%d")
                        endDate = datetime.datetime.strptime(chunks[3], "%Y-%m-%d")
                        if endDate < startDate:
                            fidLog.write(
                                "WARNING: End date before start date for condition {0:s}'s restriction line \"{1:s}\". "
                                "The restriction has been ignored.\n".format(currentCondition, controlInfo))
                        else:
                            # Create the function to use to perform the restriction.
                            comparisonFunc = lambda x: operator.le(x, endDate) and operator.ge(x, startDate)
                            conditionData[currentCondition]["Restrictions"]["Date"].append(comparisonFunc)
                    elif "value" in controlInfo:
                        # The restriction involves values.
                        if len(chunks) != 3:
                            # The restriction is not of the correct form.
                            fidLog.write(
                                "WARNING: The value restriction \"{0:s}\" for condition {1:s} is not formatted "
                                "correctly and has been ignored.\n".format(controlInfo, currentCondition))
                        else:
                            # The restriction has the correct number of parts.
                            if chunks[1] not in ['<', "<=", '>', ">="]:
                                # The operator is missing.
                                fidLog.write(
                                    "WARNING: The value restriction \"{0:s}\" for condition {1:s} should have one of "
                                    "<, <=, > or >= as the 2nd element. The restriction has been ignored.\n"
                                        .format(controlInfo, currentCondition))
                            try:
                                value = float(chunks[2])
                                comparisonFunc = None  # The function to use to perform the restriction.
                                if chunks[1] == '<':
                                    comparisonFunc = lambda x: operator.lt(x, value)
                                elif chunks[1] == "<=":
                                    comparisonFunc = lambda x: operator.le(x, value)
                                elif chunks[1] == '>':
                                    comparisonFunc = lambda x: operator.gt(x, value)
                                elif chunks[1] == ">=":
                                    comparisonFunc = lambda x: operator.ge(x, value)
                                conditionData[currentCondition]["Restrictions"]["Val1"].append(comparisonFunc)
                            except ValueError:
                                # The value supplied could not be converted to a float.
                                fidLog.write(
                                    "WARNING: The value restriction \"{0:s}\" for condition {1:s} should have a number "
                                    "as the 3rd element. The restriction has been ignored.\n"
                                        .format(controlInfo, currentCondition))
                    else:
                        # The restriction is not recognised.
                        fidLog.write(
                            "WARNING: The mode, output or restriction line \"{0:s}\" for condition {1:s} was not "
                            "recognised and has been ignored.\n".format(controlInfo, currentCondition))
            else:
                # Found a code for the current condition.
                code = line.strip().replace('.', '')

                # Determine if the code is a negated code.
                isNegativeCode = False
                negationIndicator = ''
                if code[0] == '-':
                    # Found a negated code
                    isNegativeCode = True
                    negationIndicator = '-'
                    code = code[1:]

                # Determine if the code needs expanding to include child codes.
                if code[-1] == '%':
                    # Found a code that needs expanding to include child codes.
                    code = code[:-1]
                    codeList = [i for i in mapCodeToDescription if i[:len(code)] == code]
                else:
                    # Found a code that does not need expanding to include child codes.
                    codeList = [code]

                # Record that these codes are indicators for the current condition and write out the case definition
                # input file annotated with code descriptions.
                for i in codeList:
                    # Add the code as an indicator for the current condition.
                    mapConditionToCode[currentCondition]["Negative" if isNegativeCode else "Positive"].add(i)

                    # Write out the code and its description.
                    if i in mapCodeToDescription:
                        # The code is in the description mapping.
                        fidOutput.write("{0:s}{1:.<5}\t{2:s}\n".format(negationIndicator, i, mapCodeToDescription[i]))
                    else:
                        # The code has no known description.
                        fidOutput.write("{0:s}{1:.<5}\tCode not recognised\n".format(negationIndicator, i))
                        fidLog.write("WARNING: Code {0:s} was not found in the dictionary.\n".format(i))

    return mapConditionToCode, conditionData, conditionsFound
