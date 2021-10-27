import logging
import operator
from typing import List

import verboselogs

from openpyn import locations

verboselogs.install()
logger = logging.getLogger(__package__)


def filter_by_area(area: str, type_country_filtered: List) -> List:
    remaining_servers = []
    resolved_locations = locations.get_unique_locations(list_of_servers=type_country_filtered)
    for aServer in type_country_filtered:
        for item in resolved_locations:
            lower_case_areas = [x.lower() for x in item[2]]
            if aServer["location"]["lat"] == item[1]["lat"] and \
                    aServer["location"]["long"] == item[1]["long"] and \
                    area.lower() in lower_case_areas:
                aServer["location_names"] = item[2]  # add location info to server
                remaining_servers.append(aServer)
                # logger.debug(aServer)
    return remaining_servers


def filter_by_country(country_code: str, type_filtered_servers: List) -> List:
    remaining_servers = []
    for aServer in type_filtered_servers:
        if aServer["domain"][:2] == country_code:
            remaining_servers.append(aServer)
            # logger.debug(aServer["domain"])
    return remaining_servers


def filter_by_location(location: float, type_filtered_servers: List) -> List:
    remaining_servers = []
    for aServer in type_filtered_servers:
        if aServer["location"]["lat"] == location[0] and aServer["location"]["long"] == location[1]:
            remaining_servers.append(aServer)
            # logger.debug(aServer)
    return remaining_servers


def filter_by_netflix(json_response, country_code: str) -> List:
    remaining_servers = []
    server_count = 0
    netflix_us = [[585, 592, "us"], [603, 604, "us"], [609, 617, "us"], [625, 632, "us"], [645, 680, "us"],
                  [690, 690, "us"], [707, 710, "us"], [722, 737, "us"], [777, 780, "us"], [797, 804, "us"],
                  [833, 843, "us"], [856, 853, "us"], [872, 879, "us"], [896, 903, "us"], [908, 919, "us"],
                  [936, 939, "us"], [972, 987, "us"], [1016, 1020, "us"], [1033, 1041, "us"], [1046, 1049, "us"],
                  [1054, 1086, "us"], [1102, 1130, "us"], [1138, 1141, "us"], [1150, 1157, "us"], [1162, 1195, "us"],
                  [1236, 1239, "us"], [1248, 1255, "us"], [1260, 1279, "us"], [1284, 1287, "us"], [1297, 1312, "us"],
                  [1322, 1341, "us"], [1346, 1357, "us"], [1362, 1365, "us"], [1370, 1373, "us"], [1418, 1421, "us"],
                  [1426, 1429, "us"], [1442, 1457, "us"], [1470, 1479, "us"], [1484, 1495, "us"], [1500, 1515, "us"],
                  [1520, 1539, "us"], [1560, 1599, "us"], [1604, 1607, "us"], [1612, 1671, "us"], [1676, 1691, "us"],
                  [1696, 1707, "us"], [1709, 1737, "us"], [1742, 1745, "us"], [1750, 1793, "us"], [1798, 1801, "us"],
                  [1806, 2029, "us"], [2034, 2045, "us"], [2048, 2139, "us"], [2144, 2203, "us"], [2216, 2223, "us"],
                  [2228, 2392, "us"], [2396, 2411, "us"], [2428, 2451, "us"], [2460, 2488, "us"], [2509, 2524, "us"],
                  [2533, 2536, "us"], [2545, 2548, "us"], [2561, 2564, "us"], [2573, 2600, "us"], [2609, 2616, "us"],
                  [2621, 2632, "us"], [2642, 2645, "us"], [2674, 2677, "us"], [2686, 2705, "us"], [2710, 2721, "us"],
                  [2730, 2749, "us"], [2758, 2765, "us"], [2778, 2789, "us"], [2794, 2805, "us"], [2810, 2825, "us"],
                  [2834, 2843, "us"], [2848, 2851, "us"], [2853, 2853, "us"], [2862, 2870, "us"], [2872, 2872, "us"],
                  [2877, 2893, "us"], [2895, 2895, "us"], [2897, 2899, "us"], [2951, 2953, "us"]]

    netflix_ca = [[18, 21, "ca"], [27, 30, "ca"], [37, 40, "ca"], [49, 56, "ca"], [61, 64, "ca"], [69, 76, "ca"],
                  [81, 90, "ca"], [103, 104, "ca"], [117, 124, "ca"], [149, 343, "ca"], [367, 453, "ca"], [456, 457, "ca"],
                  [461, 462, "ca"]]

    netflix_nl = [[21, 24, "nl"], [39, 42, "nl"], [44, 47, "nl"], [52, 67, "nl"], [156, 264, "nl"], [269, 287, "nl"],
                  [292, 331, "nl"], [360, 360, "nl"], [373, 373, "nl"], [375, 377, "nl"], [382, 387, "nl"], [21, 24, "nl"],
                  [39, 42, "nl"], [44, 47, "nl"], [52, 67, "nl"], [156, 264, "nl"], [269, 287, "nl"], [292, 331, "nl"],
                  [360, 360, "nl"], [373, 373, "nl"], [375, 377, "nl"], [382, 387, "nl"]]

    netflix_jp = [[15, 16, "jp"], [26, 29, "jp"], [67, 69, "jp"], [71, 74, "jp"], [115, 126, "jp"], [175, 175, "jp"],
                  [181, 181, "jp"]]

    netflix_uk = [[69, 72, "uk"], [89, 89, "uk"], [154, 156, "uk"], [178, 181, "uk"], [195, 199, "uk"], [228, 231, "uk"],
                  [264, 275, "uk"], [280, 283, "uk"], [300, 303, "uk"], [336, 339, "uk"], [344, 347, "uk"], [372, 375, "uk"],
                  [380, 383, "uk"], [393, 400, "uk"], [417, 420, "uk"], [425, 428, "uk"], [433, 436, "uk"], [457, 460, "uk"],
                  [465, 468, "uk"], [484, 487, "uk"], [496, 496, "uk"], [565, 568, "uk"], [593, 596, "uk"], [609, 612, "uk"],
                  [617, 620, "uk"], [637, 640, "uk"], [649, 656, "uk"], [673, 676, "uk"], [701, 704, "uk"], [705, 708, "uk"],
                  [725, 728, "uk"], [765, 766, "uk"]]

    netflix_gr = [[3, 3, "gr"]]

    netflix_mx = [[3, 9, "mx"], [11, 11, "mx"]]

    netflix_srv = []

    # Google Sheets Formula
    # =CONCATENATE("[",IF(ISERR(FIND("-", A1)),CONCATENATE(A1,", ",A1),SUBSTITUTE(A1,"-",", ")), ", ""us""", "]")

    if country_code == "us":
        netflix_srv = netflix_us
    elif country_code == "ca":
        netflix_srv = netflix_ca
    elif country_code == "nl":
        netflix_srv = netflix_nl
    elif country_code == "jp":
        netflix_srv = netflix_jp
    elif country_code == "uk":
        netflix_srv = netflix_uk
    elif country_code == "gr":
        netflix_srv = netflix_gr
    elif country_code == "mx":
        netflix_srv = netflix_mx
    elif country_code == "all":
        netflix_srv = netflix_us + netflix_ca + netflix_nl + netflix_jp + netflix_uk + netflix_gr + netflix_mx

    for eachServer in json_response:
        server_count += 1
        for server in netflix_srv:
            for number in range(server[0], server[1] + 1):
                if server[2] + str(number) + "." in eachServer["domain"]:
                    remaining_servers.append(eachServer)
                    # logger.debug(eachServer["domain"])
    # logger.debug("Total available servers = ", serverCount)
    return remaining_servers


def filter_by_type(json_response, p2p: bool, dedicated: bool, double_vpn: bool, tor_over_vpn: bool, anti_ddos: bool) -> List:
    remaining_servers = []
    server_count = 0
    standard_vpn = False

    if p2p is False and dedicated is False and double_vpn is False and tor_over_vpn is False and anti_ddos is False:
        standard_vpn = True

    for eachServer in json_response:
        server_count += 1
        for ServerType in eachServer["categories"]:
            if p2p and ServerType["name"] == "P2P":
                remaining_servers.append(eachServer)
                break
            if dedicated and ServerType["name"] == "Dedicated IP":
                remaining_servers.append(eachServer)
                break
            if double_vpn and ServerType["name"] == "Double VPN":
                remaining_servers.append(eachServer)
                break
            if tor_over_vpn and ServerType["name"] == "Onion Over VPN":
                remaining_servers.append(eachServer)
                break
            if anti_ddos and ServerType["name"] == "Obfuscated Servers":
                remaining_servers.append(eachServer)
                break
            if standard_vpn and ServerType["name"] == "Standard VPN servers":
                remaining_servers.append(eachServer)
                break
    # logger.debug("Total available servers = ", serverCount)
    return remaining_servers


def filter_by_protocol(json_res_list: List, tcp: bool) -> List:
    remaining_servers = []

    for res in json_res_list:
        # when connecting using TCP only append if it supports OpenVPN-TCP
        if tcp is True and res["features"]["openvpn_tcp"] is True:
            remaining_servers.append([res["domain"][:res["domain"].find(".")], res["load"]])
        # when connecting using UDP only append if it supports OpenVPN-UDP
        elif tcp is False and res["features"]["openvpn_udp"] is True:
            remaining_servers.append([res["domain"][:res["domain"].find(".")], res["load"]])
    return remaining_servers


# Exclude servers over "max_load" and only keep < "top_servers"
def filter_by_load(server_list: List, max_load: int, top_servers: int) -> List:
    remaining_servers = []
    # sort list by the server load
    server_list.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in server_list:
        server_load = int(server[1])
        # skip if server_load < 6, sometimes they don't work
        if max_load >= server_load > 5:
            if len(remaining_servers) < top_servers:
                remaining_servers.append(server)
    return remaining_servers
