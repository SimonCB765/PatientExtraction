"""Function to generate the mappings between conditions and codes from the user supplied case definitions."""

# Python imports.
from collections import defaultdict


def main(fileInput, filePatientsWithCodes, fileCodeDescriptions, fileOutput, fileLog):
    """

    :param fileInput:               The location of the input file containing the case definitions.
    :type fileInput:                str
    :param filePatientsWithCodes:   The location of the file containing the mapping from codes to patients with them.
    :type filePatientsWithCodes:    str
    :param fileCodeDescriptions:    The location of the file containing the mapping of codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param fileOutput:              The location of the file to write the annotated input file to.
    :type fileOutput:               str
    :param fileLog:                 The location of the log file.
    :type fileLog:                  str
    :return:                        1) A mapping from codes to the conditions that they are positive and negative
                                        indicators of. Each code in the dictionary has as its entry a dictionary
                                        containing two sets:
                                        "Positive" - the conditions for which it is a positive indicator
                                        "Negative" - the conditions for which it is a negative indicator
                                    2) A mapping from conditions to the restrictions they place on patients having it.
                                        For example, a code for the condition must be in a date range, or a value
                                        associated with a positive indicator code for the condition must be in a range.
    :rtype:                         dict, dict

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

    #----------------------------------#
    # Load the Code to Patient Mapping #
    #----------------------------------#
    mapCodeToPatients = {}
    with open(filePatientsWithCodes, 'r') as fidPatientsWithCodes:
        for line in fidPatientsWithCodes:
            line = line.strip()
            chunks = line.split('\t')
            mapCodeToPatients[chunks[0]] = set(chunks[1].split(','))

    #--------------------------------------------------------------#
    # Generate Code Condition Mappings and Annotate the Input File #
    #--------------------------------------------------------------#
    # Create the mapping from codes to the conditions that it is a positive and negative indicator of.
    mapCodeToCondition = defaultdict(lambda: {"Positive": set(), "Negative": set()})
    # Create the mapping from conditions to the list of restrictions on patients having the condition
    # (e.g. date ranges, values, etc.).
    conditionRestrictions = {}
    currentCondition = ""  # The condition for which the codes are currently being gathered.
    with open(fileInput, 'r') as fidInput, open(fileOutput, 'w') as fidOutput, open(fileLog, 'a') as fidLog:
        for line in fidInput:
            if line[0] == '#':
                # Found the start of a condition.
                fidOutput.write(line)
                currentCondition = line[1:].strip().replace(' ', '_')
                conditionRestrictions[currentCondition] = []  # Initialise the condition to having no restrictions.
            elif line[0] == '>':
                # Found the start of a restriction.
                fidOutput.write(line)
                restriction = line[1:].strip()
                #TODO handle restrictions properly.
                #conditionRestrictions[currentCondition].append(restriction)
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
                    mapCodeToCondition[i]["Negative" if isNegativeCode else "Positive"].add(currentCondition)

                    # Write out the code and its description.
                    if i in mapCodeToDescription:
                        # The code is in the description mapping.
                        fidOutput.write("{0:s}{1:.<5}\t{2:s}\n".format(negationIndicator, i, mapCodeToDescription[i]))
                    else:
                        # The code has no known description.
                        fidOutput.write("{0:s}{1:.<5}\tCode not recognised\n".format(negationIndicator, i))
                        fidLog.write("WARNING: Code {0:s} was not found in the dictionary.\n".format(i))

    return mapCodeToCondition, conditionRestrictions
