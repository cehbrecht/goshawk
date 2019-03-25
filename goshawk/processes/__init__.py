from .wps_say_hello import SayHello
from .wps_get_weather_stations import GetWeatherStations

processes = [
    SayHello(),
    GetWeatherStations(),
]
