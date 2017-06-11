#!/usr/bin/python3

from openpyn import filters
from openpyn import locations
from openpyn import firewall
from openpyn import root
from openpyn import credentials
from openpyn import __version__

import subprocess
import argparse
import requests
import random
import os
import json
import sys
import platform
import time


def main():
    parser = argparse.ArgumentParser(
        description="A python3 script (GPLv3+) to easily connect to and switch between, OpenVPN \
        servers hosted by NordVPN. Quickly Connect to the least busy servers (using current \
        data from Nordvpn website) with lowest latency from you. Find Nordvpn servers in a given \
        country or city. Tunnels DNS traffic through the VPN which normally (when using OpenVPN \
        with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a thirdparty \
        DNS servers) and completely compromises Privacy!")
    parser.add_argument(
        '-v', '--version', action='version', version="openpyn " + __version__)
    parser.add_argument(
        '-s', '--server', help='server name, i.e. ca64 or au10',)
    parser.add_argument(
        '-u', '--udp', help='use port UDP-1194 instead of the default TCP-443',
        action='store_true')
    parser.add_argument(
        '-c', '--country-code', type=str, help='Specify Country Code with 2 letters, i.e au,')
    # use nargs='?' to make a positional arg optinal
    parser.add_argument(
        'country', nargs='?', help='Country Code can also be specified without "-c,"\
         i.e "openpyn au"')
    parser.add_argument(
        '-a', '--area', type=str, help='Specify area, city name or state e.g \
        "openpyn au -a victoria" or "openpyn au -a \'sydney\'"')
    parser.add_argument(
        '-d', '--daemon', help='Run script in the background as openvpn daemon',
        action='store_true')
    parser.add_argument(
        '-m', '--max-load', type=int, default=70, help='Specify load threashold, \
        rejects servers with more load than this, DEFAULT=70')
    parser.add_argument(
        '-t', '--top-servers', type=int, default=6, help='Specify the number of Top \
         Servers to choose from the NordVPN\'s Sever list for the given Country, These will be \
         Pinged. DEFAULT=6')
    parser.add_argument(
        '-p', '--pings', type=str, default="5", help='Specify number of pings \
        to be sent to each server to determine quality, DEFAULT=5')
    parser.add_argument(
        '-T', '--toppest-servers', type=int, default=3, help='After ping tests \
        the final server count to randomly choose a server from, DEFAULT=3')
    parser.add_argument(
        '-k', '--kill', help='Kill any running Openvnp process, very useful \
        to kill openpyn process running in background with "-d" switch',
        action='store_true')
    parser.add_argument(
        '-x', '--kill-flush', help='Kill any running Openvnp process, AND Flush Iptables',
        action='store_true')
    parser.add_argument(
        '--update', help='Fetch the latest config files from nord\'s site',
        action='store_true')
    parser.add_argument(
        '-f', '--force-fw-rules', help='Enforce Firewall rules to drop traffic when tunnel breaks\
        , Force disable DNS traffic going to any other interface', action='store_true')
    parser.add_argument(
        '-l', '--list', dest="list_servers", type=str, nargs='?', default="nope",
        help='If no argument given prints all Country Names and Country Codes; \
        If country code supplied ("-l us"): Displays all servers in that given\
        country with their current load and openvpn support status. Works in \
        conjunction with (-a | --area, and server types (--p2p, --tor) \
        e.g "openpyn -l it --p2p --area milano"')
    parser.add_argument(
        '--p2p', help='Only look for servers with "Peer To Peer" support', action='store_true')
    parser.add_argument(
        '--dedicated', help='Only look for servers with "Dedicated IP" support',
        action='store_true')
    parser.add_argument(
        '--tor', dest='tor_over_vpn', help='Only look for servers with "Tor Over VPN" support',
        action='store_true')
    parser.add_argument(
        '--double', dest='double_vpn', help='Only look for servers with "Double VPN" support',
        action='store_true')
    parser.add_argument(
        '--anti-ddos', dest='anti_ddos', help='Only look for servers with "Anti DDos" support',
        action='store_true')
    parser.add_argument(
        '--test', help='Simulation only, do not actually connect to the vpn server',
        action='store_true')

    args = parser.parse_args()

    run(
        args.server, args.country_code, args.country, args.area, args.udp, args.daemon,
        args.max_load, args.top_servers, args.pings, args.toppest_servers,
        args.kill, args.kill_flush, args.update, args.list_servers,
        args.force_fw_rules, args.p2p, args.dedicated, args.double_vpn,
        args.tor_over_vpn, args.anti_ddos, args.test)


def run(
    # run openpyn
    server, country_code, country, area, udp, daemon, max_load, top_servers,
        pings, toppest_servers, kill, kill_flush, update, list_servers,
        force_fw_rules, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos, test):

    port = "tcp443"
    if udp:
        port = "udp1194"

    if kill:
        kill_vpn_processes()  # dont touch iptable rules
        sys.exit()
    elif kill_flush:
        kill_vpn_processes()
        firewall.clear_fw_rules()      # also clear iptable rules
        sys.exit()
    elif update:
        update_config_files()
        sys.exit()

    # a hack to list all countries and thier codes when no arg supplied with "-l"
    elif list_servers != 'nope':      # means "-l" supplied
        if list_servers is None:      # no arg given with "-l"
            if p2p or dedicated or double_vpn or tor_over_vpn or anti_ddos:
                # show the special servers in all countries
                display_servers(
                    list_servers="all", area=area, p2p=p2p, dedicated=dedicated,
                    double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos)
            else:
                list_all_countries()
        # if a country code is supplied give details about that country only.
        else:
            # if full name of the country supplied get country_code
            if len(list_servers) > 2:
                list_servers = get_country_code(full_name=list_servers)
            display_servers(
                list_servers=list_servers, area=area, p2p=p2p, dedicated=dedicated,
                double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos)

    # only clear/touch FW Rules if "-f" used
    elif force_fw_rules:
        firewall.clear_fw_rules()

    # check if openvpn config files exist if not download them.
    check_config_files()

    # if only positional argument used
    if country_code is None and server is None:
        country_code = country      # consider the positional arg e.g "us" same as "-c us"
    # if either "-c" or positional arg f.e "au" is present
    if country_code:
        # ask for and store credentials if not present, skip if "--test"
        if not test:
            if credentials.check_credentials() is False:
                credentials.save_credentials()

        if len(country_code) > 2:   # full country name
            # get the country_code from the full name
            country_code = get_country_code(full_name=country_code)
        country_code = country_code.lower()
        better_servers_list = find_better_servers(
                                country_code, area, max_load, top_servers, udp, p2p,
                                dedicated, double_vpn, tor_over_vpn, anti_ddos)
        pinged_servers_list = ping_servers(better_servers_list, pings)
        filtered_by_toppest = filters.filter_by_toppest(pinged_servers_list, toppest_servers)
        chosen_server = choose_best_server(filtered_by_toppest)
        # if "-f" used appy Firewall rules
        if force_fw_rules:
            network_interfaces = get_network_interfaces()
            vpn_server_ip = get_vpn_server_ip(chosen_server, port)
            firewall.apply_fw_rules(network_interfaces, vpn_server_ip)
        connection = connect(chosen_server, port, daemon, test)
    elif server:
        # ask for and store credentials if not present, skip if "--test"
        if not test:
            if credentials.check_credentials() is False:
                credentials.save_credentials()

        server = server.lower()
        # if "-f" used appy Firewall rules
        if force_fw_rules:
            network_interfaces = get_network_interfaces()
            vpn_server_ip = get_vpn_server_ip(server, port)
            firewall.apply_fw_rules(network_interfaces, vpn_server_ip)
        connection = connect(server, port, daemon, test)
    else:
        print('To see usage options type: "openpyn -h" or "openpyn --help"')


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
        country_code, area, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos):

    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)

    type_filtered_servers = filters.filter_by_type(
        json_response, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos)
    if country_code != "all":       # if "-l" had country code with it. e.g "-l au"
        type_country_filtered = filters.filter_by_country(country_code, type_filtered_servers)
        if area is None:
            return type_country_filtered
        else:
            type_country_area_filtered = filters.filter_by_area(area, type_country_filtered)
            return type_country_area_filtered
    return type_filtered_servers


# Filters servers based on the speficied criteria.
def find_better_servers(
    country_code, area, max_load, top_servers, udp, p2p, dedicated,
        double_vpn, tor_over_vpn, anti_ddos):
    if udp:
        used_protocol = "OPENVPN-UDP"
    else:
        used_protocol = "OPENVPN-TCP"

    # use api.nordvpn.com
    json_res_list = get_data_from_api(
                    country_code=country_code, area=area, p2p=p2p, dedicated=dedicated,
                    double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos)

    server_list = filters.filter_by_protocol(json_res_list=json_res_list, udp=udp)

    better_servers_list = filters.filter_by_load(server_list, max_load, top_servers)

    print("According to NordVPN, Least Busy " + str(len(better_servers_list)) + " Servers, In",
          country_code.upper(), end=" ")
    if area:
        print("in Location", json_res_list[0]["location_names"], end=" ")

    print("With 'Load' less than", max_load,  "Which Support", used_protocol, end=" ")
    if p2p:
        print(", p2p = ", p2p, end=" ")
    if dedicated:
        print(", dedicated =", dedicated, end=" ")
    if double_vpn:
        print(", double_vpn =", double_vpn, end=" ")
    if tor_over_vpn:
        print(",tor_over_vpn =", tor_over_vpn, end=" ")
    if anti_ddos:
        print(",anti_ddos =", anti_ddos, end=" ")

    print("are :", better_servers_list)
    return better_servers_list


# Pings servers with the speficied no of "ping",
# returns a sorted list by Ping Avg and Median Deveation
def ping_servers(better_servers_list, pings):
    pinged_servers_list = []
    for i in better_servers_list:
        # ping_result to append 2  lists into it
        ping_result = []
        try:
            ping_proc = subprocess.Popen(
                ["ping", i[0] + ".nordvpn.com", "-i", ".2", "-c", pings],
                stdout=subprocess.PIPE)
            # pipe the output of ping to grep.
            ping_output = subprocess.check_output(
                ("grep", "min/avg/max/mdev"), stdin=ping_proc.stdout)

        except subprocess.CalledProcessError as e:
            print("Ping Failed to :", i[0], "Skipping it")
            continue
        ping_string = str(ping_output)
        ping_string = ping_string[ping_string.find("= ") + 2:]
        ping_string = ping_string[:ping_string.find(" ")]
        ping_list = ping_string.split("/")
        # change str values in ping_list to ints
        ping_list = list(map(float, ping_list))
        ping_list = list(map(int, ping_list))
        print("Pinging Server " + i[0] + " min/avg/max/mdev = ", ping_list)
        ping_result.append(i)
        ping_result.append(ping_list)
        print(ping_result)
        pinged_servers_list.append(ping_result)
    # sort by Ping Avg and Median Deveation
    pinged_servers_list = sorted(pinged_servers_list, key=lambda item: (item[1][1], item[1][3]))
    return pinged_servers_list


# Returns a final server (randomly) from only the best "toppest_servers" (e.g 3) no. of servers.
def choose_best_server(best_servers):
    best_servers_names = []

    # populate bestServerList
    for i in best_servers:
        best_servers_names.append(i[0][0])

    print("Top " + str(len(best_servers)) + " Servers with best Ping are:", best_servers_names)
    chosen_servers_list = best_servers[random.randrange(0, len(best_servers))]
    chosen_server = chosen_servers_list[0][0]  # the first value, "server name"
    print("Out of the Best Available Servers, Randomly Selected ", chosen_server,
          "with Ping of  min/avg/max/mdev = ", chosen_servers_list[1])
    return chosen_server


def kill_vpn_processes():
    try:
        print("Killing any running openvpn processes")
        openvpn_processes = subprocess.check_output(["pgrep", "openvpn"])
        # When it returns "0", proceed
        root.verify_root_access("Root access needed to kill openvpn process")
        subprocess.run(["sudo", "killall", "openvpn"])
    except subprocess.CalledProcessError as ce:
        # when Exception, the openvpn_processes issued non 0 result, "not found"
        print("No openvpn process found")
        return


def update_config_files():
    root.verify_root_access("Root access needed to write files in '/usr/share/openpyn/files'")
    try:
        subprocess.check_call(
            "sudo wget -N https://nordvpn.com/api/files/zip -P /usr/share/openpyn/".split())
        subprocess.check_call(
            "sudo unzip -u -o /usr/share/openpyn/zip -d /usr/share/openpyn/files/".split())
        subprocess.check_call("sudo rm /usr/share/openpyn/zip".split())
    except subprocess.CalledProcessError:
        print("Exception occured while wgetting zip")


# Lists information abouts servers under the given criteria.
def display_servers(list_servers, area, p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos):
    servers_on_web = set()      # servers shown on the website

    # if list_servers was not a specific country it would be "all"
    json_res_list = get_data_from_api(
                    country_code=list_servers, area=area, p2p=p2p, dedicated=dedicated,
                    double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos)
    # print(json_res_list)

    if area:
            print("The NordVPN Servers In", list_servers.upper(), "Area", area, "Are :")
    else:
        print("The NordVPN Servers In", list_servers.upper(), "Are :")

    # add server names to "servers_on_web" set
    for res in json_res_list:
        print("Server =", res["domain"][:res["domain"].find(".")], ", Load =", res["load"],
              ", Country =", res["country"], ", Features", res["categories"], '\n')
        servers_on_web.add(res["domain"][:res["domain"].find(".")])

    if not area:
        locations_in_country = locations.get_unique_locations(list_of_servers=json_res_list)
        print("The available Locations in country", list_servers.upper(), "are :")
        for location in locations_in_country:
            print(location[2])

    if list_servers != "all" and p2p is False and dedicated is False and double_vpn is False \
            and tor_over_vpn is False and anti_ddos is False and area is False:
            # else not applicable.
        print_latest_servers(server_set=servers_on_web)
    sys.exit()


def print_latest_servers(server_set):
    servers_in_files = set()      # servers from .openvpn files
    new_servers = set()   # new Servers, not published on website yet, or taken down

    serverFiles = subprocess.check_output(
        "ls /usr/share/openpyn/files" + list_servers + "*", shell=True)
    openvpn_files_str = str(serverFiles)
    openvpn_files_str = openvpn_files_str[2:-3]
    openvpn_files_list = openvpn_files_str.split("\\n")

    for server in openvpn_files_list:
        server_name = server[server.find("files/") + 6:server.find(".")]
        servers_in_files.add(server_name)

    for server in servers_in_files:
        if server not in servers_on_web:
            new_servers.add(server)
    if len(new_servers) > 0:
        print("The following server have not even been listed on the nord's site yet",
              "they usally are the fastest or Dead.\n")
        print(new_servers)
    return


def check_config_files():
    try:
        serverFiles = subprocess.check_output(
            "ls /usr/share/openpyn/files", shell=True, stderr=subprocess.DEVNULL)
        openvpn_files_str = str(serverFiles)
    except subprocess.CalledProcessError:
        subprocess.run("sudo mkdir -p /usr/share/openpyn/files".split())
        serverFiles = subprocess.check_output(
            "ls /usr/share/openpyn/files", shell=True, stderr=subprocess.DEVNULL)
        openvpn_files_str = str(serverFiles)

    if len(openvpn_files_str) < 4:  # 3 is of Empty str (b'')
        print("\nRunning openpyn for the first time? running 'openpyn --update' for you :) \n")
        time.sleep(3)
        # download the config files
        update_config_files()
    return


def list_all_countries():
    countries_mapping = {}
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["domain"][:2] not in countries_mapping:
            countries_mapping.update({res["domain"][:2]: res["country"]})
    for key in countries_mapping.keys():
        print("Full Name : " + countries_mapping[key] + "      Country Code : " + key + '\n')
    sys.exit()


def get_country_code(full_name):
    url = "https://api.nordvpn.com/server"
    json_response = get_json(url)
    for res in json_response:
        if res["country"].lower() == full_name.lower():
            code = res["domain"][:2].lower()
            return code
    return "Country Name Not Correct"


def get_network_interfaces():
    # find the network interfaces present on the system
    interfaces = []
    interfaces_details = []

    interfaces = subprocess.check_output("ls /sys/class/net", shell=True)
    interfaceString = str(interfaces)
    interfaceString = interfaceString[2:-3]
    interfaces = interfaceString.split('\\n')

    for interface in interfaces:
        interface_out = subprocess.check_output(["ip", "addr", "show", interface])
        interfaces_output = str(interface_out)
        ip_addr_out = interfaces_output[interfaces_output.find("inet") + 5:]
        ip_addr = ip_addr_out[:ip_addr_out.find(" ")]

        interfaces_output = interfaces_output[5:interfaces_output.find(">")+1]
        interfaces_output = interfaces_output.replace(":", "").replace("<", "").replace(">", "")

        interface_output_list = interfaces_output.split(" ")
        if ip_addr != "":
            interface_output_list.append(ip_addr)
        interfaces_details.append(interface_output_list)
    return interfaces_details


def get_vpn_server_ip(server, port):
    # grab the ip address of vpnserver from the config file
    file_path = "/usr/share/openpyn/files/" + server + ".nordvpn.com." + port + ".ovpn"
    with open(file_path, 'r') as openvpn_file:
        for line in openvpn_file:
            if "remote " in line:
                vpn_server_ip = line[7:]
                vpn_server_ip = vpn_server_ip[:vpn_server_ip.find(" ")]
        openvpn_file.close()
        return vpn_server_ip


def connect(server, port, daemon, test):
    if test:
        print("Simulation end reached, openpyn would have connected to Server:",
              server, "on port:", port, " with 'daemon' mode:", daemon)
        sys.exit(1)

    kill_vpn_processes()   # kill existing openvpn processes
    print("CONNECTING TO SERVER", server, " ON PORT", port)

    is_root = root.verify_root_access("Root access required to run 'openvpn'")
    if daemon is True and is_root is False:
        root.obtain_root_access()

    resolvconf_exists = os.path.isfile("/sbin/resolvconf")
    # resolvconf_exists = False
    detected_os = platform.linux_distribution()[0]

    if resolvconf_exists:  # Debian Based OS
        # tunnel dns throught vpn by changing /etc/resolv.conf using
        # "update-resolv-conf.sh" to change the dns servers to NordVPN's.
        if daemon:
            subprocess.Popen(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass",
                    "/usr/share/openpyn/credentials", "--script-security", "2",
                    "--up", "/usr/share/openpyn/update-resolv-conf.sh",
                    "--down", "/usr/share/openpyn/update-resolv-conf.sh", "--daemon"])
            print("Started 'openvpn' in --daemon mode")
        else:
            try:
                print("Your OS '" + detected_os + "' Does have '/sbin/resolvconf'",
                      "using it to update DNS Resolver Entries")
                subprocess.run(
                    "sudo openvpn --redirect-gateway --config" + " /usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn --auth-user-pass \
                    /usr/share/openpyn/credentials --script-security 2 --up \
                    /usr/share/openpyn/update-resolv-conf.sh --down \
                    /usr/share/openpyn/update-resolv-conf.sh", shell=True)
            except (KeyboardInterrupt) as err:
                print('\nShutting down safely, please wait until process exits\n')

    else:       # If not Debian Based
        print("Your OS ", detected_os, "Does not have '/sbin/resolvconf': Manually Applying Patch" +
              " to Tunnel DNS Through The VPN Tunnel By Modifying '/etc/resolv.conf'")
        apply_dns_patch = subprocess.run(
            ["sudo", "/usr/share/openpyn/manual-dns-patch.sh"])

        if daemon:
            subprocess.Popen(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn",
                    "--auth-user-pass", "/usr/share/openpyn/credentials", "--daemon"])
            print("Started 'openvpn' in --daemon mode")
        else:
            try:
                subprocess.run(
                    "sudo openvpn --redirect-gateway --config" + " /usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn --auth-user-pass \
                    /usr/share/openpyn/credentials", shell=True)
            except (KeyboardInterrupt) as err:
                print('\nShutting down safely, please wait until process exits\n')


if __name__ == '__main__':
    main()
    sys.exit()
