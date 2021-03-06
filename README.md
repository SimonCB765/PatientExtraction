# Introduction

This repository contains code intended to enable the repeated extraction of patient data without needing to query the relational database storing the data. In order to run the data extraction process, the following steps should be followed:

1. Extract the entire set of patient data from the database. The extracted data is expected to be in an [SQL insert style format](#sql-extract-file-syntax).
2. Run the [Generate Data Files](#generate-data-files) package.
3. Specify the data you want extracted following [these](#data-directives-file) guidelines.
4. Run the [Patient Extraction](#patient-extraction) package.

If the output location of the [Generate Data Files](#generate-data-files) package is not altered, then the [Patient Extraction](#patient-extraction) package can be run without specifying the location of any input files (other than the directives file). Otherwise the location where the flat file generated by the [Generate Data Files](#generate-data-files) package is saved will need to be provided to the [Patient Extraction](#patient-extraction) package.

### SQL Extract File Syntax

The patient data extracted from the database is expected to be in an SQL insert style format. An example of the expected format is:

	insert into `table`(`column1`,`column2`,`column3`,...) values (value1,value2,value3,...);\n

In the case of the patient data, an example line from the dump file is:

	insert into `journal`(`id`,`code`,`date`,`value1`,`value2`,`text`) values (26015,'6791','2004-03-10',0.0000,0.0000,null);\n

# Generate Data Files

This package is used to generate the flat file format used by the patient extraction. In order to generate the data file the file containing the patient medical histories needs to be either placed in the default location (a file called journal.sql in the Data directory) or have its location specified using the `-p` flag at runtime. The expected format of this file can be found [here](#sql-extract-file-syntax).

Two commands are suitable for generating the flat file:
1. `python /path/to/Code/GenerateDataFiles <optional-arguments>`
    - Called from any directory.
2. `python -m GenerateDataFiles <optional-arguments>`
    - Called from within the Code directory.

# Patient Extraction

This package is used to extract specific data about given patients. In order to extract patient data four files are needed:

1. The file containing the mapping between clinical codes and their descriptions. The location of this file can be provided with the `-c` flag or by placing it in the default location (a file called Coding.tsv in the Data directory). A suitable mapping file (saved in the default location) is provided with this repository. The file should be a tsv file containing one code per line, with each line having the format:
    - Code\tDescription\n
2. The flat file of medical histories generated using the [Generate Data Files](#generate-data-files) package. This can be provided using the `-d` flag or by placing it in the default location that the [Generate Data Files](#generate-data-files) package creates it (a file called FlatPatientData.tsv in the Data directory).
3. The subset of patients for which data should be extracted. The location of this file can be provided with the `-p` flag or by placing it in the default location (a file called PatientSubset.txt in the Data directory). Only patients with IDs specific in the file will have data about them extracted. The file that comes with the repository is empty, and the default behaviour of the package is therefore to extract data about all patients. The file is expected to contain one patient ID per line, with each line having the format:
	- ID\n
4. The file containing the directions about what data to extract. The format of this file and how it works is described [here](#data-directives-file).

Two commands are suitable for generating the flat file:
1. `python /path/to/Code/PatientExtraction /path/to/data/directives <optional-arguments>`
    - Called from any directory.
2. `python -m PatientExtraction /path/to/data/directives <optional-arguments>`
    - Called from within the Code directory.

## Data Directives File

### Format

The file of data directives is intended to collect together descriptions of the information about each patient that should be collected (e.g. whether the patient has suffered cardiac arrest, mean glucose reading, lowest serum creatinine reading). This is achieved by specifying the clinical codes that a patient must contain in their record in order to be selected as matching the criteria of the directive. In addition to the codes, restrictions (such as a value associated with a code being greater than some threshold) can be suppliedto further reduce the scope over which the directive applies. Each directive is formatted as follows:

	# Unique Directive Identifier
	> MODE {extraction-modes} 
	> OUT {output-methods} 
	> {restriction-1} 
	> {restriction-2} 
	...
	> {restriction-N} 
	code1
	code2
	...
	codeN

Multiple directives can be placed one after another in the same file. Each directive needs a unique identifier composed of any combination of characters. Often a description of what the directive is intended to extract (e.g. Incidence of Heart Failure) is most beneficial. If the same unique directive identifier is used for two or more directives, then the definitions are combined together.

### Codes

Each directive can have any number of codes defined within it. The expected format of a code is:

1. An optional initial negative sign.
2. Any number of alphanumeric characters.
3. Any number of full stops.
4. An optional percent sign (%).

This produces the following regular expression that defines a valid code: `-?[a-zA-Z0-9]*\.*%?`. Examples of valid codes are:

- `C10E`
- `-1sd..`
- `ABC...%`
- `-c10f%`

Full stops are simply stripped from the code and have no semantic value. They're included as it is not uncommon to see a code `XXX` written as `XXX..` in a 5 character system.

The percent sign is used to indicate that all codes with the given prefix are positive for the directive. For example, the code `C10%` will match all codes beginning with `C10`.

A negative sign in front of a code indicates that that code should not be used to identify patients that meet the criteria of the directive. For example, if the code `C%` is included in a directive, then all patients containing a code that starts with a `C` will be selected as meeting the directive's criteria. However, if you add code `-C10%`, then only those patients that have a code beginning with a `C` that does not begin with `C10` will be selected. As an example, of the following patients:

1. Patient 1 with codes `Cxx`, `Cyy` and `Czz`.
2. Patient 2 with codes `Cxx` and `C10yy`.
3. Patient 3 with only the code `C10E1`.

patients 1 and 2 will be selected as meeting the criteria of the directive, while patient 3 would not.

### Extraction Modes

Extraction modes describe the way that patient records should be selected. For example, for a given directive you may be interested in the lowest blood glucose measurement recorded in each patient's record. You would then use the `earliest` extraction mode. Alternatively, you may be interested in averaging all blood glucose measurements. In this case you would use the `all` extraction mode to extract all blood glucose readings recorded. The {extraction-modes} should be one or more of the following separated by whitespace:

- `EARLIEST` - Select the earliest association between each patient and one of the non-negative codes defined in the directive.
- `LAST` - Select the most recent association between each patient and one of the non-negative codes defined in the directive.
- `ALL` - (Default value) Select all associations between each patient and the non-negative codes defined in the directive.
- `MAX1` - Select the association between each patient and one of the non-negative codes with the greatest associated value for the value 1 (v) field.
- `MAX2` - Select the association between each patient and one of the non-negative codes with the greatest associated value for the value 2 (w) field.
- `MIN1` - Select the association between each patient and one of the non-negative codes with the smallest associated value for the value 1 (v) field.
- `MIN2` - Select the association between each patient and one of the non-negative codes with the smallest associated value for the value 2 (w) field.

The extraction mode instructions are not case sensitive. The lines 
`> MODE ALL MAX` 
and 
`> mode all max` 
are equivalent. At least one whitespace character is needed as a separator between the `>` character and the word `mode`, and at least one between each extraction mode, e.g. between `all` and `max` in the example above.

### Output Methods

Output methods describe how the extracted associations between patients and codes should be processed and output. For example, if you want to output the date on which the extracted association occurred you would use the `date` output method. The {output-methods} should be one or more of the following separated by whitespace:

- `CODE` - Output the code from the extracted association. If the `ALL` mode is used to extract multiple associations, then this will output an arbitrary extracted code.
- `COUNT` - (Default value) Output the number of associations extracted.
- `DATE` - Output the date on which the extracted association occurred. If the `ALL` mode is used to extract multiple associations, then this will output the date of an arbitrary extracted association.
- `EXISTS` - Output a 1 if there were any associations extracted, else output a 0.
- `MAX1` - Output the maximum value 1 (v) field value among the extracted associations.
- `MAX2` - Output the maximum value 2 (w) field value among the extracted associations.
- `MEAN1` - Output the mean value 1 (v) field value for the extracted associations.
- `MEAN2` - Output the mean value 2 (w) field value for the extracted associations.
- `MEDIAN1` - Output the median value 1 (v) field value for the extracted associations.
- `MEDIAN2` - Output the median value 2 (w) field value for the extracted associations.
- `MIN1` - Output the minimum value 1 (v) field value among the extracted associations.
- `MIN2` - Output the minimum value 2 (w) field value among the extracted associations.
- `VAL1` - Output the value 1 (v) field value from the extracted association. If the `ALL` mode was used to extract multiple associations, then this will output the value 1 field value of an arbitrary extracted association.
- `VAL2` - Output the value 2 (w) field value from the extracted association. If the `ALL` mode was used to extract multiple associations, then this will output the value 2 field value of an arbitrary extracted association.

The output method instructions are not case sensitive. The lines 
`> OUT CODE MAX` 
and 
`> out code max` 
are equivalent. At least one whitespace character is needed as a separator between the `>` character and the word `out`, and at least one between each output method, e.g. between `code` and `max` in the example above.

### Restrictions

Restrictions are used to limit the patient-code association extracted to a given data or value range. For example, extracted associations can be limited to those that occurred within the last three years, or where an associated value is greater than a given threshold. Multiple restrictions of either type can be provided in one directive. This can be used to provide multiple date or value ranges. In the case of multiple restrictions, and association must satisfy all restrictions before it is extracted. Each {restriction} line should contain one of:

- A date range of the form:
	- `from X`
		- This will extract associations from the date `X` to the present date inclusive.
	- `from X to Y`
		- This will extract associations between the dates `X` and `Y` inclusive.
	- Dates must be in the format YYYY-MM-DD.
    - The second date must be more recent than the first.
- A value range of the form:
	- `x OP value` or `value OP x`
	- `x` is a numeric value.
	- `OP` is the comparison operator to use, and can be one of: `<`, `<=`, `>` or `>=`

The restriction instructions are not case sensitive. The lines 
`> FROM YYYY-MM-DD TO YYYY-MM-DD` 
and 
`> from YYYY-MM-DD to YYYY-MM-DD` 
are equivalent. At least one whitespace character is needed as a separator between the `>` character and the start of the restriction, and between the components of the restriction, e.g. between from and the date and to and the dates in the example above.

### Example Directives File

	# Directive A
	> mode all
	> out count exists mean1 mean2
	> from 2005-01-01
	C10..%
	-C10E%
	
	# Directive B
	> mode earliest latest
	> out val1 val2
	> val1 > 5
	> val1 < 10
	> val2 > 3
	44h5%
	44i2%
	44I9