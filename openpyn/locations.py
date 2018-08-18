import logging
import random
import sys
import time
from typing import Dict, List, Set

import requests
import verboselogs

verboselogs.install()
logger = logging.getLogger(__package__)

user_agents = ['Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0',
               'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
               'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0',
               'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:59.0) Gecko/20100101 Firefox/59.0',
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:59.0) Gecko/20100101 Firefox/59.0']


# takes server list outputs locations (each only once) the servers are in.
def get_unique_locations(list_of_servers: List) -> List:
    unique_locations = []
    resolved_locations = []
    locations_count = 0

    for aServer in list_of_servers:
        latLongDic = {"lat": aServer["location"]["lat"], "long": aServer["location"]["long"]}
        if latLongDic not in unique_locations:
            unique_locations.append(latLongDic)
    # logger.debug(unique_locations)
    for eachLocation in unique_locations:
        user_agent = {'User-Agent': user_agents[locations_count % 6],
                      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        geo_address_list = get_locations(eachLocation, user_agent)
        time.sleep(random.randrange(1, 5, 1) * 0.1)
        resolved_locations.append(geo_address_list)
        locations_count += 1
    # logger.debug("resolved_locations %s", resolved_locations)
    return resolved_locations


def get_locations(location_dic: Dict, req_headers: str) -> List:
    latitude = location_dic["lat"]
    longitude = location_dic["long"]

    url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2'
    params = "&lat={lat}&lon={lon}".format(
        lat=latitude,
        lon=longitude
    )
    final_url = url + params
    # logger.debug("req_headers %s", req_headers)
    r = requests.get(final_url, headers=req_headers)
    geo_address_list = []
    name_list = []
    try:
        response = r.json()
        results = response['address']
        # logger.debug(results)
    except IndexError:
        logger.error("IndexError: Looks like you have reached API's daily request limit. \
No location data for you :( you could restart your router to get a new IP.")
        sys.exit()

    geo_address_list.append(location_dic)

    for key in results:
        # logger.debug(results["city"])
        if key == "country_code":
            geo_address_list.insert(0, results["country"])
        if key == "village":
            name_list.append(results["village"])
        if key == "city":
            name_list.append(results["city"])
        if key == "suburb":
            name_list.append(results["suburb"])
        if key == "region":
            name_list.append(results["region"])
        if key == "state":
            name_list.append(results["state"])
        if key == "state_district":
            name_list.append(results["state_district"])
    geo_address_list.insert(2, name_list)
    logger.debug(geo_address_list)
    return geo_address_list
