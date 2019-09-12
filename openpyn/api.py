import logging
from typing import Dict, List

import requests
import verboselogs
from openpyn import filters

logger = logging.getLogger(__package__)
verboselogs.install()


# Using requests, GETs and returns json from a url.
def get_json(url) -> Dict:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    try:
        json_response = requests.get(url, headers=headers).json()
    except requests.exceptions.HTTPError:
        raise RuntimeError("Cannot GET the JSON from nordvpn.com, Manually Specify a Server \
using '-s' for example '-s au10'")
    except requests.exceptions.RequestException:
        raise RuntimeError("Error while connecting to {}, Check Your Network Connection. \
forgot to flush iptables? (openpyn -x)".format(url))
    return json_response


# Gets json data, from api.nordvpn.com. filter servers by type, country, area.
def get_data_from_api(
        country_code: str, area: str, p2p: bool, dedicated: bool, double_vpn: bool,
        tor_over_vpn: bool, anti_ddos: bool, netflix: bool, location: float) -> List:
    country_code = country_code.lower()
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)

    type_filtered_servers = []
    if netflix:
        type_filtered_servers = filters.filter_by_netflix(json_response, country_code)
    else:
        type_filtered_servers = filters.filter_by_type(json_response, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos)
    if location:
        type_location_filtered = filters.filter_by_location(location, type_filtered_servers)
        return type_location_filtered
    if country_code != "all":       # if "-l" had country code with it. e.g "-l au"
        type_country_filtered = filters.filter_by_country(country_code, type_filtered_servers)
        if area is None:
            return type_country_filtered
        type_country_area_filtered = filters.filter_by_area(area, type_country_filtered)
        return type_country_area_filtered
    return type_filtered_servers


def list_all_countries() -> None:
    countries_mapping = {}
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["domain"][:2] not in countries_mapping:
            countries_mapping.update({res["domain"][:2]: res["country"]})
    for key, val in countries_mapping.items():
        print("Full Name : " + val + "\t\tCountry Code : " + key)


def get_country_code(full_name: str) -> str:
    full_name = full_name.lower()
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["country"].lower() == full_name:
            code = res["domain"][:2]
            return code
    raise RuntimeError("Country Name Not Correct")


def get_country_name(iso_code: str) -> str:
    iso_code = iso_code.lower()
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["domain"][:2] == iso_code:
            name = res["country"]
            return name
    raise RuntimeError("Country Code Not Correct")
