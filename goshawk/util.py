from goshawk.midas import getStations


def translate_bbox(wps_bbox):
    """
    Converts BBox definition in WPS to BBox definition in MIDAS code:

      * Input =  (w, s, e, n)
      * Output = (n, w, s, e)

    """
    (w, s, e, n) = wps_bbox
    midas_bbox = (n, w, s, e)
    return midas_bbox


def get_station_list(counties, bbox, data_types, start_time, end_time, output_file):
    """
    Wrapper to call of midas station getter code.
    """
    # Translate bbox if it is used
    if bbox is not None:
        bbox = translate_bbox(bbox)

    station_getter = getStations.StationIDGetter(
        counties,
        bbox=bbox,
        dataTypes=data_types,
        startTime=revert_datetime_to_long_string(start_time),
        endTime=revert_datetime_to_long_string(end_time),
        outputFile=output_file,
        noprint=1)

    return station_getter.stList


def revert_datetime_to_long_string(dt):
    """
    Turns a date/time into a long string as needed by midas code.
    """
    return str(dt).replace("-", "").replace(" ", "").replace("T", "").replace(":", "")
