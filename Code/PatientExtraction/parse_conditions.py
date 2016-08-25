"""Extract the codes, modes, outputs and restrictions that make up case definitions."""


def main(fileCaseDefs, validChoices):
    """Extract the codes, modes, outputs and restrictions that make up case definitions.

    :param fileCaseDefs:            The location of the input file containing the case definitions.
    :type fileCaseDefs:             str
    :param validChoices:            The valid mode and output flags that can appear in the case definition file.
    :type validChoices:             dict
    :return:                        1) A mapping from case definitions to the positive indicator codes, negative
                                        indicator codes, modes, outputs and restrictions that make up the case
                                        definition. Each case definition is indexed by its name and has as its
                                        associated value a mapping containing keys:
                                        "Positive" - The positive indicator codes.
                                        "Negative" - The negative indicator codes.
                                        "Modes"
                                        "Outputs"
                                        "Restrictions"
                                    2) The conditions that the user has requested patient data for in the order that
                                        they appear in the input file.
    :rtype:                         dict, list

    """

    pass
