#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess
import sys
import time

from colorama import Fore, Style
from openpyn import __basefilepath__  # pylint: disable=W0406
from openpyn import __version__  # pylint: disable=W0406
from openpyn import api  # pylint: disable=W0406
from openpyn import asus  # pylint: disable=W0406
from openpyn import credentials  # pylint: disable=W0406
from openpyn import filters  # pylint: disable=W0406
from openpyn import firewall  # pylint: disable=W0406
from openpyn import initd  # pylint: disable=W0406
from openpyn import locations  # pylint: disable=W0406
from openpyn import root  # pylint: disable=W0406
from openpyn import systemd  # pylint: disable=W0406


def main():
    parser = argparse.ArgumentParser(
        description="A python3 script/systemd service (GPLv3+) to easily connect to and switch \
        between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers \
        (using current data from NordVPN website) with lowest latency from you. Find NordVPN \
        servers in a given country or city. Tunnels DNS traffic through the VPN which normally \
        (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if \
        you use a third-party DNS servers) and completely compromises Privacy!")
    parser.add_argument(
        '-v', '--version', action='version', version="openpyn " + __version__)
    parser.add_argument(
        '--init', help='Initialise, store/change credentials, download/update VPN config files,\
        needs root "sudo" access.', action='store_true')
    parser.add_argument(
        '-s', '--server', help='server name, i.e. ca64 or au10')
    parser.add_argument(
        '--tcp', help='use port TCP-443 instead of the default UDP-1194',
        action='store_true')
    parser.add_argument(
        '-c', '--country-code', type=str, help='Specify country code with 2 letters, i.e. au')
    # use nargs='?' to make a positional arg optional
    parser.add_argument(
        'country', nargs='?', help='Country code can also be specified without "-c,"\
         i.e. "openpyn au"')
    parser.add_argument(
        '-a', '--area', type=str, help='Specify area, city name or state e.g \
        "openpyn au -a victoria" or "openpyn au -a \'sydney\'"')
    parser.add_argument(
        '-d', '--daemon', help='Update and start systemd service openpyn.service,\
        running it as a background process, to check status "systemctl status openpyn"',
        action='store_true')
    parser.add_argument(
        '-m', '--max-load', type=int, default=70, help='Specify load threshold, \
        rejects servers with more load than this, DEFAULT=70')
    parser.add_argument(
        '-t', '--top-servers', type=int, default=10, help='Specify the number of top \
         servers to choose from the NordVPN\'s server list for the given country, these will be \
         pinged, DEFAULT=10')
    parser.add_argument(
        '-p', '--pings', type=str, default="3", help='Specify number of pings \
        to be sent to each server to determine quality, DEFAULT=3')
    parser.add_argument(
        '-k', '--kill', help='Kill any running OpenVPN process, very useful \
        to kill openpyn process running in background with "-d" switch',
        action='store_true')
    parser.add_argument(
        '-x', '--kill-flush', help='Kill any running OpenVPN process, and flush iptables',
        action='store_true')
    parser.add_argument(
        '--update', help='Fetch the latest config files from NordVPN\'s site',
        action='store_true')
    parser.add_argument(
        '--skip-dns-patch', dest='skip_dns_patch', help='Skips DNS patching,\
        leaves /etc/resolv.conf untouched. (Not recommended)', action='store_true')
    parser.add_argument(
        '-f', '--force-fw-rules', help='Enforce firewall rules to drop traffic when tunnel breaks\
        , force disable DNS traffic going to any other interface', action='store_true')
    parser.add_argument(
        '--allow', dest='internally_allowed', help='To be used with "f" to allow ports \
        but ONLY to INTERNAL IP RANGE. for example: you can use your PC as SSH, HTTP server \
        for local devices (i.e. 192.168.1.* range) by "openpyn us --allow 22 80"', nargs='+')
    parser.add_argument(
        '-l', '--list', dest="list_servers", type=str, nargs='?', default="nope",
        help='If no argument given prints all Country Names and Country Codes; \
        If country code supplied ("-l us"): Displays all servers in that given\
        country with their current load and OpenVPN support status. Works in \
        conjunction with (-a | --area, and server types (--p2p, --tor) \
        e.g "openpyn -l it --p2p --area milano"')
    parser.add_argument(
        '--silent', help='Do not try to send notifications. Use if "libnotify" or "gi"\
        are not available. Automatically used in systemd service file', action='store_true')
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
        '--anti-ddos', dest='anti_ddos', help='Only look for servers with "Anti DDoS" support',
        action='store_true')
    parser.add_argument(
        '--netflix', dest='netflix', help='Only look for servers that are optimised for "Netflix"',
        action='store_true')
    parser.add_argument(
        '--test', help='Simulation only, do not actually connect to the VPN server',
        action='store_true')
    parser.add_argument(
        '-n', '--nvram', type=str, help='Specify client to save configuration to \
        NVRAM (ASUSWRT-Merlin)')
    parser.add_argument(
        '-o', '--openvpn-options', dest='openvpn_options', type=str, help='Pass through OpenVPN \
        options, e.g. openpyn uk -o \'--status /var/log/status.log --log /var/log/log.log\'')

    args = parser.parse_args()

    run(
        args.init, args.server, args.country_code, args.country, args.area, args.tcp,
        args.daemon, args.max_load, args.top_servers, args.pings,
        args.kill, args.kill_flush, args.update, args.list_servers,
        args.force_fw_rules, args.p2p, args.dedicated, args.double_vpn,
        args.tor_over_vpn, args.anti_ddos, args.netflix, args.test, args.internally_allowed,
        args.skip_dns_patch, args.silent, args.nvram, args.openvpn_options)


# run openpyn
def run(init, server, country_code, country, area, tcp, daemon, max_load, top_servers,
        pings, kill, kill_flush, update, list_servers, force_fw_rules,
        p2p, dedicated, double_vpn, tor_over_vpn, anti_ddos, netflix, test,
        internally_allowed, skip_dns_patch, silent, nvram, openvpn_options):
    port = "udp"
    if tcp:
        port = "tcp"

    detected_os = sys.platform
    if detected_os == "linux":
        if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
            silent = True
            skip_dns_patch = True
        elif os.path.exists("/etc/openwrt_release"):
            silent = True
            skip_dns_patch = True
            nvram = None
        else:
            nvram = None
    elif detected_os == "win32":
        print(Fore.BLUE + "Are you even a l33t mate? Try GNU/Linux")
        print(Style.RESET_ALL)
        sys.exit()

    # check if dependencies are installed
    if shutil.which("openvpn") is None or shutil.which("wget") is None or shutil.which("unzip") is None:
        print(Fore.RED + "Please Install 'openvpn' 'wget' 'unzip' first")
        print(Style.RESET_ALL)
        sys.exit()

    if init:
        initialise()
    elif daemon:
        if detected_os != "linux":
            print(Fore.RED + "Daemon mode is only available in GNU/Linux distros")
            print(Style.RESET_ALL)
            sys.exit()

        if not root.verify_running_as_root():
            print(Fore.RED + "Please run '--daemon' or '-d' mode with sudo")
            print(Style.RESET_ALL)
            sys.exit()
        openpyn_options = ""

        # if only positional argument used
        if country_code is None and server is None:
            country_code = country      # consider the positional arg e.g "us" same as "-c us"
        # if either "-c" or positional arg f.e "au" is present

        if country_code:
            if len(country_code) > 2:   # full country name
                # get the country_code from the full name
                country_code = api.get_country_code(full_name=country_code)
            country_code = country_code.lower()
            openpyn_options += country_code

        elif server:
            openpyn_options += " --server " + server

        if area:
            openpyn_options += " --area " + area
        if tcp:
            openpyn_options += " --tcp"
        if max_load:
            openpyn_options += " --max-load " + str(max_load)
        if top_servers:
            openpyn_options += " --top-servers " + str(top_servers)
        if pings:
            openpyn_options += " --pings " + str(pings)
        if force_fw_rules:
            openpyn_options += " --force-fw-rules"
        if p2p:
            openpyn_options += " --p2p"
        if dedicated:
            openpyn_options += " --dedicated"
        if double_vpn:
            openpyn_options += " --double"
        if tor_over_vpn:
            openpyn_options += " --tor"
        if anti_ddos:
            openpyn_options += " --anti-ddos"
        if netflix:
            openpyn_options += " --netflix"
        if test:
            openpyn_options += " --test"
        if internally_allowed:
            open_ports = ""
            for port_number in internally_allowed:
                open_ports += " " + port_number
            openpyn_options += " --allow" + open_ports
        if skip_dns_patch:
            openpyn_options += " --skip-dns-patch"
        if nvram:
            openpyn_options += " --nvram " + str(nvram)
        if openvpn_options:
            openpyn_options += " --openvpn-options '" + openvpn_options + "'"
        openpyn_options += " --silent"
        # print(openpyn_options)
        if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
            initd.update_service(openpyn_options, run=True)
        elif os.path.exists("/etc/openwrt_release"):
            initd.update_service(openpyn_options, run=True)
        else:
            systemd.update_service(openpyn_options, run=True)
        sys.exit()

    elif kill:
        kill_management_client()
        kill_vpn_processes()  # don't touch iptable rules
        kill_openpyn_process()
        sys.exit()
    elif kill_flush:
        firewall.clear_fw_rules()      # also clear iptable rules
        # if --allow present, allow those ports internally
        if internally_allowed:
            network_interfaces = get_network_interfaces()
            firewall.internally_allow_ports(network_interfaces, internally_allowed)
        kill_management_client()
        kill_vpn_processes()
        kill_openpyn_process()
        sys.exit()
    elif update:
        update_config_files()
        sys.exit()

    # a hack to list all countries and their codes when no arg supplied with "-l"
    elif list_servers != 'nope':      # means "-l" supplied
        if list_servers is None:      # no arg given with "-l"
            if p2p or dedicated or double_vpn or tor_over_vpn or anti_ddos or netflix:
                # show the special servers in all countries
                display_servers(
                    list_servers="all", port=port, area=area, p2p=p2p, dedicated=dedicated,
                    double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
                    netflix=netflix)
            else:
                api.list_all_countries()
        # if a country code is supplied give details about that country only.
        else:
            # if full name of the country supplied get country_code
            if len(list_servers) > 2:
                list_servers = api.get_country_code(full_name=list_servers)
            display_servers(
                list_servers=list_servers, port=port, area=area, p2p=p2p, dedicated=dedicated,
                double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
                netflix=netflix)

    # only clear/touch FW Rules if "-f" used
    elif force_fw_rules:
        firewall.clear_fw_rules()

    # check if OpenVPN config files exist if not download them.
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
            country_code = api.get_country_code(full_name=country_code)
        country_code = country_code.lower()

        # keep trying to connect to new servers
        for tries in range(3):  # pylint: disable=W0612
            better_servers_list = find_better_servers(
                country_code, area, max_load, top_servers, tcp, p2p,
                dedicated, double_vpn, tor_over_vpn, anti_ddos, netflix)
            pinged_servers_list = ping_servers(better_servers_list, pings)
            chosen_servers = choose_best_servers(pinged_servers_list)
            # connect to chosen_servers, if one fails go to next
            for aserver in chosen_servers:
                # if "-f" used apply firewall rules
                if force_fw_rules:
                    network_interfaces = get_network_interfaces()
                    vpn_server_ip = get_vpn_server_ip(aserver, port)
                    firewall.apply_fw_rules(network_interfaces, vpn_server_ip, skip_dns_patch)
                    if internally_allowed:
                        firewall.internally_allow_ports(network_interfaces, internally_allowed)
                if nvram:
                    asus.run(aserver, country_code, nvram, "All", "adaptive", "Strict", tcp, test)
                    sys.exit()
                print(Style.BRIGHT + Fore.BLUE + "Out of the Best Available Servers, Chose",
                      (Fore.GREEN + aserver + Fore.BLUE))
                connect(aserver, port, silent, test, skip_dns_patch, openvpn_options)
    elif server:
        # ask for and store credentials if not present, skip if "--test"
        if not test:
            if credentials.check_credentials() is False:
                credentials.save_credentials()

        server = server.lower()
        # if "-f" used apply firewall rules
        if force_fw_rules:
            network_interfaces = get_network_interfaces()
            vpn_server_ip = get_vpn_server_ip(server, port)
            firewall.apply_fw_rules(network_interfaces, vpn_server_ip, skip_dns_patch)
            if internally_allowed:
                firewall.internally_allow_ports(network_interfaces, internally_allowed)
        if nvram:
            asus.run(server, country_code, nvram, "All", "adaptive", "Strict", tcp, test)
            sys.exit()
        for i in range(20):  # pylint: disable=W0612
            connect(server, port, silent, test, skip_dns_patch, openvpn_options)
    else:
        print('To see usage options type: "openpyn -h" or "openpyn --help"')
    sys.exit()


def initialise():
    credentials.save_credentials()
    update_config_files()
    if sys.platform == "linux":
        if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
            initd.install_service()
        elif os.path.exists("/etc/openwrt_release"):
            initd.install_service()
        else:
            systemd.install_service()
    return


# Filters servers based on the specified criteria.
def find_better_servers(country_code, area, max_load, top_servers, tcp, p2p, dedicated,
                        double_vpn, tor_over_vpn, anti_ddos, netflix):
    if tcp:
        used_protocol = "OPENVPN-TCP"
    else:
        used_protocol = "OPENVPN-UDP"

    # use api.nordvpn.com
    json_res_list = api.get_data_from_api(
        country_code=country_code, area=area, p2p=p2p, dedicated=dedicated,
        double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
        netflix=netflix)

    server_list = filters.filter_by_protocol(json_res_list=json_res_list, tcp=tcp)

    better_servers_list = filters.filter_by_load(server_list, max_load, top_servers)

    print(Style.BRIGHT + Fore.BLUE + "According to NordVPN, Least Busy " +
          Fore.GREEN + str(len(better_servers_list)) + Fore.BLUE + " Servers, In",
          Fore.GREEN + country_code.upper() + Fore.BLUE, end=" ")
    if area:
        print("in Location" + Fore.GREEN, json_res_list[0]["location_names"], end=" ")

    print(Fore.BLUE + "With 'Load' less than", Fore.GREEN + str(max_load) + Fore.BLUE,
          "Which Support", Fore.GREEN + used_protocol, end=" ")
    if p2p:
        print(", p2p = ", p2p, end=" ")
    if dedicated:
        print(", dedicated =", dedicated, end=" ")
    if double_vpn:
        print(", double_vpn =", double_vpn, end=" ")
    if tor_over_vpn:
        print(", tor_over_vpn =", tor_over_vpn, end=" ")
    if anti_ddos:
        print(", anti_ddos =", anti_ddos, end=" ")
    if netflix:
        print(", netflix =", netflix, end=" ")

    print(Fore.BLUE + "are :" + Fore.GREEN, better_servers_list, Fore.BLUE + "\n")
    return better_servers_list


# Pings servers with the specified no of "ping",
# returns a sorted list by Ping Avg and Median Deviation
def ping_servers(better_servers_list, pings):
    pinged_servers_list = []
    ping_supports_option_i = True       # older ping command doesn't support "-i"

    try:
        subprocess.check_output(["ping", "-n", "-i", ".2", "-c", "2", "8.8.8.8"],
                                stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # when Exception, the processes issued error, "option is not supported"
        ping_supports_option_i = False
        print("Your 'ping' command doesn't support '-i' or '-n', \
falling back to wait of 1 second between pings, pings will be slow\n")
    for i in better_servers_list:
        # ping_result to append 2  lists into it
        ping_result = []
        try:
            if ping_supports_option_i:
                ping_proc = subprocess.Popen(
                    ["ping", "-n", "-i", ".2", "-c", pings, i[0] + ".nordvpn.com"],
                    stdout=subprocess.PIPE)
            else:
                ping_proc = subprocess.Popen(
                    ["ping", "-c", pings, i[0] + ".nordvpn.com"],
                    stdout=subprocess.PIPE)
            # pipe the output of ping to grep.
            ping_output = subprocess.check_output(
                ["grep", "-B", "1", "min/avg/max/"], stdin=ping_proc.stdout)

            ping_string = str(ping_output)
            # print(ping_string)
            if "0%" not in ping_string:
                print(Style.BRIGHT + Fore.RED + "Some packet loss while pinging",
                      i[0], "Skipping it\n" + Fore.BLUE)
                continue
        except subprocess.CalledProcessError:
            print(Style.BRIGHT + Fore.RED + "Ping Failed to:",
                  i[0], "Excluding it from the list\n" + Fore.BLUE)
            print(Style.RESET_ALL)
            continue
        except KeyboardInterrupt:
            print(Style.BRIGHT + Fore.RED + '\nKeyboardInterrupt; Shutting down\n')
            print(Style.RESET_ALL)
            sys.exit()
        ping_string = ping_string[ping_string.find("= ") + 2:]
        ping_string = ping_string[:ping_string.find(" ")]
        ping_list = ping_string.split("/")
        # change str values in ping_list to ints
        ping_list = list(map(float, ping_list))
        ping_list = list(map(int, ping_list))
        print(Style.BRIGHT + Fore.BLUE + "Pinging Server " + i[0] + " min/avg/max/mdev = ",
              Fore.GREEN + str(ping_list), Fore.BLUE + "\n")
        ping_result.append(i)
        ping_result.append(ping_list)
        # print(ping_result)
        pinged_servers_list.append(ping_result)
    # sort by Ping Avg and Median Deviation
    pinged_servers_list = sorted(pinged_servers_list, key=lambda item: (item[1][1], item[1][3]))
    return pinged_servers_list


# Returns a list of servers (top servers) (e.g 5 best servers) to connect to.
def choose_best_servers(best_servers):
    best_servers_names = []

    # populate bestServerList
    for i in best_servers:
        best_servers_names.append(i[0][0])

    print("Top " + Fore.GREEN + str(len(best_servers)) + Fore.BLUE + " Servers with best Ping are:",
          Fore.GREEN + str(best_servers_names) + Fore.BLUE + "\n")
    print(Style.RESET_ALL)
    return best_servers_names


def kill_vpn_processes():
    try:
        subprocess.check_output(["pgrep", "openvpn"])
        # When it returns "0", proceed
        root.verify_root_access("Root access needed to kill openvpn process")
        subprocess.call(["sudo", "killall", "openvpn"])
        print("Killed the running openvpn process")
        time.sleep(1)
    except subprocess.CalledProcessError:
        # when Exception, the openvpn_processes issued non 0 result, "not found"
        pass
    return


def kill_openpyn_process():
    try:
        root.verify_root_access("Root access needed to kill openpyn process")
        subprocess.call(["sudo", "killall", "openpyn"])
    except subprocess.CalledProcessError:
        # when Exception, the openvpn_processes issued non 0 result, "not found"
        pass
    return


def kill_management_client():
    # kill the management client if it is for some reason still alive
    try:
        root.verify_root_access("Root access needed to kill 'openpyn-management' process")
        subprocess.check_output(["sudo", "killall", "openpyn-management"],
                                stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # when Exception, the openvpn_processes issued non 0 result, "not found"
        pass
    return


def update_config_files():
    root.verify_root_access("Root access needed to write files in " +
                            "'" + __basefilepath__ + "files/" + "'")
    try:
        subprocess.check_call(
            ["sudo", "wget", "https://downloads.nordcdn.com/configs/archives/servers/ovpn.zip", "-P", __basefilepath__])
    except subprocess.CalledProcessError:
        print(
            Fore.RED + "Exception occured while wgetting zip, is the internet working? \
is nordcdn.com blocked by your ISP or Country?, If so use Privoxy \
[https://github.com/jotyGill/openpyn-nordvpn/issues/109]" + Style.RESET_ALL)
        sys.exit()
    try:
        subprocess.check_call(
            ["sudo", "unzip", "-u", "-o", __basefilepath__ + "ovpn", "-d", __basefilepath__ + "files/"],
            stderr=subprocess.DEVNULL)
        subprocess.check_call(
            ["sudo", "rm", __basefilepath__ + "ovpn.zip"])
    except subprocess.CalledProcessError:
        try:
            subprocess.check_call(
                ["sudo", "rm", "-rf", __basefilepath__ + "files/ovpn_udp"])
            subprocess.check_call(
                ["sudo", "rm", "-rf", __basefilepath__ + "files/ovpn_tcp"])
            subprocess.check_call(
                ["sudo", "unzip", __basefilepath__ + "ovpn", "-d", __basefilepath__ + "files/"])
            subprocess.check_call(
                ["sudo", "rm", __basefilepath__ + "ovpn.zip"])
        except subprocess.CalledProcessError:
            print(Fore.RED + "Exception occured while unzipping ovpn.zip, is unzip installed?" +
                  Style.RESET_ALL)
            sys.exit()


# Lists information about servers under the given criteria.
def display_servers(list_servers, port, area, p2p, dedicated, double_vpn,
                    tor_over_vpn, anti_ddos, netflix):
    servers_on_web = set()      # servers shown on the website

    # if list_servers was not a specific country it would be "all"
    json_res_list = api.get_data_from_api(
        country_code=list_servers, area=area, p2p=p2p, dedicated=dedicated,
        double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
        netflix=netflix)
    # print(json_res_list)

    print(Fore.BLUE + "The NordVPN Servers In", Fore.GREEN +
          list_servers.upper() + Fore.BLUE, end=" ")
    if area:
        print("Area ", Fore.GREEN + area + Fore.BLUE, end=" ")
    if p2p:
        print("with " + Fore.GREEN + "p2p" + Fore.BLUE + " support", end=" ")
    if dedicated:
        print("with " + Fore.GREEN + "dedicated" + Fore.BLUE + " support", end=" ")
    if double_vpn:
        print("with " + Fore.GREEN + "double_vpn" + Fore.BLUE + " support", end=" ")
    if tor_over_vpn:
        print("with " + Fore.GREEN + "tor_over_vpn" + Fore.BLUE + " support", end=" ")
    if anti_ddos:
        print("with " + Fore.GREEN + "anti_ddos" + Fore.BLUE + " support", end=" ")
    if netflix:
        print("with " + Fore.GREEN + "netflix" + Fore.BLUE + " support", end=" ")
    print("Are:\n" + Style.RESET_ALL)

    # add server names to "servers_on_web" set
    for res in json_res_list:
        print("Server =", res["domain"][:res["domain"].find(".")], ", Load =", res["load"],
              ", Country =", res["country"], ", Features", res["categories"], '\n')
        servers_on_web.add(res["domain"][:res["domain"].find(".")])

    if not area:
        locations_in_country = locations.get_unique_locations(list_of_servers=json_res_list)
        print("\nThe available Locations in country", list_servers.upper(), "are :")
        for location in locations_in_country:
            print(location[2])

    if list_servers != "all" and not p2p and not dedicated and not double_vpn \
            and not tor_over_vpn and not anti_ddos and not netflix and not area:
            # else not applicable.
        print_latest_servers(list_servers=list_servers, port=port, server_set=servers_on_web)
    sys.exit()


def print_latest_servers(list_servers, port, server_set):
    if port == "tcp":
        folder = "ovpn_tcp/"
    else:
        folder = "ovpn_udp/"

    servers_in_files = set()      # servers from .ovpn files
    new_servers = set()   # new Servers, not published on website yet, or taken down
    try:
        serverFiles = subprocess.check_output(
            "ls " + __basefilepath__ + "files/" + folder + list_servers + "*", shell=True)
    except subprocess.CalledProcessError:
        print(Fore.RED + "The supplied Contry Code is likely wrong or you just don't have \
its config files (In which case run 'sudo openpyn --update')" + Style.RESET_ALL)
        sys.exit()
    openvpn_files_str = str(serverFiles)
    openvpn_files_str = openvpn_files_str[2:-3]
    openvpn_files_list = openvpn_files_str.split("\\n")

    for server in openvpn_files_list:
        server_name = server[server.find("files/" + folder) + 15:server.find(".")]
        servers_in_files.add(server_name)

    for server in servers_in_files:
        if server not in server_set:
            new_servers.add(server)
    if new_servers:
        print("The following server have not even been listed on the nord's site yet",
              "they usally are the fastest or Dead.\n")
        print(new_servers)
    return


def check_config_files():
    try:
        serverFiles = subprocess.check_output(
            "ls " + __basefilepath__ + "files", shell=True, stderr=subprocess.DEVNULL)
        openvpn_files_str = str(serverFiles)
    except subprocess.CalledProcessError:
        subprocess.call(["sudo", "mkdir", "-p", __basefilepath__ + "files"])
        serverFiles = subprocess.check_output(
            "ls " + __basefilepath__ + "files", shell=True, stderr=subprocess.DEVNULL)
        openvpn_files_str = str(serverFiles)

    if len(openvpn_files_str) < 4:  # 3 is of Empty str (b'')
        print(Fore.GREEN + "\nRunning openpyn for the first time? running \
'openpyn --update' for you :) \n")
        time.sleep(5)
        # download the config files
        update_config_files()
    return


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

        interfaces_output = interfaces_output[5:interfaces_output.find(">") + 1]
        interfaces_output = interfaces_output.replace(":", "").replace("<", "").replace(">", "")

        interface_output_list = interfaces_output.split(" ")
        if ip_addr != "":
            interface_output_list.append(ip_addr)
        interfaces_details.append(interface_output_list)
    return interfaces_details


def get_vpn_server_ip(server, port):
    # grab the ip address of vpnserver from the config file
    if port == "tcp":
        folder = "ovpn_tcp/"
    else:
        folder = "ovpn_udp/"

    vpn_config_file = __basefilepath__ + "files/" + folder + server + \
        ".nordvpn.com." + port + ".ovpn"
    with open(vpn_config_file, 'r') as openvpn_file:
        for line in openvpn_file:
            if "remote " in line:
                vpn_server_ip = line[7:]
                vpn_server_ip = vpn_server_ip[:vpn_server_ip.find(" ")]
        openvpn_file.close()
        return vpn_server_ip


def uses_systemd_resolved():
    # see https://www.freedesktop.org/software/systemd/man/systemd-resolved.service.html

    systemd_resolved_running = subprocess.call(
        ["systemctl",  "is-active", "systemd-resolved"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ) == 0

    if not systemd_resolved_running:
        return False

    # systemd-resolved is running, good
    # however it's not enough, /etc/resolv.conf might be misconfigured and point at wrong place
    # better safe than sorry!

    stub_systemd_resolver = "127.0.0.53"  # seems to be hardcoded in systemd
    dns_servers = []
    with open('/etc/resolv.conf', 'r') as f:
        import re
        ns_rgx = re.compile("nameserver (.*)")
        for line in f:
            m = ns_rgx.match(line)
            if m and len(m.groups()) > 0:
                dns_servers.append(m.group(1))
    resolv_conf_managed = dns_servers == [stub_systemd_resolver]

    if resolv_conf_managed:
        return True

    # otherwise, something must be broken.. why is systemd-resolved running yet resolv.conf still pointing somewhere else?
    raise RuntimeError(
        "Invalid configuration: systemd-resolved is running, but resolv.conf contains {}".format(dns_servers))


def connect(server, port, silent, test, skip_dns_patch, openvpn_options, server_provider="nordvpn"):
    detected_os = sys.platform
    if server_provider == "nordvpn":
        if port == "tcp":
            folder = "ovpn_tcp/"
        else:
            folder = "ovpn_udp/"

        vpn_config_file = __basefilepath__ + "files/" + folder + server +\
            ".nordvpn.com." + port + ".ovpn"
        # print("CONFIG FILE", vpn_config_file)
        if os.path.isfile(vpn_config_file) is False:
            print(Fore.RED + "VPN configuration file", vpn_config_file,
                  "doesn't exist, don't worry running 'openpyn --update' for you :)" + Fore.BLUE)
            time.sleep(6)
            update_config_files()
    elif server_provider == "ipvanish":
        vpn_config_file = __basefilepath__ + "files/" + "ipvanish/" + server
        # print("ipvanish")

    if test:
        print("Simulation end reached, openpyn would have connected to Server:" +
              Fore.GREEN, server, Fore.BLUE + "on port:" + Fore.GREEN, port,
              Fore.BLUE + "with 'silent' mode:" + Fore.GREEN, silent)
        print(Style.RESET_ALL)
        sys.exit(1)

    kill_vpn_processes()   # kill existing OpenVPN processes
    # kill_management_client()
    print(Fore.BLUE + "CONNECTING TO SERVER" + Fore.GREEN, server,
          Fore.BLUE + "ON PORT", Fore.GREEN + port + Fore.BLUE)

    root_access = root.verify_root_access(
        Fore.GREEN + "Sudo credentials required to run 'openvpn'" + Fore.BLUE)
    if root_access is False:
        root.obtain_root_access()

    if not silent:
        # notifications Don't work with 'sudo'
        if detected_os == "linux" and root.running_with_sudo():
            print(Fore.RED + "Desktop notifications don't work when using 'sudo', run without it, "
                  + "when asked, provide the sudo credentials" + Fore.BLUE)
        else:
            subprocess.Popen("openpyn-management".split())
    print(Style.RESET_ALL)
    if detected_os == "linux":
        use_systemd_resolved = uses_systemd_resolved()
        use_resolvconf = os.path.isfile("/sbin/resolvconf")
    else:
        use_systemd_resolved = False
        use_resolvconf = False
        skip_dns_patch = True
    if not openvpn_options:
        openvpn_options = ""
    if (use_systemd_resolved or use_resolvconf) and skip_dns_patch is False:  # Debian Based OS + do DNS patching
        try:
            if use_systemd_resolved:
                up_down_script = __basefilepath__ + "scripts/update-systemd-resolved.sh"
                print("Your OS' " + Fore.GREEN + detected_os + Fore.BLUE +
                      "' has systemd-resolve running ",
                      "using it to update DNS Resolver Entries" + Style.RESET_ALL)
            elif use_resolvconf:
                # tunnel dns throught vpn by changing /etc/resolv.conf using
                # "update-resolv-conf.sh" to change the dns servers to NordVPN's.

                up_down_script = __basefilepath__ + "scripts/update-resolv-conf.sh"
                print("Your OS' " + Fore.GREEN + detected_os + Fore.BLUE +
                      "' Does have '/sbin/resolvconf'",
                      "using it to update DNS Resolver Entries" + Style.RESET_ALL)
            else:
                raise RuntimeError("Should not happen")

            def run_openvpn(*args):
                cmdline = [
                    "sudo", "openvpn",
                    "--redirect-gateway",
                    "--auth-retry", "nointeract",
                    "--config", vpn_config_file,
                    "--auth-user-pass", __basefilepath__ + "credentials",
                    "--script-security", "2",
                    "--up", up_down_script,
                    "--down", up_down_script,
                    "--down-pre",
                    *args,
                ] + openvpn_options.split()
                subprocess.run(cmdline, check=True)

            if silent:
                run_openvpn()
            else:
                run_openvpn(
                    "--management", "127.0.0.1", "7015",
                    "--management-up-down",
                )
        except subprocess.CalledProcessError as openvpn_err:
            # print(openvpn_err.output)
            if 'Error opening configuration file' in str(openvpn_err.output):
                print("Error opening configuration file", vpn_config_file,
                      "Make Sure it exists, run 'openpyn --update'")
                sys.exit()
        except KeyboardInterrupt:
            print('\nShutting down safely, please wait until process exits\n')
            sys.exit()
        except PermissionError:     # needed cause complains when killing sudo process
            sys.exit()

    else:       # If not Debian Based or skip_dns_patch
        # if skip_dns_patch, do not touch etc/resolv.conf
        if skip_dns_patch is False:
            print("Your OS", Fore.GREEN + detected_os + Fore.BLUE,
                  "Does not have" + Fore.GREEN + " '/sbin/resolvconf':\n" +
                  Fore.BLUE + "Manually Applying Patch to Tunnel DNS Through" +
                  "The VPN Tunnel By Modifying" + Fore.GREEN +
                  "' /etc/resolv.conf'")
            print(Style.RESET_ALL)
            subprocess.call(["sudo", __basefilepath__ + "scripts/manual-dns-patch.sh"])
        else:
            print(Fore.RED + "Not Modifying /etc/resolv.conf, DNS traffic",
                  "likely won't go through the encrypted tunnel")
            print(Style.RESET_ALL)
        try:   # pylint: disable=R1702
            if silent:
                if detected_os == "linux":
                    if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
                        # make sure module is loaded
                        if os.popen("test ! -c /dev/net/tun && echo 0 || echo 1").read()[0:-1] == '0':
                            subprocess.call("modprobe tun", shell=True)
                            if os.popen("test ! -c /dev/net/tun && echo 0 || echo 1").read()[0:-1] == '0':
                                print(Style.BRIGHT + Fore.RED +
                                      "Cannot open TUN/TAP dev /dev/net/tun: No such file or directory")
                                print(Style.RESET_ALL)
                                sys.exit(0)
                subprocess.run(
                    ["sudo", "openvpn", "--redirect-gateway", "--auth-retry",
                     "nointeract", "--config", vpn_config_file, "--auth-user-pass",
                     __basefilepath__ + "credentials"]
                    + openvpn_options.split(), check=True)
            else:
                subprocess.run(
                    ["sudo", "openvpn", "--redirect-gateway", "--auth-retry",
                     "nointeract", "--config", vpn_config_file, "--auth-user-pass",
                     __basefilepath__ + "credentials",
                     "--management", "127.0.0.1", "7015", "--management-up-down"]
                    + openvpn_options.split(), check=True)
        except subprocess.CalledProcessError as openvpn_err:
            # print(openvpn_err.output)
            if 'Error opening configuration file' in str(openvpn_err.output):
                print("Error opening configuration file", vpn_config_file,
                      "Make Sure it exists, run 'openpyn --update'")
                sys.exit()
        except KeyboardInterrupt:
            print('\nShutting down safely, please wait until process exits\n')
            sys.exit()
        except PermissionError:     # needed cause complains when killing sudo process
            sys.exit()


if __name__ == '__main__':
    main()
    sys.exit()
