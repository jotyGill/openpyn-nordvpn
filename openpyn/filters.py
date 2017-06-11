import operator
import sys
from openpyn import locations


def filter_by_toppest(pinged_servers_list, toppest_servers):
    remaining_servers = []

    # 5 top servers or if less than 5 totel servers
    for server_counter in range(toppest_servers):
        if server_counter < len(pinged_servers_list):
            remaining_servers.append(pinged_servers_list[server_counter])
            server_counter += 1
    return remaining_servers


def filter_by_area(area, type_country_filtered):
    remaining_servers = []
    resolved_locations = locations.get_unique_locations(list_of_servers=type_country_filtered)
    for aServer in type_country_filtered:
        for item in resolved_locations:
            if aServer["location"]["lat"] == item[1]["lat"] and \
                    aServer["location"]["long"] == item[1]["long"] and area in item[2]:
                    aServer["location_names"] = item[2]  # add location info to server
                    # print(aServer)
                    remaining_servers.append(aServer)
    return remaining_servers


def filter_by_country(country_code, type_filtered_servers):
    remaining_servers = []
    for aServer in type_filtered_servers:
        if aServer["domain"][:2].lower() == country_code.lower():
            remaining_servers.append(aServer)
            # print(remaining_servers)
    return remaining_servers


def filter_by_type(json_response, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos):
    remaining_servers = []
    serverCount = 0
    for eachServer in json_response:
        serverCount += 1
        for ServerType in eachServer["categories"]:
            # print(eachServer["categories"])
            if p2p and ServerType["name"] == "P2P":
                remaining_servers.append(eachServer)
            if dedicated and ServerType["name"] == "Dedicated IP servers":
                remaining_servers.append(eachServer)
            if double_vpn and ServerType["name"] == "Double VPN":
                remaining_servers.append(eachServer)
            if tor_over_vpn and ServerType["name"] == "Onion over VPN":
                remaining_servers.append(eachServer)
            if anti_ddos and ServerType["name"] == "Anti DDoS":
                remaining_servers.append(eachServer)
            if p2p is False and dedicated is False and double_vpn is False and \
                    tor_over_vpn is False and anti_ddos is False:
                if ServerType["name"] == "Standard VPN servers":
                    remaining_servers.append(eachServer)
    # print("Total available servers = ", serverCount)
    return remaining_servers


def filter_by_protocol(json_res_list, udp):
    remaining_servers = []

    for res in json_res_list:
        # when connecting using UDP only append if it supports OpenVPN-UDP
        if udp is True and res["features"]["openvpn_udp"] is True:
            remaining_servers.append([res["domain"][:res["domain"].find(".")], res["load"]])
        # when connecting using TCP only append if it supports OpenVPN-TCP
        elif udp is False and res["features"]["openvpn_tcp"] is True:
            remaining_servers.append([res["domain"][:res["domain"].find(".")], res["load"]])
            # print("TCP SERVESR :", res["feature"], res["feature"]["openvpn_tcp"])
    return remaining_servers


# Exclude servers over "max_load" and only keep < "top_servers"
def filter_by_load(server_list, max_load, top_servers):
    remaining_servers = []
    # sort list by the server load
    server_list.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in server_list:
        server_load = int(server[1])
        # skip if server_load < 4, sometimes they don't work
        if server_load < max_load and len(remaining_servers) < top_servers and server_load > 3:
            remaining_servers.append(server)

    if len(remaining_servers) < 1:    # if no servers under search criteria
        print("There are no servers that satisfy your criteria, please broaden your search.")
        sys.exit()
    return remaining_servers
