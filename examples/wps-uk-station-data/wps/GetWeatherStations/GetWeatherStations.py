"""
get_weather_stations.py
===================

Process get_weather_stations that holds the GetWeatherStations class.

"""

import os, stat, time
import sys
import logging

from cows_wps.process_handler.fileset import FileSet, FLAG
import cows_wps.process_handler.process_support as process_support
from cows_wps.process_handler.context.process_status import STATUS

import lib as gws_utils
import processes.internal.ProcessBase.ProcessBase


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class GetWeatherStations(processes.internal.ProcessBase.ProcessBase.ProcessBase):

    # Define arguments that we need to set from inputs
    args_to_set = ["Counties", "BBox", "DataTypes", "StartDateTime", "EndDateTime"]

    # Define defaults for arguments that might not be set
    input_arg_defaults = {"Counties": [],
                          "BBox": None,
                          "DataTypes": [],
                         }

    # Define a dictionary for arguments that need to be processed 
    # before they are set (with values as the function doing the processing).
    arg_processers = {"StartDateTime": gws_utils.revertDateTimeToLongString, 
                      "EndDateTime": gws_utils.revertDateTimeToLongString}

    
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

        # Add output file 
        stationsFile = 'weather_stations.txt'
        stationsFilePath = os.path.join(context.processDir, "outputs", stationsFile)

        if not dry_run:
            # Call code to get Weather Stations
            stationList = gws_utils.getStationList(a["Counties"], a["BBox"], a["DataTypes"], 
                           a["StartDateTime"], a["EndDateTime"], stationsFilePath)
        
            # Add the stations list to the XML output section: ProcessSpecificContent
            context.outputs['ProcessSpecificContent'] = {"WeatherStations": " ".join(stationList)} 

        # In this case we want to inform the output XML that you can send the outputs to a separate process
        # This string can be picked up the an intelligent client in order to construct a new WPS request
        # with this job as its input
        context.outputs['job_details']['job_capabilities'] = "send_to_extract_weather_data"

        if not dry_run:
            # We can log information at any time to the main log file
            context.log.info('Written output file: %s' % stationsFilePath)
        else:
            context.log.debug("Running dry run.")

        # Add the stations file to the outputs
        if not dry_run:
            self._addFileToOutputs(stationsFilePath, 'Weather Stations File')
        else:
            # Estimate size of outputs by estimating the number of stations
            if len(a["Counties"]) > 0:
                nEstimatedStations = len(a["Counties"]) * 15
            else:
                (w, s, e, n) = a["BBox"]
                lonExtent = abs(e - w)
                latExtent = n - s
                nEstimatedStations = int(lonExtent * latExtent * 50)

            estimatedVolume = nEstimatedStations * 5
            self._addFileToOutputs(stationsFilePath, 'Weather Stations File', size = estimatedVolume)

        if not dry_run:
            # Finish up by calling function to set status to complete and zip up files etc
            # In this case we set keep = True so that weather station file is accessible to downstream process
            # without unzipping. This is fine as files are small.
            process_support.finishProcess(context, self.fileSet, self.startTime, keep = True)
        else:
            estimated_duration = 10 # seconds
            process_support.finishDryRun(context, [], self.fileSet,
                            estimated_duration, acceptedMessage = 'Dry run complete')           


    def _validateInputs(self):
        """
        Runs specific checking of arguments and their compatibility.
        """
        if self.args["Counties"] == [] and self.args["BBox"] == None:
            raise Exception("Invalid arguments provided. Must provide either a geographical bounding box or a list of counties.")

        if self.args["StartDateTime"] > self.args["EndDateTime"]:
            raise Exception("Invalid arguments provided. StartDateTime cannot be after EndDateTime")
