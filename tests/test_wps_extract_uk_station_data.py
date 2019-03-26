import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output
from goshawk.processes.wps_extract_uk_station_data import ExtractUKStationData


def test_wps_extract_uk_station_data():
    client = client_for(Service(processes=[ExtractUKStationData()]))
    datainputs = ""
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=ExtractUKStationData&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
