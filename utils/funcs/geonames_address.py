import requests
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_DATA_PATH = os.path.join(BASE_DIR, "Data/countries_full_multilang.json")


def load_geodata():
    """Load and cache the geo JSON data"""
    with open(JSON_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_country_choices(lang="en"):
    """
    Get list of available countries
    Returns: List of [country_code, country_name] pairs sorted by name
    """
    EXCLUDED_COUNTRIES = {"IL"}
    data = load_geodata()
    choices = []

    for country_code, info in data.items():
        if country_code in EXCLUDED_COUNTRIES:
            continue
        name = info.get("names", {}).get(lang) or info.get("names", {}).get("en") or country_code
        choices.append([country_code, name])

    return sorted(choices, key=lambda x: x[1])


def get_province_choices(country_code, lang="en"):
    """
    Get provinces/states for a specific country
    Returns: List of [province_code, province_name] pairs sorted by name
    """
    data = load_geodata()
    country_data = data.get(country_code, {})
    provinces = country_data.get("provinces", {})

    province_choices = []
    for province_code, province_info in provinces.items():
        name = province_info.get("names", {}).get(lang) or \
               province_info.get("names", {}).get("en") or \
               province_code
        province_choices.append([province_code, name])

    return sorted(province_choices, key=lambda x: x[1])


def get_city_choices(country_code, province_code, lang="en"):
    """
    Get cities for a specific province in a country
    Returns: List of [city_code, city_name] pairs sorted by name
             or None if province has no cities data
    """
    data = load_geodata()

    # Get country data
    country_data = data.get(country_code, {})
    if not country_data:
        return None

    # Get province data
    province_data = country_data.get("provinces", {}).get(province_code, {})
    if not province_data:
        return None

    # Get cities data
    cities = province_data.get("cities", {})
    if not cities:
        return None

    city_choices = []
    for city_code, city_info in cities.items():
        name = city_info.get("names", {}).get(lang) or \
               city_info.get("names", {}).get("en") or \
               city_code
        city_choices.append([city_code, name])

    return sorted(city_choices, key=lambda x: x[1])