"""
utils.py
========

Utils for get_weather_stations.py that holds the GetWeatherStations class.

Also supports the extract_uk_station_data.py module.

"""

import sys
import logging

# MIDAS Station search code
from midas.getStations import *

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def translateBBox(wps_bbox):
    """
    Converts BBox definition in WPS to BBox definition in MIDAS code:

      * Input =  (w, s, e, n)
      * Output = (n, w, s, e)

    """
    (w, s, e, n) = wps_bbox
    midas_bbox = (n, w, s, e)

    return midas_bbox


def getStationList(counties, bbox, dataTypes, startTime, endTime, outputFile):
    """
    Wrapper to call of midas station getter code.

    """
    # Translate bbox if it is used
    if bbox != None:
        bbox = translateBBox(bbox)

    station_getter = getStations.StationIDGetter(counties, bbox = bbox, dataTypes = dataTypes, 
                       startTime = startTime, endTime = endTime, outputFile = outputFile, noprint = 1) 

    return station_getter.stList


def revertDateTimeToLongString(dt):
    """
    Turns a date/time into a long string as needed by midas code.
    """
    return str(dt).replace("-", "").replace(" ", "").replace("T", "").replace(":", "") 

