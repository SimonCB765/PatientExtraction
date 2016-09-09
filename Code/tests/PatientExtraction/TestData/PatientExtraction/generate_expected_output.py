"""Script to generate the expected output (minus the header) for the full patient extraction."""

# Python imports.
import json
import numpy

# User imports.
from Code.PatientExtraction import record_selector as rs

# The location of the dataset of patients being used and the location to generate the output.
fileData = "C:\\Users\\sb0080.UWS30079\\Documents\\PatientExtraction\\Code\\tests\\PatientExtraction\\TestData" \
           "\\PatientExtraction\\FlatPatientData.tsv"
fileOut = "C:\\Users\\sb0080.UWS30079\\Documents\\PatientExtraction\\ExpectedTestOutput.tsv"

# The codes to restrict the extraction to.
codes = ["229", "2469", "40729", "44I5", "NYSU5221"]

# Perform the extraction.
with open(fileData, 'r') as fid, open(fileOut, 'w') as fidOut:
    for line in fid:
        line = line.strip()
        chunks = line.split('\t')
        patientID = chunks[0]
        history = json.loads(chunks[1])
        history = {i: history[i] for i in history if i in codes}  # Restrict the patient history to the chosen codes.

        # Select the val1 and val2 values for the mode 'all' outputs.
        v1 = []
        v2 = []
        for i in history:
            for j in history[i]:
                v1.append(j["Val1"])
                v2.append(j["Val2"])

        # Extract output values for mode all.
        count = "{:d}".format(len(v1)) if v1 else ''
        maxV1 = "{:.2f}".format(max(v1)) if v1 else ''
        maxV2 = "{:.2f}".format(max(v2)) if v2 else ''
        meanV1 = "{:.2f}".format(numpy.mean(v1)) if v1 else ''
        meanV2 = "{:.2f}".format(numpy.mean(v2)) if v2 else ''
        medianV1 = "{:.2f}".format(numpy.percentile(v1, 50)) if v1 else ''
        medianV2 = "{:.2f}".format(numpy.percentile(v2, 50)) if v2 else ''
        minV1 = "{:.2f}".format(min(v1)) if v1 else ''
        minV2 = "{:.2f}".format(min(v2)) if v2 else ''

        # If their is any history left after restricting to the chosen codes (may not be as some patients won't have
        # any of the code), then perform additional extraction on this.
        if history:
            # Extract output values for the date modes (earliest and latest).
            earliest = rs.earliest_selector(history)
            for i, j in earliest.items():
                earliestCode = i
                earliestDate = j[0]["Date"]
                earliestVal1 = "{:.2f}".format(j[0]["Val1"])
                earliestVal2 = "{:.2f}".format(j[0]["Val2"])
            latest = rs.latest_selector(history)
            for i, j in latest.items():
                latestCode = i
                latestDate = j[0]["Date"]
                latestVal1 = "{:.2f}".format(j[0]["Val1"])
                latestVal2 = "{:.2f}".format(j[0]["Val2"])

            # Extract output values for the maximum modes (max1 and max2)
            max1Record = rs.max_selector("Val1")(history)
            for i, j in max1Record.items():
                max1Code = i
                max1Date = j[0]["Date"]
                max1Val1 = "{:.2f}".format(j[0]["Val1"])
                max1Val2 = "{:.2f}".format(j[0]["Val2"])
            max2Record = rs.max_selector("Val2")(history)
            for i, j in max2Record.items():
                max2Code = i
                max2Date = j[0]["Date"]
                max2Val1 = "{:.2f}".format(j[0]["Val1"])
                max2Val2 = "{:.2f}".format(j[0]["Val2"])

            # Extract output values for the minimum modes (min1 and min2).
            min1Record = rs.min_selector("Val1")(history)
            for i, j in min1Record.items():
                min1Code = i
                min1Date = j[0]["Date"]
                min1Val1 = "{:.2f}".format(j[0]["Val1"])
                min1Val2 = "{:.2f}".format(j[0]["Val2"])
            min2Record = rs.min_selector("Val2")(history)
            for i, j in min2Record.items():
                min2Code = i
                min2Date = j[0]["Date"]
                min2Val1 = "{:.2f}".format(j[0]["Val1"])
                min2Val2 = "{:.2f}".format(j[0]["Val2"])
        else:
            # If the patient has none of the chosen codes, then give them a default blank output.
            earliestCode, earliestDate, earliestVal1, earliestVal2 = ['', '', '', '']
            latestCode, latestDate, latestVal1, latestVal2 = ['', '', '', '']
            min1Code, min1Date, min1Val1, min1Val2 = ['', '', '', '']
            max1Code, max1Date, max1Val1, max1Val2 = ['', '', '', '']
            min2Code, min2Date, min2Val1, min2Val2 = ['', '', '', '']
            max2Code, max2Date, max2Val1, max2Val2 = ['', '', '', '']

        # Write the output for this patient.
        fidOut.write(
            "{}\t\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}"
            "\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                chunks[0], count, maxV1, maxV2, meanV1, meanV2, medianV1, medianV2, minV1, minV2,
                earliestCode, earliestDate, earliestVal1, earliestVal2,
                latestCode, latestDate, latestVal1, latestVal2,
                max1Code, max1Date, max1Val1, max1Val2,
                max2Code, max2Date, max2Val1, max2Val2,
                min1Code, min1Date, min1Val1, min1Val2,
                min2Code, min2Date, min2Val1, min2Val2
            )
        )
