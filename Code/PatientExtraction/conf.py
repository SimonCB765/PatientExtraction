"""Module to contain all globally accessible settings-like variables."""

# Python imports.
import operator

# User imports.
from . import record_outputter
from . import record_selector

# Global variables provided.
isLogging = True
validChoices = {}  # The valid modes, outputs and operators that can appear in a case definition file.


def init():
    """Initialise the settings-like variables."""

    # Initialise the dictionary of valid modes, outputs and operators that can appear in a case definition file.
    validModes = {"all": record_selector.all_selector,
                  "earliest": record_selector.earliest_selector,
                  "latest": record_selector.latest_selector,
                  "max1": record_selector.max_selector("Val1"),
                  "max2": record_selector.max_selector("Val2"),
                  "min1": record_selector.min_selector("Val1"),
                  "min2": record_selector.min_selector("Val2")}  # The valid code selection modes.
    validOutputs = {"code": record_outputter.code_outputter,
                    "count": record_outputter.count_outputter,
                    "date": record_outputter.date_outputter,
                    "exists": record_outputter.exists_outputter,
                    "max1": record_outputter.max_outputter("Val1"),
                    "max2": record_outputter.max_outputter("Val2"),
                    "mean1": record_outputter.mean_outputter("Val1"),
                    "mean2": record_outputter.mean_outputter("Val2"),
                    "median1": record_outputter.median_outputter("Val1"),
                    "median2": record_outputter.median_outputter("Val2"),
                    "min1": record_outputter.min_outputter("Val1"),
                    "min2": record_outputter.min_outputter("Val2"),
                    "val1": record_outputter.value_outputter("Val1"),
                    "val2": record_outputter.value_outputter("Val2")}  # The valid output options.
    validOperators = {'>': operator.gt, ">=": operator.ge,
                      '<': operator.lt, "<=": operator.le}  # The valid value restriction operators.
    global validChoices
    validChoices = {"Modes": validModes, "Operators": validOperators, "Outputs": validOutputs}


def control_logging(isOn=True):
    """Turn the logging on or off.

    :param isOn:    Whether logging should be turned on.
    :type isOn:     bool

    """

    global isLogging
    isLogging = isOn
