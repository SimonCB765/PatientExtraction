# PatientExtraction

## Input File Format

Negative codes are just removed from the positives, they are not used to identify patients that should not exist in the set

if the exact same condition name is used more than once, then the last one takes precedence
    all information from previous occurrences are removed
Codes ending in % are expanded to contain all child codes
Codes can have no full stops (e.g. 101) or full stops (e.g. 101..)
Can't combine full stops and %
Any number of restrictions can be provided, they will be ANDed together
Consecutive whitespace in the name will be converted to a single underscore
Multiple value and date range restrictions can be provided by having more than one line.
At least one whitespace character is needed as a separator between:

- The word MODE and the mode choice
- The word OUT and the output choices
- Each output choice
- To delimit the separate parts of the restrictions (e.g. between from and the first date)

\# Name of the condition
\> MODE {mode}
\> OUT {out}
\> {restriction}
^-?[a-zA-Z0-9]{1,5}(\\.*|%)$

{mode} should be one or more of the following separated by spaces (case insensitive):

- EARLIEST - Select the earliest non-negative indicator code for the condition.
- LAST - Select the most recent non-negative indicator code for the condition.
- ALL - (Default value) Select all non-negative indicator codes for the condition.
- MAX - Select the non-negative indicator code with the greatest associated value (value 1 (v) not value 2 (w)).
- MIN - Select the non-negative indicator code with the smallest associated value (value 1 (v) not value 2 (w)).

{out} should be one or more of the following separated by spaces (case insensitive):

- CODE - Output the selected code (if the ALL mode is used this will output an arbitrary code).
- COUNT - (Default value) Output the number of times the selected code was associated with the patient.
- DATE - Output the date when the selected code was associated with the patient (if the ALL mode is used this will output an arbitrary date).
- MAX - Output the maximum value (value 1 (v) not value 2 (w)) associated with the selected codes.
- MEAN - Output the mean value (value 1 (v) not value 2 (w)) associated with the selected codes.
- MIN - Output the minimum value (value 1 (v) not value 2 (w)) associated with the selected codes.
- VALUE - Output the value (value 1 (v) not value 2 (w)) associated with the selected code (if the ALL mode is used this will output an arbitrary value).

Each {restriction} line should contain one of (case insensitive):

- A date range in the form - from YYYY-MM-DD to YYYY-MM-DD
    - This will select patients between the two dates (inclusively)
    - The second date must be more recent than the first one (or absent to extract all information up to the present)
- A value range meeting the following criteria:
    - The expression is of the form
        - x OP value
        - value OP x OP value
    - x is a numeric value
    - OP can be one of <, <=, > or >=

Examples of valid codes:

- C10E
- -1sd..
- ABC%

## Generate Data Files
Config file needs to contain the following fields:

- SQLDataDirectory - The directory where the SQL dumps are.
- FlatFileDirectory - The directory where the flat file representation of the SQL data should be recorded.

## Patient Extraction
Config file needs to contain the following fields:

- FlatFileDirectory - The location where the flat files generated by the data generation are.
- CodeDescriptionFile - The location where the file containing the description of all codes is.