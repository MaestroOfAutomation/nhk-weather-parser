"""
Core data models for NHK Japan Weather Parser.
"""
from dataclasses import dataclass


@dataclass
class CityWeather:
    """
    Data class for city weather information.
    
    :param jp: Japanese city name.
    :param ru: Russian city name.
    :param max_c: Maximum temperature in Celsius.
    :param alt: Weather condition description.
    """
    jp: str
    ru: str
    max_c: str
    alt: str