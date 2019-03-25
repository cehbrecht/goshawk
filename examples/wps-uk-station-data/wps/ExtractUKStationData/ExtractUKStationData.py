"""
extract_uk_station_data.py
===================

Process extract_uk_station_data that holds the ExtractUKStationData class.

"""

import os, stat, time, sys
import logging

from cows_wps.process_handler.fileset import FileSet, FLAG
import cows_wps.process_handler.process_support as process_support
from cows_wps.process_handler.context.process_status import STATUS

import GetWeatherStations.lib as gws_lib
import ExtractUKStationData.lib as exuk_utils
import processes.internal.ProcessBase.ProcessBase


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class ExtractUKStationData(processes.internal.ProcessBase.ProcessBase.ProcessBase):

    # Define arguments that we need to set from inputs
    args_to_set = ["StationIDs", "Counties", "BBox", "DataTypes", "StartDateTime", "EndDateTime",
                   "Delimiter", "OutputTimeChunk", "ObsTableName", "InputJobId"] 

    # Define defaults for arguments that might not be set
    input_arg_defaults = {"StationIDs": [], 
                          "Counties": [],
                          "BBox": None,
                          "DataTypes": [],
                          "InputJobId": None,
                         }

    # Define a dictionary for arguments that need to be processed
    # before they are set (with values as the function doing the processing).
    arg_processers = {"StartDateTime": gws_lib.revertDateTimeToLongString,
                      "EndDateTime": gws_lib.revertDateTimeToLongString}



    def _executeProc(self, context, dry_run):
        """
        This is called to step through the various parts of the process
        executing the actual process if ``dry_run`` is False and just
        returning information on the volume and duration of the outputs
        if ``dry_run`` is True.
        """
        # Call standard _setup
        self._setup(context)
        a = self.args

        if not dry_run:
            # Now set status to started
            context.setStatus(STATUS.STARTED, 'Job is now running', 0)
            # Need to save status for async processes
            context.saveStatus()

        # Resolve the list of stations
        stationList = self._resolveStationList(context, dry_run)

        # Now check limit on number of station IDs
        nStations = len(stationList)
        STATION_LIMIT = 100
        nYears = int(a["EndDateTime"][:4]) - int(a["StartDateTime"][:4])

        if nStations > STATION_LIMIT and a["OutputTimeChunk"] == "decadal":
            a["OutputTimeChunk"] = "year"
            raise Exception("The number of selected station IDs has been calculated to be greater than %d. Please select a chunk size other than 'decadal' for such a large volume of data." % STATION_LIMIT)

        if nYears > 1 and nStations > STATION_LIMIT:
            raise Exception("The number of selected station IDs has been calculated to be greater than %d. Please select a time window no longer than 1 year." % STATION_LIMIT)

        if nStations == 0:
            raise Exception("No weather stations have been found for this request. Please modify your request and try again.")

        # Define data file base
        prefix = "station_data"
        if a["Delimiter"] == "comma":
            ext = "csv"
        else:
            ext = "txt"

        dataFileBase = os.path.join(context.processDir, 'outputs', prefix)

        if not dry_run:
            # Estimate we are 5% of the way through 
            context.setStatus(STATUS.STARTED, 'Extracted station ID list.', 5)
            context.saveStatus()

            # Need temp dir for big file extractions
            procTmpDir = os.path.join(context.processDir, 'tmp')

            # Get Obs Table Names to extract from
            obs_table_names = self._getObsTableNames(a)

            # Get World Region name if available (for global extractions only)
            world_region = self._getWorldRegion(a)

            outputPaths = exuk_utils.extractStationDataByTimeChunk(obs_table_names, a["StartDateTime"], 
                       a["EndDateTime"], stationList, a["OutputTimeChunk"], dataFileBase, a["Delimiter"],
                       ext, procTmpDir, context, world_region = world_region)
       
            for outputPath in outputPaths: 
                self._addFileToOutputs(outputPath, "Station data file.")

            # Write docs links to output file
            docLinksFile = os.path.join(context.processDir, "outputs", "doc_links.txt")
            self._writeDocLinksFile(docLinksFile, obs_table_names[0])

            # Finish up by calling function to set status to complete and zip up files etc
            # In this case we set keep = True so that weather station file is accessible to downstream process
            # without unzipping. This is fine as files are small.
            process_support.finishProcess(context, self.fileSet, self.startTime, keep=True)

        else:
            outputPaths = ["%s-%s.%s" % (dataFileBase, i, ext) for i in range(nYears + 1)] 
            for outputPath in outputPaths:
                size = nStations * 200 * 365
                self._addFileToOutputs(outputPath, "Station data file.", size = size)

            estimated_duration = (nYears + 1) * 60 # seconds
            process_support.finishDryRun(context, [], self.fileSet,
                            estimated_duration, acceptedMessage = 'Dry run complete')


    def _resolveStationList(self, context, dry_run):
        """
        Works out whether we need to generate a station list or use those
        sent as inputs.
        """
        a = self.args
        stationList = None
        WEATHER_STATIONS_FILE_NAME = "weather_stations.txt"

        # Use input station list if provided
        if a["StationIDs"] != []:
            stationList = a["StationIDs"]

        # Use input job ID to extract text file of stations
        elif a["InputJobId"]:
            input_process_dir = self._locateProcessDir(a["InputJobId"])
            input_weather_stations_file = os.path.join(input_process_dir, "outputs", WEATHER_STATIONS_FILE_NAME)
            stationList = exuk_utils.extractStationsFromFile(input_weather_stations_file)  

        # Add output file
        stationsFile = WEATHER_STATIONS_FILE_NAME
        stationsFilePath = os.path.join(context.processDir, "outputs", stationsFile)

        # If not dry run
        if stationList == None:
            # Call code to get Weather Stations
            counties_list = self._getCounties(a)
            stationList = gws_lib.getStationList(counties_list, a["BBox"], a["DataTypes"], a["StartDateTime"],
                           a["EndDateTime"], stationsFilePath)

        # Write the file one per station id per line
        stationList.sort()
        self._writeStationsFile(stationsFilePath, stationList)

        # Add the stations list to the XML output section: ProcessSpecificContent
        context.outputs['ProcessSpecificContent'] = {"WeatherStations": " ".join(stationList)}

        # Add file to outputs
        self._addFileToOutputs(stationsFilePath, 'Weather Stations File')

        return stationList

    def _writeStationsFile(self, stationsFilePath, stationList):
        "Writes stations file (that were used in the extraction)."
        fout = open(stationsFilePath, "w")
        fout.write("\r\n".join([str(station) for station in stationList]))
        fout.close()

       
    def _writeDocLinksFile(self, docLinksFile, obsTable):
        "Write documentation links file." 

        midas_table_to_moles_dict = {
            "WM":   "http://catalogue.ceda.ac.uk/uuid/a1f65a362c26c9fa667d98c431a1ad38",
            "RH":   "http://catalogue.ceda.ac.uk/uuid/bbd6916225e7475514e17fdbf11141c1",
            "CURS": "http://catalogue.ceda.ac.uk/uuid/7f76ab4a47ee107778e0a7e8a701ee77",
            "ST":   "http://catalogue.ceda.ac.uk/uuid/8dc05f6ecc6065a5d10fc7b8829589ec",
            "GL":   "http://catalogue.ceda.ac.uk/uuid/0ec59f09b3158829a059fe70b17de951",
            "CUNS": "http://catalogue.ceda.ac.uk/uuid/bef3d059255a0feaa14eb78c77d7bc48",
            "TMSL": "http://catalogue.ceda.ac.uk/uuid/33ca1887e5f116057340e404b2c752f2",
            "RO":   "http://catalogue.ceda.ac.uk/uuid/b4c028814a666a651f52f2b37a97c7c7",
            "MO":   "http://catalogue.ceda.ac.uk/uuid/77910bcec71c820d4c92f40d3ed3f249",
            "RS":   "http://catalogue.ceda.ac.uk/uuid/455f0dd48613dada7bfb0ccfcb7a7d41",
            "RD":   "http://catalogue.ceda.ac.uk/uuid/c732716511d3442f05cdeccbe99b8f90",
            "CUNL": "http://catalogue.ceda.ac.uk/uuid/ec1d8e1e511838b9303921986a0137de",
            "TD":   "http://catalogue.ceda.ac.uk/uuid/1bb479d3b1e38c339adb9c82c15579d8",
            "SCLE": "http://catalogue.ceda.ac.uk/uuid/1d9aa0abc4e93fca1f91c8a187d46567",
            "WD":   "http://catalogue.ceda.ac.uk/uuid/954d743d1c07d1dd034c131935db54e0",
            "WH":   "http://catalogue.ceda.ac.uk/uuid/916ac4bbc46f7685ae9a5e10451bae7c",
            "CURL": "http://catalogue.ceda.ac.uk/uuid/fe9a02b85b50d3ee1d0b7366355bb9d8"
            }

        if obsTable not in midas_table_to_moles_dict:
            return

        fout = open(docLinksFile, "w")
        fout.write("Link to documentation: %s#tab_linked_docs\n" % midas_table_to_moles_dict[obsTable])
        fout.close()

        # Add to the output metadata
        self._addFileToOutputs(docLinksFile, "Documentation links file.", size=os.path.getsize(docLinksFile))
 

    def _getCounties(self, args):
        "Returns a list of UK counties as specified in args dictionary."
        # Argument not used in global version
        return args["Counties"]

    def _getObsTableNames(self, args):
        "Returns a list of Table codes required for extraction. Only one relevant for global."
        return [args["ObsTableName"]]

    def _getWorldRegion(self, args):
        "Returns a World Region if specified in args dictionary or None."
        return None

    def _validateInputs(self):
        """
        Runs specific checking of arguments and their compatibility.
        """
        a = self.args
        if a["Counties"] == [] and a["BBox"] == None and a["StationIDs"] == [] and a["InputJobId"] == None:
            raise Exception("Invalid arguments provided. Must provide one of (i) a geographical bounding box, (ii) a list of counties, (iii) a set of station IDs or (iv) an input job ID from which a file containing a set of selected station IDs can be extracted.")
  
        if a["StartDateTime"] > a["EndDateTime"]:
            raise Exception("Invalid arguments provided. StartDateTime cannot be after EndDateTime")
 
