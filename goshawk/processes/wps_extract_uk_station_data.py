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


class ExtractUKStationData(Process):
    """A process extracting UK station data."""
    def __init__(self):
        inputs = [
            LiteralInput('StartDateTime', 'Start Date Time',
                         abstract='The first date/time for which you wish to extract data.',
                         data_type='dateTime',
                         default='2009-01-01T12:00:00Z'),
            LiteralInput('EndDateTime', 'End Date Time',
                         abstract='The last date/time for which you wish to extract data.',
                         data_type='dateTime',
                         default='2019-03-25T12:00:00Z'),
            LiteralInput('OutputTimeChunk', 'Output Time Chunk',
                         abstract='The period of time spanned by each output file.',
                         data_type='string',
                         allowed_values=['decade', 'year', 'month'],
                         min_occurs=0),
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
            LiteralInput('StationIDs', 'Station Source IDs',
                         abstract='A list of weather stations source IDs.'
                                  ' This input will be ignored if an input job ID is provided.',
                         data_type='string',
                         min_occurs=0),
            LiteralInput('InputJobId', 'Input Job Id',
                         abstract='The Id of a separate WPS Job used to select a set of weather stations.',
                         data_type='string',
                         min_occurs=0),
            LiteralInput('ObsTableName', 'Obervation Table Name',
                         abstract='The name of the database table used in the MIDAS database to identify'
                                  ' a particular selection of weather observations.',
                         data_type='string',
                         allowed_values=['TD', 'WD', 'RD', 'RH', 'RS', 'ST', 'WH', 'WM', 'RO'],
                         # UK Daily Temperature, UK Daily Weather, UK Daily Rain,
                         # UK Hourly Rain, UK Sub-hourly Rain (to April 2005),
                         # UK Soil Temperature, UK Hourly Weather,
                         # UK Mean Wind, Global Radiation Observations
                         min_occurs=0),
            LiteralInput('Delimiter', 'Delimiter',
                         abstract='The delimiter to be used in the output files.',
                         data_type='string',
                         allowed_values=['comma', 'tab'],
                         min_occurs=0),
        ]
        outputs = [
            ComplexOutput('output', 'Output',
                          abstract='Station list as XML.',
                          as_reference=True,
                          supported_formats=[Format('text/xml')])]

        super(ExtractUKStationData, self).__init__(
            self._handler,
            identifier='ExtractUKStationData',
            title='Extract UK Station Data',
            abstract='The "Extract UK Station Data" process provides tools to'
                     ' access surface station weather observations for a range'
                     ' of variables throughout the UK.'
                     ' These include temperature, rainfall and wind measurements.'
                     ' These records are available from 1859 to this year.'
                     ' You can select which stations you require using'
                     ' either a bounding box, a list of UK counties,'
                     ' a list of station IDs or an uploaded file containing station IDs.'
                     ' Data is returned in CSV or tab-delimited text files.'
                     ' Please see the disclaimer.',
            keywords=['stations', 'uk', 'demo'],
            metadata=[
                Metadata('User Guide', 'http://badc.nerc.ac.uk/data/ukmo-midas/WPS.html'),
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
        LOGGER.info("extracting UK station data")
        response.outputs['output'].data = '<xml>Didcot</xml>'
        return response
