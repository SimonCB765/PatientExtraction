"""Function to generate the mappings between conditions and codes from the user supplied case definitions."""

# Python imports.
from collections import defaultdict
import re


def main(fileInput, fileCodeDescriptions, fileOutput, fileLog):
    """

    :param fileInput:               The location of the input file containing the case definitions.
    :type fileInput:                str
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
                                    2) A mapping from conditions to information about the mde, output and restrictions
                                        to be used when finding patients with the condition. The three entries for each
                                        condition are:
                                        "Mode" - a string indicating the patient's codes that should be selected
                                        "Out" - a list of strings indicating what should be output about the patient
                                        "Restrictions" - a list of restrictions on which patients should be deemed to
                                            have the condition
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

    #--------------------------------------------------------------#
    # Generate Code Condition Mappings and Annotate the Input File #
    #--------------------------------------------------------------#
    # Create the mapping from codes to the conditions that it is a positive and negative indicator of.
    mapCodeToCondition = defaultdict(lambda: {"Positive": set(), "Negative": set()})
    # Create the mapping from conditions to information about the extraction mode, desired output and the
    # restrictions on patients having the condition (e.g. date ranges, values, etc.).
    conditionData = {}
    currentCondition = ""  # The condition for which the codes are currently being gathered.
    with open(fileInput, 'r') as fidInput, open(fileOutput, 'w') as fidOutput, open(fileLog, 'a') as fidLog:
        for line in fidInput:
            if line[0] == '#':
                # Found the start of a condition.
                fidOutput.write(line)
                line = line[1:].strip()
                currentCondition = re.sub("\s+", '_', line)

                # Initialise the mapping recording mode, output and patient restrictions for this condition.
                conditionData[currentCondition] = {"Mode": "all", "Out": ["count"], "Restrictions": []}
            elif line[0] == '>':
                # Found the start of mode, output or restriction information.
                fidOutput.write(line)
                controlInfo = line[1:].strip()

                if controlInfo[:4].lower() == "mode":
                    chunks = controlInfo.split()
                    conditionData[currentCondition]["Mode"] = chunks[1]
                elif controlInfo[:3].lower() == "out":
                    chunks = controlInfo.split()
                    conditionData[currentCondition]["Out"] = chunks[1:]
                else:
                    #TODO handle restrictions properly.
                    pass
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

    return mapCodeToCondition, conditionData
