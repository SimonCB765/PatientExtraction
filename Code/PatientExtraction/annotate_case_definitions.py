"""Annotate a file of case definitions by expanding all defining codes."""

# Python imports.
import logging
import re

# Globals.
LOGGER = logging.getLogger(__name__)


def main(fileDefinitions, fileCodeDescriptions, fileAnnotateDefinitions):
    """Annotate a file of case definitions by expanding all defining codes.

    :param fileDefinitions:         The location of the file containing the case definitions.
    :type fileDefinitions:          str
    :param fileCodeDescriptions:    The location of the file containing the mapping of codes to their descriptions.
    :type fileCodeDescriptions:     str
    :param fileAnnotateDefinitions: The location of the file to write the annotated input file to.
    :type fileAnnotateDefinitions:  str

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
                    for i, j in currentConditionCodes.items():
                        for k in sorted(j):
                            description = mapCodeToDescription.get(k, "Code not recognised")
                            if description == "Code not recognised":
                                LOGGER.warning("Code {0:s} was not found in the dictionary.\n".format(k))
                            fidAnnotateDefinitions.write("{0:s}{1:.<5}\t{2:s}\n".format(
                                '-' if i == "Negative" else '', k, description))
                currentConditionCodes = {"Negative": set([]), "Positive": set([])}

                # Write out the name of the next case definition.
                line = re.sub("\s+", ' ', line)  # Turn consecutive whitespace into a single space.
                fidAnnotateDefinitions.write("{:s}\n".format(line))
            elif line[0] == '>':
                # The line contains case definition mode, output or restriction information.
                line = re.sub("\s+", ' ', line)  # Turn consecutive whitespace into a single space.
                line = (line[1:].strip()).lower()  # Make everything lowercase.
                fidAnnotateDefinitions.write(">{:s}\n".format(line))
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
        for i, j in currentConditionCodes.items():
            for k in sorted(j):
                description = mapCodeToDescription.get(k, "Code not recognised")
                if description == "Code not recognised":
                    LOGGER.warning("Code {0:s} was not found in the dictionary.\n".format(k))
                fidAnnotateDefinitions.write("{0:s}{1:.<5}\t{2:s}\n".format(
                    '-' if i == "Negative" else '', k, description))
