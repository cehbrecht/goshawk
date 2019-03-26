import pytest

from pywps import Service
from pywps.tests import client_for, assert_response_success

from .common import get_output
from goshawk.processes.wps_get_weather_stations import GetWeatherStations


def test_wps_get_weather_stations():
    client = client_for(Service(processes=[GetWeatherStations()]))
    datainputs = "Counties=cornwall"
    resp = client.get(
        "?service=WPS&request=Execute&version=1.0.0&identifier=GetWeatherStations&datainputs={}".format(
            datainputs))
    assert_response_success(resp)
    assert 'output' in get_output(resp.xml)
