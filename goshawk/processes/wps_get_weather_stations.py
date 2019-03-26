from pywps import Process, LiteralInput, ComplexOutput, BoundingBoxInput, Format
from pywps.app.Common import Metadata

import logging
LOGGER = logging.getLogger("PYWPS")


UK_COUNTIES = [
    'ABERDEENSHIRE',
    'ALDERNEY',
    'ANGUS',
    'ANTRIM',
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
            LiteralInput('Counties', 'Counties',
                         abstract='A list of counties within which to search for weather stations.',
                         data_type='string',
                         allowed_values=UK_COUNTIES,
                         min_occurs=0),
            LiteralInput('DataTypes', 'Data Types',
                         abstract='A list of counties within which to search for weather stations.',
                         data_type='string',
                         allowed_values=['CLBD', 'CLBN', 'CLBR', 'CLBW', 'DCNN', 'FIXD',
                                         'ICAO', 'LPMS', 'RAIN', 'SHIP', 'WIND', 'WMO'],
                         min_occurs=0),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Station list as XML.',
                          as_reference=True,
                          supported_formats=[Format('text/xml')])]

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

    @staticmethod
    def _handler(request, response):
        LOGGER.info("getting uk weather stations.")
        response.outputs['output'].data = '<xml>Didcot</xml>'
        return response
