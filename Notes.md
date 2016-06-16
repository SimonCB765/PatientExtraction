# INPUT
Format seems to be something like
PatientID||Code_A|Code_A_Flags_1|Code_A_Flags2||Code_B|Code_B_Flags

For example,
26015||136|d=1993-08-26,v=2||1371|d=2003-10-06|d=2003-10-06||22K|d=2004-10-13,v=26.1||2469|d=2006-12-07,v=130,w=70|d=2007-12-28,v=100,w=65|d=2005-10-11,v=100,w=62|d=2004-11-10,v=98,w=54|d=2003-10-06,v=100,w=60|d=2002-07-11,v=90,w=56|d=2001-11-05,v=110,w=60|d=2000-12-06,v=100,w=60||PETA9623BRIDL|d=2010-06-11,t=TWO TO BE TAKEN FOUR TIMES DAILY

For each code, one set of flags is present per date the patient was associated with the code

The only valid code flags appear to be

- d - appears to be the date that the code was assigned
- t - appears to be some sort of free text that goes with the code
- v - appears to be a value that goes with the code
- w - no idea what this is

## PROBLEMS
- Major problem with the format used due to there being = signs in the free text occasionally
    - The free text is also likely to cause other problems
    - Probably need to enclose it in quotes and make sure to escape control characters in it
- I know the file Norman is using has errors in its formatting. There are definitely occasions where two sets of double pipe are right next to each other, e.g. ||||

## TODO
1 Come up with a different and better flat file one record per patient format for the input
2 Convert the entire QICKD database into this new flat file format
3 Possibly generate some randomised/shuffled or completely synthetic subset to include online and for testing