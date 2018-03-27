import sys

import requests
from colorama import Fore, Style
from openpyn import filters


# Using requests, GETs and returns json from a url.
def get_json(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    try:
        json_response = requests.get(url, headers=headers).json()
    except requests.exceptions.HTTPError:
        print("Cannot GET the json from nordvpn.com, Manually Specify a Server\
        using '-s' for example '-s au10'")
        sys.exit()
    except requests.exceptions.RequestException:
        print("There was an ambiguous exception, Check Your Network Connection.",
              "forgot to flush iptables? (openpyn -x)")
        sys.exit()
    return json_response


# Gets json data, from api.nordvpn.com. filter servers by type, country, area.
def get_data_from_api(
        country_code, area, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos, netflix):

    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)

    type_filtered_servers = filters.filter_by_type(
        json_response, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos, netflix)
    if country_code != "all":       # if "-l" had country code with it. e.g "-l au"
        type_country_filtered = filters.filter_by_country(country_code, type_filtered_servers)
        if area is None:
            return type_country_filtered
        type_country_area_filtered = filters.filter_by_area(area, type_country_filtered)
        return type_country_area_filtered
    return type_filtered_servers


def list_all_countries():
    countries_mapping = {}
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["domain"][:2] not in countries_mapping:
            countries_mapping.update({res["domain"][:2]: res["country"]})
    for key, val in countries_mapping.items():
        print("Full Name : " + val + "      Country Code : " + key + '\n')
    sys.exit()


def get_country_code(full_name):
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["country"].lower() == full_name.lower():
            code = res["domain"][:2].lower()
            return code
    print(Fore.RED + "Country Name Not Correct")
    print(Style.RESET_ALL)
    sys.exit()
