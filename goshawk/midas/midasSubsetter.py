#!/usr/bin/env python

"""

midasSubsetter.py
=================

Subsets data from the MIDAS flat files. Allows extraction by:

- table
- date range
- column name
- value conditions

The MIDASSubsetter class needs to be able to see the file 'midas_structure.txt' which
is essentially a description of the table contents in a text file. This is parsed each
time this script is called.

There is hard-coded limit of 100,000 lines that can currently be extracted.

Usage:
======

    midasSubsetter.py -t <table> [-s <YYYYMMDDhhmm>] [-e <YYYYMMDDhhmm>]
         [-c <column1>[,<column2>...]] [-n <conditions>] [-d <delimiter>]
         [-i <src_id1>[,<src_id2>...]] [-g <groupfile>] [-r <region>] [-p <tempdir>] <outputFile>


Where:
------

    <table>     - is the name of the MIDAS table
    -s          - provide the start date/time
    -e          - provide the end date/time
    -c          - provide a comma-separated list of required columns
    -n          - provide a list of comma-separated list of conditions in the form:
                    * range=<low>:<high>     [<low> and <high> are values]
                    * greater_than=<value>
                    * less_than=<value>
                    * exact=<match>          [<match> is a string]
                    * pattern=<pattern>      [<pattern> is a regular expression]
    -d          - delimiter is one of ","|"comma"|"tab" or other character/string.
    -i          - provide a comma separated list of station IDs
    -g          - provide the name of a file containing one station id per line.
    -r          - for GLOBAL table only - provide a region (optional - otherwise will do global search).
                  Regions are: 1-Africa, 2-Asia, 3-South America, 4-North Central America,
                               5-South West Pacific, 6-Europe, 7-Antarctic.
    -p           - temporary directory location (absolute path)

Examples:
=========

midasSubsetter.py -t RS -s 200401010000 -e 200401011000

midasSubsetter.py -t RS -s 200401010000 -e 200401011000 outputfile.dat

midasSubsetter.py -t RS -s 200401010000 -e 200401011000 -g testlist.txt outputfile.dat

midasSubsetter.py -t RS -s 200401010000 -e 200401011000 -i 214,926 -d tab

"""

# Import required modules
import sys
import commands
import os
import getopt
import re
import glob
import time


# Set up global variables
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def expand(i): return os.path.join(base_dir, i)

metadatadir = expand("metadata")
datadir = expand("data")

midasStructureTable = os.path.join(metadatadir, "allTablePartitionNames.txt")
temp_dir = expand(".temporary")
outputDir = temp_dir

# partition regex pattern
_partitionPattern = re.compile(r"nonsense-data_[a-zA-Z\-]+_(\d{6})-(\d{6})\.txt")

# Define nameDict globally
nameDict = {'STXX': 'SOIL_TEMP_OB', 'SRCC': 'SRC_CAPABILITY', 'GLXX': 'GBL_WX_OB',
            'SRCE': 'SOURCE', 'TMSL': 'TEMP_MIN_SOIL_OB', 'MRXX': 'MARINE_OB',
            'ROXX': 'RADT_OB_V2', 'TDXX': 'TEMP_DRNL_OB', 'WDXX': 'WEATHER_DRNL_OB',
            'RDXX': 'RAIN_DRNL_OB', 'RSXX': 'RAIN_SUBHRLY_OB', 'RHXX': 'RAIN_HRLY_OB',
            'WMXX': 'WIND_MEAN_OB', 'WHXX': 'WEATHER_HRLY_OB'}

globalWXCodes = {"1": "glblwx-africa", "2": "glblwx-asia",
                 "3": "glblwx-south-america", "4": "glblwx-north-central-america",
                 "5": "glblwx-south-west-pacific", "6": "glblwx-europe",
                 "7": "glblwx-antarctic"}


def countLines(fname):
    "Returns a count of the lines in a files."
    return commands.getoutput("wc -l %s" % fname).strip()


def dateMatch(line, pattern):
    """
    If line matches pattern then return the date as a long, else None.
    """
    match = pattern.match(line)
    if match:
        dateLong = long("".join(match.groups()[1:]))
        return dateLong
    return


def tableMatch(tableName):
    """
    Takes what is given and returns a tuple of (tableID, tableName).
    """
    if len(tableName) < 5:
        shortnames = nameDict.keys()
        if tableName in shortnames:
            longname = nameDict[tableName]
        elif tableName + "XX" in shortnames:
            longname = nameDict[tableName + "XX"]
        else:
            raise Exception("Tablename not known: %s" % tableName)
        shortname = tableName[:2]
    else:
        longnames = nameDict.values()
        if tableName not in longnames:
            raise Exception("Tablename not known: %s" % tableName)
        else:
            for s, l in nameDict.items():
                if l == tableName:
                    shortname = s
                    break
            longname = l

    return (shortname[:2], longname)


def exitNicely(msg=""):
    """
    Takes an error message as the argument and prints help message.
    """
    print __doc__
    print "ERROR:", msg
    sys.exit()


def padTime(timestring):
    """
    Returns a 12 digit string as time by padding any missing month, day, hour
    or minute values.
    """
    padder = "000001010000"
    if len(timestring) < 12:
        timestring = timestring + (padder[len(timestring):])
    return timestring


def getColumnIndex(tableID, colName):
    """
    Returns the index in a row of a given column name.
    """
    inputFile = os.path.join(metadatadir, "table_structures/%sTB.txt" % tableID)
    colNames = [col.strip().lower() for col in open(inputFile).readlines()]

    if colName in colNames:
        return colNames.index(colName)

    raise Exception("Cannot find column name '%s' in table '%s'" %
                    (colName, tableID))


class MIDASSubsetter:
    """
    Subsetting class to manage extractions from large text files holding MIDAS data.
    """

    def __init__(self, tableNames, outputPath, startTime=None, endTime=None, columns="all", conditions=None,
                 src_ids=None, region=None, delimiter="default", tempDir=temp_dir, verbose=1):
        """
        Initialisation of instance sets up the rules and calls various methods.
        """
        self.region = region
        self.verbose = verbose
        self.tempDir = tempDir

        tableNames = [a.upper() for a in tableNames]
        if type(columns) == type([]):
            # convert to list of ints if appropriate
            try:
                columns = [int(i) for i in columns]
            except:
                pass

        # Get full list of all tables and partitions
        tableDict = self._parseTableStructure()

        (tableID, tableName) = tableMatch(tableNames[0])
        if self.verbose:
            print "NOTE: Multiple table search not yet implemented."
        #print tableDict[tableName]

        self.rowHeaders = self._getRowHeaders(tableID)
        if self.verbose:
            print "Got row headers..."
        partitionFiles = tableDict[tableName]["partitionList"]
        if self.verbose:
            print "Got partition files..."

        if self.verbose:
            print "Getting file list..."
        fileList = self._getFileList(
            tableName, startTime, endTime, partitionFiles)

        if columns == "all" and conditions == None:
            if self.verbose:
                print "\nExtracting all rows: %s\nFrom files: %s\nBetween: %s and %s\n" % (tableID, ("\t"+"\n\t".join(fileList)), startTime,
                                                                                           endTime)
            dataFile = self._getCompleteRows(
                tableID, fileList, startTime, endTime, src_ids=src_ids)
        else:
            if self.verbose:
                print "\nExtracting row subsets for: %s\nFrom files: %s\nBetween: %s and %s\n" % (tableID, fileList, startTime,
                                                                                                  endTime)
            dataFile = self._getRowSubsets(
                tableID, fileList, startTime, endTime, columns, conditions)

        if self.verbose:
            print "\nData extracted to temporary file(s)..."

        self._writeOutputFile(dataFile, outputPath, delimiter)

    def _parseTableStructure(self, structureFile=midasStructureTable):
        """
        Parses the table structure text file to return a list of [<files>, <columns>]
        where <files> is a list of [<file_name>, <start_time>, <end_time>].
        """
        tableDict = {}

        fpatt = re.compile(r"nonsense-data_([a-zA-Z\-]+)_(\d{6})-(\d{6}).txt")

        tableList = nameDict.values()

        for tableName in tableList:  

            if tableName in ["SRC_CAPABILITY", "SOURCE", "TEMP_MIN_SOIL_OB", "MARINE_OB"]:
                continue
            tableID = tableMatch(tableName)[0]
            tableDict[tableName] = {"partitionList": []}

            partitionDir = datadir
            os.chdir(partitionDir)
            partitionFiles = glob.glob("*.txt")
            partitionFiles.sort()

            for pfile in partitionFiles:
                pmatch = fpatt.match(pfile)
                if pmatch:
                    # Deal with non-matching regions if global used...
                    if self.region:
                        regionName = globalWXCodes[self.region]
                        if pmatch.groups()[0] != regionName:
                            continue

                    ppath = os.path.join(partitionDir, pfile)
                    tableDict[tableName]["partitionList"].append(ppath)

            os.chdir(base_dir)

        return tableDict

    def _getFileList(self, table, startTime, endTime, partitionFiles, pattern=_partitionPattern):
        """
        Returns a list of files required for reading based on the request.
        """
        startYM = long(startTime[:6])
        endYM = long(endTime[:6])
        filePathList = []
        template = "nonsense-data_%s_%s-%s.txt"

        for file in partitionFiles:
            (nameStart, nameEnd) = pattern.search(file).groups()
            if long(nameEnd) < long(startYM) or long(nameStart) > long(endYM):
                pass
            else:
                filePathList.append(file)
        return filePathList

    def _getCompleteRows(self, tableID, fileList, startTime, endTime, src_ids=None):
        """
        Returns a list of complete rows from the database.
        """
        try:
            timeIndex = getColumnIndex(tableID, "ob_time")
        except:
            try:
                timeIndex = getColumnIndex(tableID, "ob_date")
            except:
                timeIndex = getColumnIndex(tableID, "ob_end_time")

        _datePattern = re.compile(
            r"([^,]+, ){%s}(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})" % timeIndex)

        now = time.strftime("%Y%m%d.%H%M%S", time.localtime(time.time()))
        print self.tempDir
        tempFilePath = os.path.join(self.tempDir, "temp_%s" % (now))
        tempFile = open(tempFilePath, "w")

        startTimeLong = long(padTime(startTime))
        endTimeLong = long(padTime(endTime))

        getAllSrcIds = False
        # Set up srcId pattern finders
        if src_ids:
            selectedRows = []
            print "Now extracting station ids provided..."
            srcidIndex = getColumnIndex(tableID, "src_id")

            # reg ex module has a limit of 9999 items that can be in a "|" separated match option
            # somewhere on web says it can be set at 7500
            # For safety I'll split them into 5000 batches
            n = 0
            srcIdPatternsList = []

            while n <= (len(src_ids) - 1):
                srcIdPatternsList.append(re.compile(
                    r"([^,]+, ){%s}(%s)," % (srcidIndex, "|".join(src_ids[n: (n + 5000)]))))
                n += 5000

        else:
            getAllSrcIds = True

        count = 0
        for filename in fileList:

            lcount = 0
            if self.verbose:
                print "\nFiltering file '%s' containing %s lines." % (
                    filename, countLines(filename))
            file = open(filename)
            line = file.readline()

            while line:
                lcount = lcount+1
                if self.verbose and lcount % 100000 == 0:
                    print "\tRead %s lines..." % lcount

                line = line.strip()
                dmatch = dateMatch(line, _datePattern)

                # Check if datetime has gone past the selected range
                if dmatch and dmatch > endTimeLong:
                    print "Breaking out of read loop because time past end time!"
                    break

                # Now check if src ids need to match
                idmatch = None

                if src_ids:
                    for _srcidPattern in srcIdPatternsList:
                        if _srcidPattern.match(line):
                            idmatch = 1
                            break

                if dmatch and (idmatch or getAllSrcIds):
                    if startTimeLong <= dmatch <= endTimeLong:
                        tempFile.write(line.strip()+"\n")
                        count += 1

                line = file.readline()

            file.close()
        tempFile.close()

        if self.verbose:
            print "Lines to filter = ", countLines(tempFilePath)

        return tempFilePath  # rows

    def _getRowHeaders(self, tableID, columns="all"):
        """
        Reads in the dictionary to get the headers for each column.
        """
        inputFile = os.path.join(
            metadatadir, "table_structures/%sTB.txt" % tableID)
        rowHeaders = [rh.strip().lower() for rh in open(inputFile).readlines()]
        return rowHeaders

    def _getRowSubsets(self, tableID, fileList, startTime, endTime, columns="all", conditions=None):
        """
        Returns a list of rows after sub-setting according to columns and conditions.
        """
        # rows=[]
        now = time.strftime("%Y%m%d.%H%M%S", time.localtime(time.time()))
        tempFilePath = os.path.join(self.tempDir, "temp_%s" % (now))
        tempFile = open(tempFilePath, "w")

        startTimeLong = long(padTime(startTime))
        endTimeLong = long(padTime(endTime))

        count = 0
        for filename in fileList:
            file = open(filename)
            line = file.readline()
            while line:
                line = line.strip()
                match = dateMatch(line)

                if match:
                    dataTimeLong = long(match)
                    if startTimeLong < match < endTimeLong:
                        if type(columns) == type([]):
                            newLine = None
                            splitLine = re.split(",\s+", line)

                            for i in columns:
                                i = i-1
                                if newLine == None:
                                    newLine = "%s, " % splitLine[i]
                                else:
                                    newLine = "%s%s, " % (
                                        newLine, splitLine[i])
                            # rows.append(newLine)
                            tempFile.write(newLine)

                        count = count+1
                line = file.readline()

            file.close()
            tempFile.close()

        return tempFilePath

    def _writeOutputFile(self, tempDataFile, outputPath, delimiter="default"):
        """
        Writes the output file and returns 1 if successful, if delimiter is not "default"
        it modifies each output line accordingly to include chosen delimiter.
        """
        headerLine = ", ".join(self.rowHeaders)+"\n"

        print "Getting size of temporary output file."
        size = os.path.getsize(tempDataFile)
        if size > (200*10**6):
            print "File is bigger than 200MB so I'm not going to try filtering it."

            if outputPath == "display":
                print "This file is too big to display so data has been saved to:"
                now = time.strftime(
                    "%Y%m%d.%H%M%S", time.localtime(time.time()))
                outputPath = os.path.join(outputDir, "out_%s.txt" % now)

            outputFile = open(outputPath, "w")
            outputFile.write(headerLine)
            dataFile = open(tempDataFile)
            line = dataFile.readline()

            while line:
                outputFile.write(line)
                line = dataFile.readline()

            dataFile.close()
            outputFile.close()

            print "\t", outputPath
            os.unlink(tempDataFile)
            return
        else:
            print "Can sort and filter since file is small."

        dataFile = open(tempDataFile)
        rows = dataFile.readlines()
        dataFile.close()
        rows.insert(0, headerLine)

        if delimiter != "default":
            rows = self._reFormatDelimiters(rows, delimiter)

        data = "".join(rows)
        if outputPath == "display":
            print "Output data follows:\n"
            print data+"\n"
        else:
            if len(rows) == 1:
                print "===\nNo data found.\n===\n"
                data = "Your extraction request has run successfully, but no data have been found matching your request.\n\nPlease use the MIDAS station search pages on the CEDA website (http://archive.ceda.ac.uk/midas_stations/) to check your station reporting periods and message types to ensure that your selected stations report message types containing the data elements you require within your selected period.\n\nAdditional information about data outages/known issues/instrument failure can also be found on station records.\n\nIf you have completed these checks and believe the data should be available please contact the CEDA helpdesk for further assistance (support@ceda.ac.uk), providing full details of the extractions you are trying to submit."

            output = open(outputPath, "w")
            output.write(data)
            output.close()
            if len(rows) > 1:
                print "%s records written to: %s\n===\n" % (
                    len(rows), outputPath)

        os.unlink(tempDataFile)
        return 1

    def _reFormatDelimiters(self, rows, delimiter):
        """
        Returns a list of rows with delimiters as requested.
        """
        if delimiter in ("comma", ","):
            return rows
        elif delimiter == "tab":
            delimiter = "\t"

        newRows = [delimiter.join(row.split(", ")) for row in rows]
        return newRows


if __name__ == "__main__":

    argList = sys.argv[1:]
    outputPath = None
    (args, outputPath) = getopt.getopt(argList, "t:s:e:c:n:d:i:r:g:p:")

    startTime = None
    endTime = None
    columns = "all"
    conditions = None
    src_ids = None
    delimiter = "default"
    region = None
    tableNames = []
    tempDir = temp_dir

    if not outputPath:
        outputPath = "display"
    else:
        outputPath = outputPath[0]

    for arg, value in args:
        if arg == "-t":
            tableNames = value.split(",")
        elif arg == "-s":
            startTime = value
        elif arg == "-e":
            endTime = value
        elif arg == "-c":
            columns = value.split(",")
        elif arg == "-d":
            delimiter = value
        elif arg == "-i":
            src_ids = value.split(",")
        elif arg == "-r":
            region = value
        elif arg == "-p":
            tempDir = value
        elif arg == "-g":
            src_ids = [i.strip() for i in open(value).readlines()]
        elif arg == "-n":
            conditions = {}
            conditionList = value.split(",")
            for cond in conditionList:
                a, b = cond.split("=")
                conditions[a] = b

    if tableNames == []:
        exitNicely("Must provide table name with '-t' argument.")

    MIDASSubsetter(tableNames, outputPath, startTime, endTime, columns, conditions,
                   src_ids, region, delimiter, tempDir=tempDir)
