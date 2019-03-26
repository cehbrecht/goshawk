#!/usr/bin/env python

"""
getStations.py
==============

Takes a county or list of counties and returns a list of station IDs
(src_id).

Usage
=====

    getStations.py [-c <county1>[,<county2>...]] [-x <lon1>,<lon2> -y <lat1>,<lat2>]
                   [-n] [-f <filename>] [-s <YYYYMMDDhhmm>] [-e <YYYYMMDDhhmm>]
                   [-d <datatype>] <output_filename>

Where:
======

    -c      is used followed by a list of counties to match.
    -x      is the lower and upper longitudes of the bounding box
    -y      is the lower and upper latitudes of the bounding box
    -n      means don't display any output
    -f      is used to provide a file with a list of counties, one per line
    -s      is the start date-time that you are interested in
    -e      is the end date-time that you are interested in
    -d      is a comma-separated list of data types you want to match (currently 
            believed to be CLBD CLBN CLBR CLBW DCNN FIXD ICAO LPMS RAIN SHIP WIND WMO).
    <output_filename>   is used if you want to write the output to a file.


Examples:
=========

    python getStations.py -c cornwall,devon,wiltshire 
    python getStations.py  -x 0,3 -y 52,54
    python getStations.py  -x 0,3 -y 52,54 -n
    python getStations.py  -x 0,0.4 -y 52,52.2
    python getStations.py  -x 0.2,0.4 -y 52,52.2 -s 200301010000
    python getStations.py  -x 0.3,0.4 -y 52,52.2 -s 200301010000 -d rain
    python getStations.py  -x 0.3,0.4 -y 52.05,52.1 -s 199901010000 -e 200501010000 -d rain
    python getStations.py  -c DEVON -s 199901010000 -e 200501010000 -d rain
    python getStations.py  -c DEVON  -e 200501010000 -d rain

"""

# Import required modules
import os
import re
import sys
import glob
import getopt

import bbox_utils

# Set up global variables
base_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

def expand(i): return os.path.join(base_dir, i)

metadatadir = expand("metadata")
sourceFile = os.path.join(metadatadir, "SRCE.DATA.COMMAS_REMOVED")
sourceColsFile = os.path.join(metadatadir, "SOURCE.txt")
sourceCapabilitiesFile = os.path.join(metadatadir, "SRCC.DATA")
sourceCapsColsFile = os.path.join(metadatadir, "table_structures", "SCTB.txt")

geogAreaFile = os.path.join(metadatadir, "GEAR.DATA")
geogAreaColsFile = os.path.join(metadatadir, "GEOGRAPHIC_AREA.txt")

_datePattern = re.compile(r"(\d{4})-(\d{2})-(\d{2})\s*(\d{2})?:?(\d{2})?")


def exitNicely(msg):
    print __doc__
    print "ERROR:", msg
    sys.exit()


def dateMatch(line, pattern):
    """
    If line matches pattern then return the date as a long, else None.
    """
    match = pattern.match(line)
    if match:
        d = "".join([m for m in match.groups() if m])
        while len(d) < 12:
            d = d + "00"

        dt = long(d)
        return dt
    return


class StationIDGetter:
    """
    Class to generate lists of station names from arguments.
    """

    def __init__(self, counties, bbox, dataTypes, startTime, endTime, outputFile=None, noprint=None):
        """
        Sets up instance variables and calls relevant methods.
        """
        self.dataTypes = [dtype.lower() for dtype in dataTypes]

        # fix times to ensure correct formats (longs)
        if type(startTime) == type("str"):
            startTime = startTime.replace("T", " ")
            startTime = dateMatch(startTime, _datePattern)

        if type(endTime) == type("str"):
            endTime = endTime.replace("T", " ")
            endTime = dateMatch(endTime, _datePattern)

        self.startTime = startTime
        self.endTime = endTime

        # Read in tables
        self._buildTables()

        # Do spatial search to get a load of SRC_IDs
        if counties == []:
            stList = self._getByBBox(bbox)
        else:
            counties = [county.upper() for county in counties]
            stList = self._getByCounties(counties)

        # Now do extra filtering
        self.stList = self._filterBySourceCapability(stList)

        print "Number of stations found: %s\n" % len(self.stList)

        if noprint == None:
            print "SRC IDs follow:\n=================="
        if outputFile == None:
            if noprint == None:
                for row in self.stList:
                    print row
        else:
            output = open(outputFile, "w")

            for row in self.stList:
                output.write(row + "\r\n")

            output.close()

            print "Output written to '%s'" % outputFile

    def getStationList(self):
        """
        Returns the list.
        """
        return self.stList

    def _getByBBox(self, bbox):
        """
        Returns all stations within a bounding box described as
        [N, W, S, E].
        """
        (n, w, s, e) = bbox
        print "Searching within a box of (N - S) %s - %s and (W - E) %s - %s..." % (
            n, s, w, e)
        n = float(n)
        w = float(w)
        s = float(s)
        e = float(e)

        # Reverse north and south if necessary
        if n < s:
            ntemp = n
            n = s
            s = ntemp

        source = self.tables["SOURCE"]
        sourceCols = source["columns"]
        latCol = self._getColumnIndex(sourceCols, "HIGH_PRCN_LAT")
        lonCol = self._getColumnIndex(sourceCols, "HIGH_PRCN_LON")
        srcIDCol = self._getColumnIndex(sourceCols, "SRC_ID")

        matchingStations = []
        for station in source["rows"]:
            stationList = [item.strip() for item in station.split(",")]

            try:
                lat = float(stationList[latCol])
                lon = float(stationList[lonCol])
            except:
                try:
                    lat = float(stationList[latCol]+1)
                    lon = float(stationList[lonCol]+1)
                except:
                    print station

            src_id = stationList[srcIDCol]
            if bbox_utils.isInBBox(lat, lon, n, w, s, e):
                matchingStations.append(src_id)

        return matchingStations

    def _filter(self, rows, term):
        """
        Returns a reduced list of rows that match the term given.
        """
        newRows = []

        for row in rows:
            if row.find(term) > -1:
                newRows.append(row)

        return newRows

    def _getByCounties(self, counties):
        """
        Returns all stations within the borders of the counties listed.
        """
        print "\nCOUNTIES to filter on:", counties

        source = self.tables["SOURCE"]
        sourceCols = source["columns"]
        geog = self.tables["GEOG"]
        geogCols = geog["columns"]

        areaTypeCol = self._getColumnIndex(geogCols, "GEOG_AREA_TYPE")
        areaIDCol = self._getColumnIndex(geogCols, "WTHN_GEOG_AREA_ID")
        areaNameCol = self._getColumnIndex(geogCols, "GEOG_AREA_NAME")

        sourceAreaIDCol = self._getColumnIndex(sourceCols, "LOC_GEOG_AREA_ID")
        srcIDCol = self._getColumnIndex(sourceCols, "SRC_ID")

        countyCodes = []
        countyMatches = []

        for area in geog["rows"]:

            areaList = [a.strip() for a in area.split(",")]
            areaID = areaList[areaIDCol]

            areaType = areaList[areaTypeCol]
            areaName = areaList[areaNameCol]

            if areaType.upper() == "COUNTY" and areaName in counties:

                countyCodes.append(areaID)
#                countyMatches.append(re.compile(r"\s*([^,]+),\s*([^,]+,\s*){%s}(%s,)" % ((sourceAreaIDCol-1), areaID)))
#                print r"([^,]+), ([^,]+, ){%s}(%s,)" % ((sourceAreaIDCol-1), areaID)

        matchingStations = []

        for station in source["rows"]:

            items = [item.strip() for item in station.split(",")]
            if items[sourceAreaIDCol] in countyCodes:
                matchingStations.append(items[0])

            # for cm in countyMatches:
            #    match = cm.match(station)

            #    if match:
            #        src_id = match.group(1)
            #        matchingStations.append(src_id)

        return matchingStations

    def _filterBySourceCapability(self, stList):
        """
        Does data type and time range filtering if requested.
        """
        if self.dataTypes == [] and (self.startTime == None and self.endTime == None):
            return stList

        if self.dataTypes != []:
            print "Filtering on data types: %s" % self.dataTypes
        if self.startTime:
            print "From: %s" % self.startTime
        if self.endTime:
            print "To: %s" % self.endTime

        newList = []

        srcc = self.tables["SRCC"]
        srccRows = srcc["rows"]
        srccCols = srcc["columns"]

        idTypeCol = self._getColumnIndex(srccCols, "ID_TYPE")
        srcIDCol = self._getColumnIndex(srccCols, "SRC_ID")

        startCol = self._getColumnIndex(srccCols, "SRC_CAP_BGN_DATE")
        endCol = self._getColumnIndex(srccCols, "SRC_CAP_END_DATE")

        for row in srccRows:

            items = [item.strip() for item in row.split(",")]
            srcID = items[srcIDCol]

            if srcID in stList:

                # Check if this data type includes this source id
                dataTypeAllowed = False

                if self.dataTypes != []:
                    dataType = items[idTypeCol]

                    if dataType.lower() in self.dataTypes:
                        dataTypeAllowed = True

                else:
                    dataTypeAllowed = True

                # Check if this time window is available for this source id
                timeAllowed = True

                if self.startTime:
                    endOfMeasuring = dateMatch(items[endCol], _datePattern)
                    #print endOfMeasuring, self.startTime

                    if self.startTime > endOfMeasuring:
                        timeAllowed = False

                if self.endTime:
                    startOfMeasuring = dateMatch(items[startCol], _datePattern)
                    #print startOfMeasuring, self.endTime

                    if self.endTime < startOfMeasuring:
                        timeAllowed = False

                if dataTypeAllowed and timeAllowed:
                    if srcID not in newList:
                        newList.append(srcID)

        print "Original list length:", len(stList)
        print "Selected after SRCC filtering:", len(newList)
        return newList

    def _lineMatch(self, line, pattern):
        """
        If line matches pattern then return the date as a long, else None.
        """
        match = pattern.match(line)

        if match:
            dateLong = long("".join(match.groups()[1:]))
            return dateLong

        return

    def _getColumnIndex(self, alist, item):
        """
        Returns the index of item in alist.
        """
        return alist.index(item)

    def _buildTables(self):
        """
        Builds some dictionaries to house the tables in the form:
        self.tables["SOURCE"] = {"columns"=["src_id", ...]
                               "rows"=["23942309423.,234,2342","234...]}
        """
        self.tables = {}

        self.tables["SOURCE"] = {"columns": [i.strip() for i in open(sourceColsFile).readlines()],
                                 "rows": [i.strip() for i in self._cleanRows(open(sourceFile).readlines())]}
        self.tables["GEOG"] = {"columns": [i.strip() for i in open(geogAreaColsFile).readlines()],
                               "rows": [i.strip() for i in self._cleanRows(open(geogAreaFile).readlines())]}
        self.tables["SRCC"] = {"columns": [i.strip() for i in open(sourceCapsColsFile).readlines()],
                               "rows": [i.strip() for i in self._cleanRows(open(sourceCapabilitiesFile).readlines())]}

    def _cleanRows(self, rows):
        """
        Returns rows that should have removed any odd SQL headers or footers.
        """
        newRows = []

        for row in rows:
            if row.find("[") > -1 or row.find("SQL") > -1 or row.find("Oracle") > -1:
                continue

            if row.find(",") > -1:
                newRows.append(row)

        return newRows


if __name__ == "__main__":

    argList = sys.argv[1:]

    if len(sys.argv) == 1:
        exitNicely("")

    (args, outputFileList) = getopt.getopt(argList, "c:f:x:y:d:s:e:n")
    counties = []
    noprint = None
    dataTypes = []
    startTime = None
    endTime = None

    if outputFileList == []:
        outputFile = None
    else:
        outputFile = outputFileList[0]

    bbox = [None, None, None, None]

    for arg, value in args:
        if arg == "-c":
            counties = value.split(",")
        elif arg == "-x":
            bbox[1], bbox[3] = value.split(",")
        elif arg == "-y":
            bbox[0], bbox[2] = value.split(",")
        elif arg == "-f":
            counties = [line.strip() for line in open(value).readlines()]
        elif arg == "-d":
            dataTypes = value.split(",")
        elif arg == "-s":
            startTime = long(value)
        elif arg == "-e":
            endTime = long(value)
        elif arg == "-n":
            noprint = 1

    if counties == [] and None in bbox:
        exitNicely(
            "You must provide a miminum of either a list of counties or a x and y box coordinates.")

    StationIDGetter(counties, bbox, dataTypes, startTime,
                    endTime, outputFile, noprint)
