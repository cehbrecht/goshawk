"""
lib.py
======

Util functions for process extract_uk_station_data that holds the ExtractUKStationData class.

"""

import os, stat, time, sys
import zipfile

from cows_wps.process_handler.context.process_status import STATUS
from cows_wps.utils.duration_splitter import *

# MIDAS Station search code
from midas.midasSubsetter import *


def extractStationDataByTimeChunk(obs_tables, startTime, endTime, src_ids, time_chunk, 
                    output_file_base, delimiter, ext, tempDir, context, world_region = None):
    """
    Loops through time chunks extracting data to files in required time chunks.
    We pass the context object through here so that we can report progress.
    Returns a list of output file paths produced.
    """ 
    start_hr_min = startTime[8:12]
    end_hr_min = endTime[8:12]

    # Split the time chunks appropriately
    ds = DurationSplitter()
    time_splits = ds.splitDuration(startTime[:8], endTime[:8], time_chunk)
    first_date = True

    # Create list to return
    output_file_paths = []

    progress = 5 # % of way to completion

    for (count, (start_date, end_date)) in enumerate(time_splits): 

        # Add appropriate hours and minutes to date strings to make 12 character times
        if first_date == True:
            start = "%s%s" % (start_date.date, start_hr_min)
            first_date = False
        else:
            start = "%s0000" % (start_date.date)
       
        if end_date == time_splits[-1][-1]:
            end = "%s%s" % (end_date.date, end_hr_min)
        else:
            end = "%s2359" % (end_date.date)

        # Decide the output file path
        output_file_path = "%s-%s-%s.%s" % (output_file_base, start, end, ext)
        output_file_paths.append(output_file_path)
 
        # Call subsetter to extract and write the data    
        midasSubsetter.MIDASSubsetter(obs_tables, output_file_path, startTime = start,
                       endTime = end, src_ids = src_ids, delimiter = delimiter, 
                       tempDir = tempDir, region = world_region)

        # Report on progress
        progress = int(float(count) / len(time_splits) * 100)
        context.setStatus(STATUS.STARTED, 'Station data being extracted', progress)
        context.saveStatus()
        
    return output_file_paths


def extractStationsFromFile(stations_file):
    """
    Reads file and extracts stations to a list.
    """
    df = open(stations_file)
    station_ids = df.read().split()
    df.close()
    return station_ids
