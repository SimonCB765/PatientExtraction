"""Annotate a file of case definitions by expanding all defining codes."""

# Python imports.
import datetime
import logging
import re

# Globals.
LOGGER = logging.getLogger(__name__)


def main(fileDefinitions, fileCodeDescriptions, fileAnnotateDefinitions, validChoices):
    """Annotate a file of case definitions by expanding all defining codes.

    :param fileDefinitions:         The location of the file containing the case definitions.
    :type fileDefinitions:          str
    :param fileCodeDescriptions:    The location of the file containing the mapping of codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param fileAnnotateDefinitions: The location of the file to write the annotated input file to.
    :type fileAnnotateDefinitions:  str
    :param validChoices:            The valid modes, outputs and operators that can appear in the case definition file.
    :type validChoices:             dict

    """

    # ==================================== #
    # Load the Code to Description Mapping #
    # ==================================== #
    mapCodeToDescription = {}
    with open(fileCodeDescriptions, 'r') as fidCodeDescriptions:
        for line in fidCodeDescriptions:
            line = line.strip()
            chunks = line.split('\t')
            mapCodeToDescription[chunks[0]] = chunks[1]

    # ============================= #
    # Annotate the Case Definitions #
    # ============================= #
    codeMatcher = re.compile("^-?[a-zA-Z0-9]+\.*%?$")  # Regular expression to identify correctly formatted codes.
    currentConditionCodes = {"Negative": set([]), "Positive": set([])}
    with open(fileDefinitions, 'r') as fidDefinitions, open(fileAnnotateDefinitions, 'w') as fidAnnotateDefinitions:
        for lineNum, line in enumerate(fidDefinitions):
            line = line.strip()
            if not line:
                # The line is empty.
                pass
            elif line[0] == '#':
                # The line contains the name of a new case definition.
                if currentConditionCodes:
                    # Write out the codes that make up the previous case definition.
                    caseDefCodes = currentConditionCodes["Positive"] - currentConditionCodes["Negative"]
                    for i in sorted(caseDefCodes):
                        description = mapCodeToDescription.get(i, "Code not recognised")
                        if description == "Code not recognised":
                            LOGGER.warning("Code {:s} was not found in the dictionary.".format(i))
                        fidAnnotateDefinitions.write("{:.<5}\t{:s}\n".format(i, description))
                currentConditionCodes = {"Negative": set([]), "Positive": set([])}

                # Write out the name of the next case definition.
                line = re.sub("\s+", ' ', line)  # Turn consecutive whitespace into a single space.
                fidAnnotateDefinitions.write("{:s}\n".format(line))

            elif line[0] == '>':
                # The line contains case definition mode, output or restriction information.
                line = re.sub("\s+", ' ', line)  # Turn consecutive whitespace into a single space.
                line = (line[1:].strip()).lower()  # Make everything lowercase.
                chunks = line.split()

                # Check the correctness of the control line.
                if len(chunks) == 0:
                    # The control line needs more information on it.
                    LOGGER.warning("Line {:d} contains no control information.".format(lineNum + 1))
                elif chunks[0] == "mode":
                    modeChoices = [i for i in chunks[1:]]
                    invalidModeChoices = [i for i in modeChoices if i not in validChoices["Modes"]]
                    if invalidModeChoices:
                        # Some modes on this line are not valid mode choices.
                        LOGGER.warning("Line {:d} contains invalid modes [{:s}] that will be ignored."
                                       .format(lineNum + 1, ','.join([i for i in invalidModeChoices])))
                        if len(invalidModeChoices) < len(modeChoices):
                            # There are valid modes on this line.
                            fidAnnotateDefinitions.write(">mode {:s}\n".format(
                                ' '.join([i for i in modeChoices if i not in invalidModeChoices])
                            ))
                    else:
                        # All modes on the line are valid.
                        fidAnnotateDefinitions.write(">{:s}\n".format(line))
                elif chunks[0] == "out":
                    outChoices = [i for i in chunks[1:]]
                    invalidOutChoices = [i for i in outChoices if i not in validChoices["Outputs"]]
                    if invalidOutChoices:
                        # Some output methods on this line are not valid output choices.
                        LOGGER.warning("Line {:d} contains invalid output methods [{:s}] that will be ignored."
                                       .format(lineNum + 1, ','.join([i for i in invalidModeChoices])))
                        if len(invalidOutChoices) < len(outChoices):
                            # There are valid output methods on this line.
                            fidAnnotateDefinitions.write(">out {:s}\n".format(
                                ' '.join([i for i in outChoices if i not in invalidOutChoices])
                            ))
                    else:
                        # All output methods on the line are valid.
                        fidAnnotateDefinitions.write(">{:s}\n".format(line))
                elif chunks[0] == "from":
                    # The control line may contain a date restriction, so check its format.
                    if len(chunks) == 2:
                        # There are two arguments on the line, and therefore the second should be a date in YYYY-MM-DD
                        # format.
                        try:
                            # Attempt to parse the second argument as a date.
                            datetime.datetime.strptime(chunks[1], "%Y-%m-%d")
                            # The line is formatted correctly, and so can be written out.
                            fidAnnotateDefinitions.write(">{:s}\n".format(line))
                        except ValueError:
                            # The line is incorrectly formatted as the second argument failed to be parsed as a date.
                            LOGGER.warning("Line {:d} is a two argument date restriction, but the second "
                                           "argument is {:s} when it should be a YYYY-MM-DD formatted date."
                                           .format(lineNum + 1, chunks[1]))
                    elif len(chunks) == 4:
                        # There are four arguments on the line, and therefore the second should be a date in YYYY-MM-DD
                        # format, the third 'to' and the fourth a date in YYYY-MM-DD format.
                        if chunks[2] != "to":
                            # With four arguments the format must be "from date to date".
                            LOGGER.warning("Line {:d} has 4 arguments, but the third argument is not 'to'"
                                           .format(lineNum + 1))
                        else:
                            try:
                                # Attempt to parse the second and fourth arguments as dates.
                                startDate = datetime.datetime.strptime(chunks[1], "%Y-%m-%d")
                                endDate = datetime.datetime.strptime(chunks[3], "%Y-%m-%d")
                                if endDate < startDate:
                                    # The end date of the date restriction is before the start date.
                                    LOGGER.warning("Line {:d} date restriction has an end date '{:s}' before its "
                                                   "start date '{:s}'.".format(lineNum + 1, chunks[1], chunks[3]))
                                else:
                                    # The line is formatted correctly and has valid dates.
                                    fidAnnotateDefinitions.write(">{:s}\n".format(line))
                            except ValueError:
                                # The line is incorrectly formatted as the second or fourth argument failed to be
                                # parsed as a date.
                                LOGGER.warning("Line {:d} is a four argument date restriction. The second and "
                                               "fourth arguments should be YYYY-MM-DD formatted dates, but were {:s} "
                                               "and {:s} respectively.".format(lineNum + 1, chunks[1], chunks[3]))
                    else:
                        # There is an incorrect number of arguments on the line.
                        LOGGER.warning("Line {:d} contains {:d} arguments but date restrictions need 2 or 4."
                                       .format(lineNum + 1, len(chunks)))
                elif chunks[0].isdigit():
                    # The control line may contain a value restriction, so check its format.
                    if len(chunks) in [3, 5]:
                        # The line has the correct number of arguments.
                        formatError = False
                        if chunks[1] not in validChoices["Operators"]:
                            # The second argument for a value restriction beginning with a number must be a valid
                            # operator.
                            LOGGER.warning("Line {:d} is a value restriction beginning with a number, but the second "
                                           "argument is not a valid operator.".format(lineNum + 1))
                            formatError = True
                        if chunks[2] not in ["val1", "val2"]:
                            # The third argument for a value restriction beginning with a number must be the name
                            # of the value to restrict on.
                            LOGGER.warning("Line {:d} is a value restriction beginning with a number, but the second "
                                           "argument is not a valid operator.".format(lineNum + 1))
                            formatError = True
                        if len(chunks) == 5:
                            # There are five arguments on the line, so the format should be # OP val1/val2 OP #.
                            if chunks[3] not in validChoices["Operators"]:
                                # The fourth argument of a five argument value restriction must be a valid operator.
                                LOGGER.warning("Line {:d} is a five argument value restriction beginning with a "
                                               "number, but the fourth argument is not a valid operator."
                                               .format(lineNum + 1))
                                formatError = True
                            if not chunks[4].isdigit():
                                # The fifth argument of a five argument value restriction must be a number.
                                LOGGER.warning("Line {:d} is a five argument value restriction beginning with a "
                                               "number, but the fifth argument is not a number."
                                               .format(lineNum + 1))
                                formatError = True
                        if not formatError:
                            # The line is correctly formatted, so write it out. The first set of three arguments
                            # represents a restriction of the form # OP val1|val2, but needs to be reversed to
                            # val1|val2 OP # to be kept consistent with the other value restrictions. If this is not
                            # done, then Val < 3 and 3 < Val1 have to be interpreted differently despite both
                            # using the < operator.
                            chunks[2] = chunks[2].capitalize()  # Convert val1/val2 to Val1/Val2.
                            chunks[1] = chunks[1].translate({ord('>'): '<', ord('<'): '>'})  # Reverse operator.
                            fidAnnotateDefinitions.write(">{:s}\n".format(' '.join(chunks[2::-1])))
                            if len(chunks) == 5:
                                # If the restriction is a five argument restriction, then write out the second three
                                # argument restriction.
                                fidAnnotateDefinitions.write(">{:s}\n".format(' '.join(chunks[2:])))
                    else:
                        # There is an incorrect number of arguments on the line.
                        LOGGER.warning("Line {:d} contains {:d} values but value restrictions starting with a "
                                       "number should have 3 or 5.".format(lineNum + 1, len(chunks)))
                elif chunks[0] in ["val1", "val2"]:
                    # The control line may contain a value restriction, so check its format.
                    if len(chunks) == 3:
                        # The line must be formatted as val1|val2 OP #.
                        formatError = False
                        if chunks[1] not in validChoices["Operators"]:
                            # The second argument for a value restriction beginning with val1 or val2 must be a valid
                            # operator.
                            LOGGER.warning("Line {:d} is a value restriction beginning with {:s}, but the second "
                                           "argument is not a valid operator.".format(lineNum + 1, chunks[0]))
                            formatError = True
                        if not chunks[2].isdigit():
                            # The third argument of a value restriction beginning with val1 or val2 must be a number.
                            LOGGER.warning("Line {:d} is a value restriction beginning with {:s}, but the fifth "
                                           "argument is not a number.".format(lineNum + 1, chunks[0]))
                        if not formatError:
                            # The line is correctly formatted, so write it out.
                            line = line.capitalize()  # Convert val1/val2 to Val1/Val2.
                            fidAnnotateDefinitions.write(">{:s}\n".format(line))
                    else:
                        # There is an incorrect number of arguments on the line.
                        LOGGER.warning("Line {:d} contains {:d} values but value restrictions starting with v1 "
                                       "or v2 should have 3.".format(lineNum + 1, len(chunks)))
                else:
                    # The control line starts with an incorrect value.
                    LOGGER.warning("The first argument on line {:d} was '{:s}', but should have been a number or one "
                                   "of mode, out, from, v1 or v2.".format(lineNum + 1, chunks[0]))
            elif codeMatcher.match(line):
                # The line contains a code for a condition
                code = line.replace('.', '')

                # Determine if the code is a negated code.
                codeType = "Positive"
                if code[0] == '-':
                    # Found a negated code
                    codeType = "Negative"
                    code = code[1:]

                # Determine if the code needs expanding to include child codes.
                if code[-1] == '%':
                    # Found a code that needs expanding to include child codes.
                    code = code[:-1]
                    codeList = [i for i in mapCodeToDescription if i[:len(code)] == code]
                else:
                    # Found a code that does not need expanding to include child codes.
                    codeList = [code]

                # Add the codes to the list of codes for this condition.
                for i in codeList:
                    currentConditionCodes[codeType].add(i)
            else:
                # The line does not appear to contain valid information, so log this and skip it.
                LOGGER.warning("Line {:d} contains a non-blank line that could not be processed.".format(lineNum + 1))

        # Write out the codes that make up the final case definition.
        caseDefCodes = currentConditionCodes["Positive"] - currentConditionCodes["Negative"]
        for i in sorted(caseDefCodes):
            description = mapCodeToDescription.get(i, "Code not recognised")
            if description == "Code not recognised":
                LOGGER.warning("Code {:s} was not found in the dictionary.".format(i))
            fidAnnotateDefinitions.write("{:.<5}\t{:s}\n".format(i, description))
