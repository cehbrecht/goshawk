import os.path

from pywps import Process, LiteralInput, ComplexOutput, BoundingBoxInput
from pywps import FORMATS
from pywps.app.Common import Metadata

from goshawk.util import get_station_list

import logging
LOGGER = logging.getLogger("PYWPS")


UK_COUNTIES = [
    'cornwall',
    'devon',
    'wiltshire'
]


class GetWeatherStations(Process):
    """A process getting UK weather stations."""
    def __init__(self):
        inputs = [
            LiteralInput('StartDateTime', 'Start Date Time',
                         abstract='The first date/time for which to search for operating weather stations.',
                         data_type='dateTime',
                         default='2009-01-01T12:00:00Z'),
            LiteralInput('EndDateTime', 'End Date Time',
                         abstract='The last date/time for which to search for operating weather stations.',
                         data_type='dateTime',
                         default='2019-03-25T12:00:00Z'),
            BoundingBoxInput('BBox', 'Bounding Box',
                             abstract='The spatial bounding box within which to search for weather stations.'
                                      ' This input will be ignored if counties are provided.',
                             crss=['epsg:4326', 'epsg:3035'],
                             min_occurs=0),
            LiteralInput('counties', 'Counties',  # TOOO: issue in birdy with uppercase identifier
                         abstract='A list of counties within which to search for weather stations.',
                         data_type='string',
                         allowed_values=UK_COUNTIES,
                         min_occurs=0),
            LiteralInput('DataTypes', 'Data Types',
                         data_type='string',
                         allowed_values=['CLBD', 'CLBN', 'CLBR', 'CLBW', 'DCNN', 'FIXD',
                                         'ICAO', 'LPMS', 'RAIN', 'SHIP', 'WIND', 'WMO'],
                         min_occurs=0),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Station list.',
                          as_reference=True,
                          supported_formats=[FORMATS.TEXT])]

        super(GetWeatherStations, self).__init__(
            self._handler,
            identifier='GetWeatherStations',
            title='Get Weather Stations',
            abstract='The "GetWeatherStations" process allows the user to identify'
                     ' a set of Weather Station numeric IDs.'
                     ' These can be selected using temporal and spatial filters to derive a list of stations'
                     ' that the user is interested in. The output is a text file containing one station ID per line.'
                     ' Please see the disclaimer.',
            keywords=['stations', 'uk', 'demo'],
            metadata=[
                Metadata('User Guide', 'http://goshawk.readthedocs.io/en/latest/'),
                Metadata('COWS WPS', 'http://wps-web1.ceda.ac.uk/ui/home'),
                Metadata('Disclaimer' 'https://help.ceda.ac.uk/article/4642-disclaimer')
            ],
            version='1.0',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):
        # TODO: dry_run option

        # Now set status to started
        response.update_status('Job is now running', 0)

        if 'counties' in request.inputs:
            counties = [c.data for c in request.inputs['counties']]
        else:
            counties = []

        if 'BBox' in request.inputs:
            bbox = request.inputs['BBox'][0].data
        else:
            bbox = None

        if 'DataTypes' in request.inputs:
            data_types = [data_type.data for data_type in request.inputs['DataTypes']]
        else:
            data_types = []

        # Add output file
        stations_file = os.path.join(self.workdir, 'weather_stations.txt')
        get_station_list(
            counties=counties,
            bbox=bbox,
            data_types=data_types,
            start_time=request.inputs['StartDateTime'][0].data,
            end_time=request.inputs['EndDateTime'][0].data,
            output_file=stations_file)

        # We can log information at any time to the main log file
        LOGGER.info('Written output file: {}'.format(stations_file))

        response.outputs['output'].file = stations_file
        return response
