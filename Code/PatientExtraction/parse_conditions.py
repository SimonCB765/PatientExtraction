"""Extract the codes, modes, outputs and restrictions that make up case definitions."""

# Python imports.
from collections import defaultdict
import datetime
import logging
import re

# User imports.
from . import restriction_comparator_generators

# Globals.
LOGGER = logging.getLogger(__name__)


def main(fileCaseDefs, validChoices):
    """Extract the codes, modes, outputs and restrictions that make up case definitions.

    A case definition does not have to appear all together. It can be split over multiple entries, provided all
    entries have the same case definition name. Similarly, modes, outputs and restrictions can be defined on multiple
    lines. For example, the following two are equivalent:
    >mode A B C
    and
    >mode A
    >mode B C

    :param fileCaseDefs:            The location of the input file containing the case definitions. This file is
                                        expected to have been generated by a call to annotate_case_definitions.main, or
                                        to have the same format.
    :type fileCaseDefs:             str
    :param validChoices:            The valid modes, outputs and operators that can appear in the case definition file.
    :type validChoices:             dict
    :return:                        1) A mapping from case definitions to the positive indicator codes, negative
                                        indicator codes, modes, outputs and restrictions that make up the case
                                        definition. Each case definition is indexed by its name and has as its
                                        associated value a mapping containing keys:
                                        "Positive" - A set of the positive indicator codes.
                                        "Negative" - A set of the negative indicator codes.
                                        "Modes" - A set of the modes to use when extracting case information.
                                        "Outputs" - A set of the output methods to use when outputting case information.
                                        "Restrictions" - The restrictions in place on the patients selected. A
                                            restriction is represented by a function that takes a value and returns
                                            whether the patient-code association meets the restriction.
                                    2) The conditions that the user has requested patient data for in the order that
                                        they appear in the input file.
    :rtype:                         dict, list

    """

    # Define the variable needed for parsing.
    caseDefinitions = defaultdict(  # The mapping containing the case definitions in easily accessible format.
        lambda: {"Modes": set(), "Negative": set(), "Outputs": set(), "Positive": set(),
                 "Restrictions": {"Date": [], "v1": [], "v2": []}}
    )
    caseDefsOrder = []  # The case definitions in the order they appear in the user's input file.
    currentCaseDef = ""  # The current case definition being parsed.

    # Perform the parsing.
    with open(fileCaseDefs, 'r') as fidCaseDefs:
        for lineNum, line in enumerate(fidCaseDefs):
            line = line.strip()
            if line[0] == '#':
                # Found the start of a case definition.
                line = line[2:]
                currentCaseDef = re.sub("\s+", '_', line)
                if currentCaseDef not in caseDefinitions:
                    # A case definition with the same name has not already been seen.
                    caseDefsOrder.append(currentCaseDef)
            elif line[0] == '>':
                # Found the start of mode, output or restriction information.
                controlInfo = line[1:]
                chunks = controlInfo.split()
                if chunks[0] == "mode":
                    # Found a line recording modes to use for this case definition.
                    modeChoices = [i for i in chunks[1:]]
                    caseDefinitions[currentCaseDef]["Modes"].update(modeChoices)
                elif chunks[0] == "out":
                    # Found a line recording output methods to use for this case definition.
                    outChoices = [i for i in chunks[1:]]
                    caseDefinitions[currentCaseDef]["Outputs"].update(outChoices)
                elif chunks[0] == "from":
                    # Found a line recording a date range restriction to use for this case definition.
                    startDate = datetime.datetime.strptime(chunks[1], "%Y-%m-%d")
                    if len(chunks) == 2:
                        # The restriction is to have an end date of today's date.
                        endDate = datetime.datetime.now()
                    else:
                        # The restriction has both start and end dates.
                        endDate = datetime.datetime.strptime(chunks[3], "%Y-%m-%d")
                    comparisonFunc = restriction_comparator_generators.date_generator(startDate, endDate)
                    caseDefinitions[currentCaseDef]["Restrictions"]["Date"].append(comparisonFunc)
                elif chunks[0].isdigit():
                    # Found a line recording a value-based restriction starting with a number.
                    comparisonFunc = restriction_comparator_generators.value_generator(
                        float(chunks[0]), validChoices["Operators"][chunks[1]]
                    )
                    caseDefinitions[currentCaseDef]["Restrictions"][chunks[2]].append(comparisonFunc)
                elif chunks[0] in ["v1", "v2"]:
                    # Found a line recording a value-based restriction starting with v1 or v2.
                    comparisonFunc = restriction_comparator_generators.value_generator(
                        float(chunks[2]), validChoices["Operators"][chunks[1]]
                    )
                    caseDefinitions[currentCaseDef]["Restrictions"][chunks[0]].append(comparisonFunc)
                else:
                    # The line was not correctly formatted, and will be ignored.
                    LOGGER.warning("Line {:d} contains an incorrectly formatted control line.".format(lineNum + 1))
            else:
                # Found a code for the current case definition.
                line = line.replace('.', '')
                code = (line.split('\t'))[0]

                # Determine if the code is a negated code.
                isNegativeCode = False
                if code[0] == '-':
                    # Found a negated code
                    isNegativeCode = True
                    code = code[1:]

                # Add the code as an indicator for the case definition.
                caseDefinitions[currentCaseDef]["Negative" if isNegativeCode else "Positive"].add(code)

    # Make sure each case definition has a mode and output method.
    for i in caseDefinitions:
        if not caseDefinitions[i]["Modes"]:
            caseDefinitions[i]["Modes"] = ["all"]
        else:
            caseDefinitions[i]["Modes"] = sorted(caseDefinitions[i]["Modes"])
        if not caseDefinitions[i]["Outputs"]:
            caseDefinitions[i]["Outputs"] = ["count"]
        else:
            caseDefinitions[i]["Outputs"] = sorted(caseDefinitions[i]["Outputs"])

    return caseDefinitions, caseDefsOrder
