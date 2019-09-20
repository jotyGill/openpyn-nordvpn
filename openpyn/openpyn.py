#!/usr/bin/env python3

import argparse
import io
import logging
import logging.handlers
import os
import shutil
import subprocess
import sys
import tempfile
import time
import json
import shlex
import zipfile
from email.utils import parsedate
from pathlib import Path
from typing import List, Set

import coloredlogs
import requests
import verboselogs
from colorama import Fore, Style
from tqdm import tqdm

from openpyn import api
from openpyn import asus
from openpyn import credentials
from openpyn import filters
from openpyn import firewall
from openpyn import initd
from openpyn import locations
from openpyn import root
from openpyn import systemd
from openpyn import __basefilepath__, __version__, log_folder, ovpn_folder, log_format    # variables

verboselogs.install()
logger = logging.getLogger(__package__)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="A python3 script/systemd service (GPLv3+) to easily connect to and switch \
        between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers \
        (using current data from NordVPN website) with lowest latency from you. Find NordVPN \
        servers in a given country or city. Tunnels DNS traffic through the VPN which normally \
        (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if \
        you use a third-party DNS servers) and completely compromises Privacy!", allow_abbrev=False)
    parser.add_argument(
        '-v', '--version', action='version', version="openpyn " + __version__)
    parser.add_argument(
        '--init', help='Initialise, store/change credentials, download/update VPN config files,\
        needs root "sudo" access.', action='store_true')
    parser.add_argument(
        '-s', '--server', type=str, help='server name, i.e. ca64 or au10')
    parser.add_argument(
        '--tcp', help='use port TCP-443 instead of the default UDP-1194', action='store_true')
    parser.add_argument(
        '-c', '--country-code', type=str, help='Specify country code with 2 letters, i.e. au')
    # use nargs='?' to make a positional arg optional
    parser.add_argument(
        'country', nargs='?', help='Country code can also be specified without "-c,"i.e. "openpyn au"')
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
        '-p', '--pings', type=str, default="5", help='Specify number of pings \
        to be sent to each server to determine quality, DEFAULT=5')
    parser.add_argument(
        '-k', '--kill', help='Kill any running OpenVPN process, very useful \
        to kill openpyn process running in background with "-d" switch', action='store_true')
    parser.add_argument(
        '-x', '--kill-flush', help='Kill any running OpenVPN process, and flush iptables', action='store_true')
    parser.add_argument(
        '--update', help='Fetch the latest config files from NordVPN\'s site', action='store_true')
    parser.add_argument(
        '--skip-dns-patch', dest='skip_dns_patch', help='Skips DNS patching,\
        leaves /etc/resolv.conf untouched. (Not recommended)', action='store_true')
    parser.add_argument(
        '-f', '--force-fw-rules', help='Enforce firewall rules to drop traffic when tunnel breaks\
        , force disable DNS traffic going to any other interface', action='store_true')
    parser.add_argument(
        '--allow', dest='internally_allowed', help='To be used with "f" to allow ports \
        but ONLY to INTERNAL IP RANGE. for example: you can use your PC as SSH, HTTP server \
        for local devices (i.e. 192.168.1.* range) by "openpyn us --allow 22 80"', nargs='+'),
    parser.add_argument(
        '--allow-config', dest='internally_allowed_config', help='To be used with "f" to allow a complex \
        a complex set of allow port rules. This option requires a path to a JSON file that contains the \
        relevent config'
    ),
    parser.add_argument(
        '--allow-config-json', dest='internally_allowed_config_json', help='To be used with "f" to allow a complex \
        a complex set of allow port rules. This option requires works the same as "--allow-config" option \
        but accepts a json object as a string instead'
    ),
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
        '--dedicated', help='Only look for servers with "Dedicated IP" support', action='store_true')
    parser.add_argument(
        '--tor', dest='tor_over_vpn', help='Only look for servers with "Tor Over VPN" support', action='store_true')
    parser.add_argument(
        '--double', dest='double_vpn', help='Only look for servers with "Double VPN" support', action='store_true')
    parser.add_argument(
        '--anti-ddos', dest='anti_ddos', help='Only look for servers with "Obfuscated" support', action='store_true')
    parser.add_argument(
        '--netflix', dest='netflix', help='Only look for servers that are optimised for "Netflix"', action='store_true')
    parser.add_argument(
        '--test', help='Simulation only, do not actually connect to the VPN server', action='store_true')
    parser.add_argument(
        '-n', '--nvram', type=str, help='Specify client to save configuration to NVRAM (ASUSWRT-Merlin)')
    parser.add_argument(
        '-o', '--openvpn-options', dest='openvpn_options', type=str, help='Pass through OpenVPN \
        options, e.g. openpyn uk -o \'--status /var/log/status.log --log /var/log/log.log\'')
    parser.add_argument(
        '-loc', '--location', nargs=2, type=float, metavar=('latitude', 'longitude'))
    parser.add_argument(
        '--status', dest='show_status', help='Show last change in connection status', action='store_true')
    parser.add_argument(
        '--stats', dest='show_stats', help='Show openvpn connection stats', action='store_true')
    return parser.parse_args(argv[1:])


def main() -> bool:
    args = parse_args(sys.argv)
    return_code = run(
        args.init, args.server, args.country_code, args.country, args.area, args.tcp,
        args.daemon, args.max_load, args.top_servers, args.pings,
        args.kill, args.kill_flush, args.update, args.list_servers,
        args.force_fw_rules, args.p2p, args.dedicated, args.double_vpn,
        args.tor_over_vpn, args.anti_ddos, args.netflix, args.test, args.internally_allowed,
        args.internally_allowed_config, args.internally_allowed_config_json, args.skip_dns_patch,
        args.silent, args.nvram, args.openvpn_options, args.location, args.show_status, args.show_stats)
    return return_code


# run openpyn
# pylint: disable=R0911
def run(init: bool, server: str, country_code: str, country: str, area: str, tcp: bool, daemon: bool,
        max_load: int, top_servers: int, pings: str, kill: bool, kill_flush: bool, update: bool, list_servers: bool,
        force_fw_rules: bool, p2p: bool, dedicated: bool, double_vpn: bool, tor_over_vpn: bool, anti_ddos: bool,
        netflix: bool, test: bool, internally_allowed: List, internally_allowed_config: str, internally_allowed_config_json: dict,
        skip_dns_patch: bool, silent: bool, nvram: str, openvpn_options: str, location: float, show_status: bool,
        show_stats: bool) -> bool:
    fieldstyles = {
        'asctime': {'color': 'green'},
        'hostname': {'color': 'magenta'},
        'levelname': {'color': 'black', 'bold': True},
        'name': {'color': 'blue'},
        'programname': {'color': 'cyan'},
    }
    levelstyles = {
        'spam': {'color': 'green', 'faint': True},
        'debug': {'color': 'green', 'bold': True},
        'verbose': {'color': 'blue', 'bold': True},
        'info': {},
        'notice': {'color': 'magenta', 'bold': True},
        'warning': {'color': 'yellow', 'bold': True},
        'success': {'color': 'green', 'bold': True},
        'error': {'color': 'red', 'bold': True},
        'critical': {'color': 'white', 'background': 'red', 'bold': True}
    }

    logger.addHandler(logging.StreamHandler())

    # in this case only log messages originating from this logger will show up on the terminal.
    coloredlogs.install(level="verbose", logger=logger, fmt=log_format, level_styles=levelstyles, field_styles=fieldstyles)

    stats = True
    # if non-interactive shell
    if not sys.__stdin__.isatty():
        # special handler and formatter for JuiceSSH plugin
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler_formatter = logging.Formatter("%(message)s:%(levelname)s")
        stdout_handler.setFormatter(stdout_handler_formatter)
        logger.addHandler(stdout_handler)
        stats = False

    # if only positional argument used
    if country_code is None and server is None:
        # consider the positional arg e.g "us" same as "-c us"
        country_code = country

    port = "tcp" if tcp else "udp"

    # Allways decode internally json config when passed
    if internally_allowed_config_json:
        try:
            internally_allowed_config_json = json.loads(internally_allowed_config_json)
        except json.JSONDecodeError as err:
            logger.error("Failed to decode JSON passed in '----allow-config-json' Error at line {line}:{col} {msg} ".format(lineno=err.lineno, col=err.colno, msg=err.msg))
            internally_allowed_config_json = None

    detected_os = sys.platform
    asuswrt_os = False
    openwrt_os = False
    if detected_os == "linux":
        if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
            asuswrt_os = True
            force_fw_rules = False
            internally_allowed = None
            silent = True
            # TODO test skip_dns_patch
            skip_dns_patch = True
            if openvpn_options:
                openvpn_options += " " + "--syslog openpyn"
            else:
                openvpn_options = "--syslog openpyn"
            # logger.debug(openvpn_options)
        elif os.path.exists("/etc/openwrt_release"):
            openwrt_os = True
            force_fw_rules = False
            internally_allowed = None
            silent = True
            # TODO test skip_dns_patch
            skip_dns_patch = True
            nvram = None
        else:
            nvram = None
    elif detected_os == "win32":
        logger.error("Are you even a l33t mate? Try GNU/Linux")
        return 1
    else:
        force_fw_rules = False
        internally_allowed = None
        skip_dns_patch = True
        nvram = None

    # check if dependencies are installed
    if shutil.which("openvpn") is None:
        logger.error("Please install 'openvpn' first")
        return 1

    if init:
        if not root.verify_running_as_root():
            logger.error("Option '--init' "
                "requires sudo access. run 'sudo openpyn --init' instead.")
            return 1
        try:
            initialise(detected_os, asuswrt_os, openwrt_os)
            return 0
        except RuntimeError as e:
            logger.critical(e)
            return 1

    # if log folder doesnt exist, exit, "--init" creates it
    if not os.path.exists(log_folder):
        raise RuntimeError("Please initialise first by running 'sudo openpyn --init'"
            ", then start using 'openpyn' without sudo")

    # Add another rotating handler to log to .log files
    # fix permissions if needed
    for attempt in range(2):
        try:
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_folder + '/openpyn.log', when='W0', interval=4)
            file_handler_formatter = logging.Formatter(log_format)
            file_handler.setFormatter(file_handler_formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            root.verify_root_access(
                "Root access needed to set permissions of {}/openpyn.log".format(log_folder))
            subprocess.run("sudo chmod 777 {}".format(log_folder).split())
            subprocess.run("sudo chmod 666 {}/openpyn.log".format(log_folder).split())
            subprocess.run("sudo chmod 666 {}/openpyn-notifications.log".format(log_folder).split())
        else:
            break

    if daemon:
        if detected_os != "linux":
            logger.error("Daemon mode is only available in GNU/Linux distros")
            return 1

        if not root.verify_running_as_root():
            logger.error("Please run '--daemon' or '-d' mode with sudo")
            return 1

        openpyn_options = ""

        # if either "-c" or positional arg f.e "au" is present
        if country_code:
            # if full name of the country supplied get country_code
            if len(country_code) > 2:
                try:
                    country_code = api.get_country_code(full_name=country_code)
                except RuntimeError as e:
                    logger.critical(e)
                    return 1

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
            openpyn_options += " --pings " + pings
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
        if internally_allowed_config_json or internally_allowed_config:
            # Override passed config is file is specified
            if internally_allowed_config:
                internally_allowed_config_json = firewall.load_allowed_ports(internally_allowed_config)
            if firewall.validate_allowed_ports_json(internally_allowed_config_json):
                openpyn_options += " --allow-config-json=" + shlex.quote(json.dumps(internally_allowed_config_json, separators=(',', ':')))
            logger.error(openpyn_options)
        if internally_allowed:
            open_ports = ""
            for port_number in internally_allowed:
                open_ports += " " + port_number
            openpyn_options += " --allow" + open_ports
        if skip_dns_patch:
            openpyn_options += " --skip-dns-patch"
        if nvram:
            openpyn_options += " --nvram " + nvram
        if openvpn_options:
            openpyn_options += " --openvpn-options '" + openvpn_options + "'"
        # logger.debug(openpyn_options)
        if asuswrt_os:
            initd.update_service(openpyn_options, run=True)
        elif openwrt_os:
            initd.update_service(openpyn_options, run=True)
        else:
            systemd.update_service(openpyn_options, run=True)

    elif kill:
        try:
            kill_all()
            # returns exit code 143
        except RuntimeError as e:
            logger.critical(e)
            return 1

    elif kill_flush:
        if detected_os == "linux":
            if asuswrt_os:
                pass
            elif openwrt_os:
                pass
            else:
                # also clear iptable rules
                firewall.clear_fw_rules()
                # if --allow present, allow those ports internally
                logger.notice("Re-enabling ipv6")
                firewall.manage_ipv6(disable=False)
                if internally_allowed:
                    network_interfaces = get_network_interfaces()
                    firewall.internally_allow_ports(network_interfaces, internally_allowed)
        try:
            kill_all()
            # returns exit code 143
        except RuntimeError as e:
            logger.critical(e)
            return 1

    elif update:
        try:
            update_config_files()
        except RuntimeError as e:
            logger.critical(e)
            return 1

    elif show_status:
        try:
            print_status()
        except RuntimeError as e:
            logger.critical(e)
            return 1

    elif show_stats:
        try:
            print_stats()
        except RuntimeError as e:
            logger.critical(e)
            return 1


    # a hack to list all countries and their codes when no arg supplied with "-l"
    elif list_servers != "nope":      # means "-l" supplied
        try:
            if list_servers is None:      # no arg given with "-l"
                if p2p or dedicated or double_vpn or tor_over_vpn or anti_ddos or netflix:
                    # show the special servers in all countries
                    display_servers(
                        list_servers="all", port=port, area=area, p2p=p2p, dedicated=dedicated,
                        double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
                        netflix=netflix, location=location)
                else:
                    api.list_all_countries()
            # if a country code is supplied give details about that country only.
            else:
                # if full name of the country supplied get country_code
                if len(list_servers) > 2:
                    list_servers = api.get_country_code(full_name=list_servers)

                list_servers = list_servers.lower()

                display_servers(
                    list_servers=list_servers, port=port, area=area, p2p=p2p, dedicated=dedicated,
                    double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
                    netflix=netflix, location=location)
        except RuntimeError as e:
            logger.critical(e)
            return 1

    # if either "-c" or positional arg f.e "au" is present
    elif country_code:
        try:
            if not test:
                # ask for and store credentials if not present, skip if "--test"
                if credentials.check_credentials() is False:
                    logger.error("Credentials not found: Please run 'sudo openpyn --init' first")

                # check if OpenVPN config files exist if not download them, skip if "--test"
                check_config_files()

            use_systemd_resolved = False
            use_resolvconf = False
            if detected_os == "linux":
                if asuswrt_os or openwrt_os:
                    if not nvram:
                        # make sure module is loaded
                        load_tun_module()
                else:
                    use_systemd_resolved = uses_systemd_resolved()
                    use_resolvconf = os.path.isfile("/sbin/resolvconf")

            # if full name of the country supplied get country_code
            if len(country_code) > 2:
                country_code = api.get_country_code(full_name=country_code)

            country_code = country_code.lower()

            # if '-f' supplied, clear_fw_rules first
            if force_fw_rules and not test:
                firewall.clear_fw_rules()

            better_servers_list = find_better_servers(
                country_code, area, max_load, top_servers, tcp, p2p,
                dedicated, double_vpn, tor_over_vpn, anti_ddos, netflix, location, stats)
            # if no servers under search criteria
            if not better_servers_list:
                logger.critical("There are no servers that satisfy your criteria, please broaden your search.")
                return 1
            pinged_servers_list = ping_servers(better_servers_list, pings, stats)
            chosen_servers = choose_best_servers(pinged_servers_list, stats)

            # only clear/touch FW Rules if "-f" used, skip if "--test"
            if force_fw_rules and not test:
                touch_iptables_rules(chosen_servers, port, skip_dns_patch, internally_allowed, internally_allowed_config, internally_allowed_config_json)

            # connect to chosen_servers, if one fails go to next
            for aserver in chosen_servers:
                if stats:
                    print(Style.BRIGHT + Fore.BLUE + "Out of the Best Available Servers, Chose",
                          (Fore.GREEN + aserver + Fore.BLUE) + "\n")

                if nvram:
                    check_config_files()
                    asus.run(aserver, nvram, "All", "adaptive", "Strict", tcp, test)
                    logger.success("SAVED SERVER " + aserver + " ON PORT " + port + " TO NVRAM " + nvram)
                    return 0

                if test:
                    logger.success(
                        "Simulation end reached, openpyn would have connected to server: "
                        + aserver
                        + " on port: "
                        + port
                        + " with 'silent' mode: "
                        + str(silent).lower()
                    )
                    continue

                connect(aserver, port, silent, skip_dns_patch, openvpn_options, use_systemd_resolved, use_resolvconf)
        except RuntimeError as e:
            logger.critical(e)
            return 1
        except SystemExit:
            logger.info("Shutting down safely, please wait until process exits")

    elif server:
        try:
            if not test:
                # ask to store credentials if not present, skip if "--test"
                if credentials.check_credentials() is False:
                    logger.error("Credentials not found: Please run 'sudo openpyn --init' first")

                # check if OpenVPN config files exist if not download them, skip if "--test"
                check_config_files()

            use_systemd_resolved = False
            use_resolvconf = False
            if detected_os == "linux":
                if asuswrt_os or openwrt_os:
                    if not nvram:
                        # make sure module is loaded
                        load_tun_module()
                else:
                    use_systemd_resolved = uses_systemd_resolved()
                    use_resolvconf = os.path.isfile("/sbin/resolvconf")

            server = server.lower()

            # only clear/touch FW Rules if "-f" used, skip if "--test"
            if force_fw_rules and not test:
                touch_iptables_rules([server], port, skip_dns_patch, internally_allowed, internally_allowed_config, internally_allowed_config_json)

            if nvram:
                check_config_files()
                asus.run(server, nvram, "All", "adaptive", "Strict", tcp, test)
                logger.success("SAVED SERVER " + server + " ON PORT " + port + " TO NVRAM " + nvram)
                return 0

            if test:
                logger.success(
                    "Simulation end reached, openpyn would have connected to server: "
                    + server
                    + " on port: "
                    + port
                    + " with 'silent' mode: "
                    + str(silent).lower()
                )
                return 0

            # keep trying to connect to same server
            for _ in range(3 * top_servers):
                connect(server, port, silent, skip_dns_patch, openvpn_options, use_systemd_resolved, use_resolvconf)
        except RuntimeError as e:
            logger.critical(e)
            return 1
        except SystemExit:
            logger.info("Shutting down safely, please wait until process exits")

    else:
        logger.info("To see usage options type: 'openpyn -h' or 'openpyn --help'")

    # if everything went ok
    return 0


def initialise(detected_os: str, asuswrt_os: bool, openwrt_os: bool) -> None:
    if os.path.exists(ovpn_folder):
        shutil.rmtree(ovpn_folder)
    os.mkdir(ovpn_folder)
    os.chmod(ovpn_folder, 0o777)

    os.makedirs(log_folder, exist_ok=True)
    os.chmod(log_folder, 0o777)

    update_config_files()
    credentials.save_credentials()
    if detected_os == "linux":
        if asuswrt_os:
            initd.install_service()
        elif openwrt_os:
            initd.install_service()
        elif os.path.exists("/sbin/init") and os.readlink("/sbin/init").rsplit("/", maxsplit=1)[-1] == "systemd":
            systemd.install_service()
        else:
            logger.warning("systemd not found, skipping systemd integration")


def print_status():
    try:
        ps = subprocess.check_output(["pgrep", "openpyn"],
            stderr=subprocess.DEVNULL).decode(sys.stdout.encoding).strip().split()
        if len(ps) > 1: # first is the current process
            # when it returns "0", proceed
            with open("{}/status".format(log_folder), "r") as status_file:
                print(status_file.readline().rstrip())
        else:
            raise RuntimeError("'openpyn' is not running")
    except subprocess.CalledProcessError:
        # when check_output issued non 0 result, "not found"
        raise RuntimeError("command 'pgrep' not found")
    except FileNotFoundError:
        raise RuntimeError("{}/status not found".format(log_folder))


def print_stats():
    try:
        ps = subprocess.check_output(["pgrep", "openpyn"],
            stderr=subprocess.DEVNULL).decode(sys.stdout.encoding).strip().split()
        if len(ps) > 1: # first is the current process
            # when it returns "0", proceed
            with open("{}/openvpn-status".format(log_folder), "r") as status_file:
                print(status_file.read())
        else:
            raise RuntimeError("'openpyn' is not running")
    except subprocess.CalledProcessError:
        # when check_output issued non 0 result, "not found"
        raise RuntimeError("command 'pgrep' not found")
    except FileNotFoundError:
        raise RuntimeError("{}/openvpn-status not found".format(log_folder))


def load_tun_module():
    if not Path("/dev/net/tun").is_char_device():
        subprocess.call("modprobe tun", shell=True)
        if not Path("/dev/net/tun").is_char_device():
            raise RuntimeError("Cannot open TUN/TAP dev /dev/net/tun: No such file or directory")


def touch_iptables_rules(chosen_servers: List, port: str, skip_dns_patch: bool, internally_allowed: List, internally_allowed_config: str, internally_allowed_config_json: dict):
    network_interfaces = get_network_interfaces()
    vpn_server_ips = []

    if (internally_allowed_config or internally_allowed_config_json) and internally_allowed:
        if internally_allowed_config:
            internally_allowed_config_json = firewall.load_allowed_ports(internally_allowed_config)

        if firewall.validate_allowed_ports_json(internally_allowed_config_json):
            firewall.apply_allowed_port_rules(network_interfaces ,internally_allowed_config_json)
    for server in chosen_servers:
        vpn_server_ips.append(get_vpn_server_ip(server, port))

    firewall.apply_fw_rules(network_interfaces, vpn_server_ips, skip_dns_patch)
    if internally_allowed:
        firewall.internally_allow_ports(network_interfaces, internally_allowed)



# Filters servers based on the specified criteria.
def find_better_servers(country_code: str, area: str, max_load: int, top_servers: int, tcp: bool,
                        p2p: bool, dedicated: bool, double_vpn: bool, tor_over_vpn: bool,
                        anti_ddos: bool, netflix: bool, location: float, stats: bool) -> List:
    if tcp:
        used_protocol = "OPENVPN-TCP"
    else:
        used_protocol = "OPENVPN-UDP"

    # use api.nordvpn.com
    json_res_list = api.get_data_from_api(
        country_code=country_code, area=area, p2p=p2p, dedicated=dedicated,
        double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
        netflix=netflix, location=location)

    server_list = filters.filter_by_protocol(json_res_list=json_res_list, tcp=tcp)

    better_servers_list = filters.filter_by_load(server_list, max_load, top_servers)

    if better_servers_list and stats:
        print(Style.BRIGHT + Fore.BLUE + "According to NordVPN, \
Least Busy " + Fore.GREEN + str(len(better_servers_list)) + Fore.BLUE + " Servers in \
" + Fore.GREEN + country_code.upper() + Fore.BLUE, end=" ")
        if area:
            print("in Location" + Fore.GREEN, json_res_list[0]["location_names"], end=" ")

        print(Fore.BLUE + "With 'Load' Less Than", Fore.GREEN + str(max_load) + Fore.BLUE,
              "Which Support", Fore.GREEN + used_protocol, end=" ")
        if p2p:
            print(", p2p =", p2p, end=" ")
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

        print(Fore.BLUE + "Are: " + Fore.GREEN + str(better_servers_list) + Fore.BLUE + "\n")
    return better_servers_list


# Pings servers with the specified no of "ping",
# Returns a sorted list by ping median average deviation
def ping_servers(better_servers_list: List, pings: str, stats: bool) -> List:
    pinged_servers_list = []
    ping_supports_option_i = True       # older ping command doesn't support "-i"

    try:
        subprocess.check_output(["ping", "-n", "-i", ".2", "-c", "2", "8.8.8.8"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # when Exception, the processes issued error, "option is not supported"
        ping_supports_option_i = False
        logger.warning("Your 'ping' command doesn't support '-i' or '-n', \
falling back to wait of 1 second between pings, pings will be slow")
    if ping_supports_option_i == True:
        ping_subprocess_command = ["ping", "-n", "-i", ".2", "-c", pings, "dns_placeholder"]
    else:
        ping_subprocess_command = ["ping", "-c", pings, "dns_placeholder"]

    ping_subprocess_list    = []

    if stats:
        print(Style.BRIGHT + Fore.BLUE + "Sending Pings To Servers\n")

    for server_spec in better_servers_list:
        ping_subprocess_command[-1] = server_spec[0] + ".nordvpn.com"

        try:
            ping_process = subprocess.Popen(ping_subprocess_command             , stdout=subprocess.PIPE)
            grep_process = subprocess.Popen(["grep", "-B", "1", "min/avg/max"]  , stdin =ping_process.stdout, stdout=subprocess.PIPE)

            ping_subprocess = [ server_spec, grep_process ]
            time.sleep(0.02)    # needs to spawn Popen process
            ping_subprocess_list.append(ping_subprocess)

        except subprocess.CalledProcessError:
            logger.warning("Ping Failed to: %s, excluding it from the list", server_spec[0])
            continue
        except KeyboardInterrupt:
            raise SystemExit

    for ping_subprocess in ping_subprocess_list:
        ping_subprocess.append(ping_subprocess[1].communicate())

        ping_output = ping_subprocess[2][0]

        # logger.info("openpyn: ping output for %s\n%s", ping_subprocess[0][0], ping_output)

        ping_string = str(ping_output)
        ping_result = []
        # logger.debug(ping_string)
        if "0%" not in ping_string:
            logger.warning("Some packet loss while pinging %s, skipping it", ping_subprocess[0][0])
        else:
            ping_string = ping_string[ping_string.find("= ") + 2:]
            ping_string = ping_string[:ping_string.find(" ")]
            ping_list = ping_string.split("/")
            # change str values in ping_list to ints
            ping_list = list(map(float, ping_list))
            ping_list = list(map(int, ping_list))

            if stats:
                print(Style.BRIGHT + Fore.BLUE + "Ping Resonse From " + ping_subprocess[0][0].ljust(7) +
                        " min/avg/max/mdev = " + Fore.GREEN + str(ping_list), Fore.BLUE + "")
            ping_result.append(ping_subprocess[0])
            ping_result.append(ping_list)
            # logger.debug(ping_result)
            pinged_servers_list.append(ping_result)
    # sort by ping median average deviation
    if len(pinged_servers_list[0][1]) >= 4:
        # sort by Ping Avg and Median Deviation
        pinged_servers_list = sorted(pinged_servers_list, key=lambda item: (item[1][1], item[1][3]))
    else:
        # sort by Ping Avg
        pinged_servers_list = sorted(pinged_servers_list, key=lambda item: item[1][1])
    return pinged_servers_list


# Returns a list of servers (top servers) (e.g 5 best servers) to connect to.
def choose_best_servers(best_servers: List, stats: bool) -> List:
    best_servers_names = []

    # populate bestServerList
    for i in best_servers:
        best_servers_names.append(i[0][0])

    if stats:
        print("\nTop " + Fore.GREEN + str(len(best_servers)) + Fore.BLUE + " Servers with Best Ping Are: "
                + Fore.GREEN + str(best_servers_names) + Fore.BLUE)
        print(Style.RESET_ALL)
    return best_servers_names


def kill_all() -> None:
    logger.notice("Killing the running processes")

    root_access = root.verify_root_access("Root access needed to kill 'openvpn', 'openpyn', 'openpyn-management' processes")
    if root_access is False:
        root.obtain_root_access()

    kill_management_client()
    kill_vpn_processes()

    kill_openpyn_process()


def kill_vpn_processes() -> None:
    try:
        subprocess.check_output(["pgrep", "openvpn"], stderr=subprocess.DEVNULL)
        # when it returns "0", proceed
        logger.notice("Killing the running openvpn process")
        subprocess.check_output(["sudo", "killall", "openvpn"], stderr=subprocess.DEVNULL)
        time.sleep(1)
    except subprocess.CalledProcessError:
        # when Exception, the openvpn_processes issued non 0 result, "not found"
        pass


def kill_openpyn_process() -> None:
    try:
        subprocess.check_output(["pgrep", "openpyn"], stderr=subprocess.DEVNULL)
        # when it returns "0", proceed
        logger.notice("Killing the running openpyn process")
        subprocess.check_output(["sudo", "killall", "openpyn"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # when Exception, the openpyn_processes issued non 0 result, "not found"
        pass


def kill_management_client() -> None:
    # kill the management client if it is for some reason still alive
    try:
        subprocess.check_output(["pgrep", "openpyn-management"], stderr=subprocess.DEVNULL)
        # when it returns "0", proceed
        logger.notice("Killing the running openvpn-management process")
        subprocess.check_output(["sudo", "killall", "openpyn-management"], stderr=subprocess.DEVNULL)
        time.sleep(3)
    except subprocess.CalledProcessError:
        # when Exception, the openpyn-management_processes issued non 0 result, "not found"
        pass


def update_config_files() -> None:
    # temporary folder to download files in and change permissions to 666
    temp_folder = tempfile.mkdtemp()

    url = "https://downloads.nordcdn.com/configs/archives/servers/ovpn.zip"
    _, filename = url.rsplit("/", maxsplit=1)

    try:
        r = requests.head(url, stream=True)
        total = int(r.headers["content-length"])
    except requests.exceptions.RequestException:
        raise RuntimeError("Error while connecting to {}, Check Your Network Connection. \
forgot to flush iptables? (openpyn -x)".format(url))

    last_modified = r.headers["last-modified"]
    last_update_path = os.path.join(ovpn_folder, "last_update")
    if os.path.exists(last_update_path):
        with open(last_update_path, 'r') as fp:
            last_update = parsedate(fp.read())

        if last_update >= parsedate(last_modified):
            logger.info("Configuration files are up-to-date, skipping...")
            return

    r = requests.get(url, stream=True)
    f = io.BytesIO()
    chunk_size = 512

    with tqdm(total=total, unit="B", unit_scale=True, desc="Downloading {}".format(filename)) as pbar:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

    z = zipfile.ZipFile(f)
    total = sum(f.file_size for f in z.infolist())

    with tqdm(total=total, unit="B", unit_scale=True, desc="Extracting {}".format(filename)) as pbar:
        for file in z.infolist():
            z.extract(file, path=temp_folder)
            pbar.update(file.file_size)

    # change dir permissions so non root can delete/write them
    for root, dirs, files in os.walk(temp_folder):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), 0o777)
        for file in files:
            # os.chmod(os.path.join(root, file), 0o666)
            pass

    # remove dirs, because non-root can't chmod if files/dirs were created by root
    subprocess.run(["rm", "-rf", os.path.join(ovpn_folder, "ovpn_tcp")])
    subprocess.run(["rm", "-rf", os.path.join(ovpn_folder, "ovpn_udp")])

    recusive_copy(temp_folder, ovpn_folder, 0o777)

    with open(os.path.join(ovpn_folder, "last_update"), 'w') as fp:
        fp.write(last_modified)
    os.chmod(os.path.join(ovpn_folder, "last_update"), 0o666)

    shutil.rmtree(temp_folder)


# Impliments recusive copy in python
def recusive_copy(source_path, destination_path, folder_permission):
    for dirpath, dirnames, filenames in os.walk(source_path):
        for dirname in dirnames:
            pass
            # src_folder_path = os.path.join(dirpath, dirname)
            # dst_path = os.path.join(prof, dirname)
        for filename in filenames:
            src_file_path = os.path.join(dirpath, filename)
            src_list = list(Path(src_file_path).parts)
            # remove first element '/' from the list
            src_list.pop(0)
            # find index of base folder in order to extract subfolder paths
            # these subfolder paths will be created in dest location then appended to
            # the full path of files ~/.mozilla/firefox/TEST/"extensions/uBlock0@raymondhill.net.xpi"
            base_folder_ends = len(list(Path(source_path).parts)) - 1

            # extract section after 'profile' out of '/home/user/privacy-fighter/profile/extensions/ext.xpi'
            src_list = src_list[base_folder_ends:]

            # now src_file would be e.g extensions/ext.xpi
            src_file = Path(*src_list)

            dst_file_path = os.path.join(destination_path, src_file)
            # print("file : ", src_file_path, dst_file_path)
            # print("Copying: ", src_file)
            # create parent directory
            if not os.path.exists(os.path.dirname(dst_file_path)):
                os.makedirs(os.path.dirname(dst_file_path))
                os.chmod(os.path.dirname(dst_file_path), folder_permission)
            shutil.copy(src_file_path, dst_file_path)


# Lists information about servers under the given criteria.
def display_servers(list_servers: str, port: str, area: str, p2p: bool, dedicated: bool, double_vpn: bool,
                    tor_over_vpn: bool, anti_ddos: bool, netflix: bool, location: float) -> None:
    servers_on_web = set()      # servers shown on the website

    # if list_servers was not a specific country it would be "all"
    json_res_list = api.get_data_from_api(
        country_code=list_servers, area=area, p2p=p2p, dedicated=dedicated,
        double_vpn=double_vpn, tor_over_vpn=tor_over_vpn, anti_ddos=anti_ddos,
        netflix=netflix, location=location)
    # logger.debug(json_res_list)

    if not json_res_list:
        raise RuntimeError("There are no servers that satisfy your criteria, please broaden your search.")

    print(Style.BRIGHT + Fore.BLUE + "The NordVPN Servers in", Fore.GREEN +
          list_servers.upper() + Fore.BLUE, end=" ")
    if area:
        print("Area", Fore.GREEN + area + Fore.BLUE, end=" ")
    if p2p:
        print("with " + Fore.GREEN + "p2p" + Fore.BLUE + " Support", end=" ")
    if dedicated:
        print("with " + Fore.GREEN + "dedicated" + Fore.BLUE + " Support", end=" ")
    if double_vpn:
        print("with " + Fore.GREEN + "double_vpn" + Fore.BLUE + " Support", end=" ")
    if tor_over_vpn:
        print("with " + Fore.GREEN + "tor_over_vpn" + Fore.BLUE + " Support", end=" ")
    if anti_ddos:
        print("with " + Fore.GREEN + "anti_ddos" + Fore.BLUE + " Support", end=" ")
    if netflix:
        print("with " + Fore.GREEN + "netflix" + Fore.BLUE + " Support", end=" ")
    print("Are:\n" + Style.RESET_ALL)

    # add server names to "servers_on_web" set
    for res in json_res_list:
        print("Server =", res["domain"][:res["domain"].find(".")], ", Load =", res["load"],
              ", Country =", res["country"], ", Features", res["categories"], "\n")
        servers_on_web.add(res["domain"][:res["domain"].find(".")])

    if not area:
        locations_in_country = locations.get_unique_locations(list_of_servers=json_res_list)
        print("The available Locations in country", list_servers.upper(), "are :")
        for eachLocation in locations_in_country:
            print(eachLocation[2])
        print("")

    if list_servers != "all" and not p2p and not dedicated and not double_vpn \
            and not tor_over_vpn and not anti_ddos and not netflix and not area:
        # else not applicable.
        print_latest_servers(list_servers=list_servers, port=port, server_set=servers_on_web)


def print_latest_servers(list_servers: str, port: str, server_set: Set) -> None:
    folder = "ovpn_{}".format(port)

    servers_in_files = set()      # servers from .ovpn files
    new_servers = set()   # new servers, not published on website yet, or taken down
    try:
        server_files_path = os.path.join(ovpn_folder, folder, list_servers)
        server_files = subprocess.check_output(
            "ls " + server_files_path + "*", shell=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("The supplied Country Code is likely wrong or you just don't have \
its config files (In which case run 'sudo openpyn --update')")
    openvpn_files_str = str(server_files)
    openvpn_files_str = openvpn_files_str[2:-3]
    openvpn_files_list = openvpn_files_str.split("\\n")

    for server in openvpn_files_list:
        server_name = os.path.basename(server)
        servers_in_files.add(server_name.split(".")[0])

    for server in servers_in_files:
        if server not in server_set:
            new_servers.add(server)
    if new_servers:
        print("The following servers have not been listed on the nord's site yet, they usually are the fastest or dead.")
        print(new_servers)


def check_config_files() -> None:
    if not os.path.exists(ovpn_folder):
        raise RuntimeError("please run 'sudo openpyn --init' first. {} not found".format(ovpn_folder))


def get_network_interfaces() -> List:
    # find the network interfaces present on the system
    interfaces_details = []

    interfaces = subprocess.check_output("ls /sys/class/net", shell=True)
    interface_string = str(interfaces)
    interface_string = interface_string[2:-3]
    interfaces = interface_string.split("\\n")

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


def get_vpn_server_ip(server: str, port: str) -> str:
    # grab the ip address of VPN server from the config file
    vpn_config_file = os.path.join(ovpn_folder, "ovpn_{}".format(port), "{}.nordvpn.com.{}.ovpn").format(server, port)
    for i in range(2):
        try:
            with open(vpn_config_file, 'r') as openvpn_file:
                for line in openvpn_file:
                    if "remote " in line:
                        vpn_server_ip = line[7:]
                        vpn_server_ip = vpn_server_ip[:vpn_server_ip.find(" ")]
            return vpn_server_ip
        except FileNotFoundError:
            logger.notice("VPN configuration file for '{}' doesn't exist. auto downloading config files".format(server))
            update_config_files()
            continue
        else:
            raise RuntimeError("FileNotFoundError: Get the latest config files by running 'sudo openpyn --update'")


def uses_systemd_resolved() -> bool:
    # see https://www.freedesktop.org/software/systemd/man/systemd-resolved.service.html
    try:
        systemd_resolved_running = subprocess.call(
            ["systemctl", "is-active", "systemd-resolved"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) == 0
    except FileNotFoundError:   # when OS doesn't find systemctl
        return False

    if not systemd_resolved_running:
        return False

    # systemd-resolved is running, good
    # however it's not enough, /etc/resolv.conf might be misconfigured and point at wrong place
    # better safe than sorry!

    stub_systemd_resolver = "127.0.0.53"  # seems to be hardcoded in systemd
    dns_servers = []
    with open("/etc/resolv.conf", "r") as f:
        import re
        ns_rgx = re.compile("nameserver (.*)")
        for line in f:
            m = ns_rgx.match(line)
            if m and m.groups:
                dns_servers.append(m.group(1))
    resolv_conf_managed = dns_servers == [stub_systemd_resolver]

    if resolv_conf_managed:
        return True

    # otherwise, something must be broken.. why is systemd-resolved running, yet resolv.conf still pointing somewhere else?
    # TODO test implications
    logger.warning("systemd-resolved is running, but resolv.conf contains %s, test if DNS leaks!", dns_servers)
    return True


def connect(server: str, port: str, silent: bool, skip_dns_patch: bool,
            openvpn_options: str, use_systemd_resolved: bool, use_resolvconf: bool, server_provider="nordvpn") -> None:
    detected_os = sys.platform
    if server_provider == "nordvpn":
        vpn_config_file = os.path.join(ovpn_folder, "ovpn_{}".format(port), "{}.nordvpn.com.{}.ovpn").format(server, port)
        # logger.debug("CONFIG FILE %s", vpn_config_file)
        if os.path.isfile(vpn_config_file) is False:
            logger.notice("VPN configuration file %s doesn't exist, \
don't worry running 'openpyn --update' for you :)", vpn_config_file)
            time.sleep(6)
            update_config_files()

    root_access = root.verify_root_access("Sudo credentials required to run 'openvpn'")
    if root_access is False:
        root.obtain_root_access()

    kill_management_client()
    kill_vpn_processes()   # kill existing OpenVPN processes

    if not silent:
        # notifications don't work with 'sudo'
        if detected_os == "linux" and root.running_with_sudo():
            logger.warning("Desktop notifications don't work when using 'sudo', run without it, \
when asked, provide the sudo credentials")
            subprocess.Popen("openpyn-management".split())
        else:
            subprocess.Popen("openpyn-management --do-notify".split())

    if not openvpn_options:
        openvpn_options = ""

    logger.success("CONNECTING TO SERVER " + server + " ON PORT " + port)

    if (use_systemd_resolved or use_resolvconf) and skip_dns_patch is False:  # Debian Based OS + do DNS patching
        try:
            if use_systemd_resolved:
                openvpn_options += " " + "--dhcp-option DOMAIN-ROUTE ."
                up_down_script = __basefilepath__ + "scripts/update-systemd-resolved.sh"
                logger.success("Your OS '%s' has systemd-resolve running, \
using it to update DNS Resolver Entries", detected_os)
            elif use_resolvconf:
                # tunnel DNS through VPN by changing /etc/resolv.conf using
                # "update-resolv-conf.sh" to change the DNS servers to NordVPN's.

                up_down_script = __basefilepath__ + "scripts/update-resolv-conf.sh"
                logger.success("Your OS '%s' Does have '/sbin/resolvconf', \
using it to update DNS Resolver Entries", detected_os)
            else:
                raise RuntimeError("Should not happen")

            def run_openvpn(*args):
                cmdline = [
                    "sudo", "openvpn",
                    "--redirect-gateway",
                    "--status", "{}/openvpn-status".format(log_folder), "30",
                    "--auth-retry", "nointeract",
                    "--config", vpn_config_file,
                    "--auth-user-pass", __basefilepath__ + "credentials",
                    "--script-security", "2",
                    "--up", up_down_script,
                    "--down", up_down_script,
                    "--down-pre",
                    *args,
                ] + openvpn_options.split()
                completed = subprocess.run(cmdline, check=True)

                # "sudo killall openvpn" - the default signal sent is SIGTERM
                # SIGTERM signal causes OpenVPN to exit gracefully - OpenVPN exits with 0 status

                if completed.returncode == 0:
                    raise SystemExit

            if silent:
                run_openvpn()
            else:
                run_openvpn(
                    "--management", "127.0.0.1", "7015",
                    "--management-up-down",
                )
        except subprocess.CalledProcessError as openvpn_err:
            # logger.debug(openvpn_err.output)
            if "Error opening configuration file" in str(openvpn_err.output):
                raise RuntimeError("Error opening config %s, make sure it exists, run 'openpyn --update'" % vpn_config_file)
        except KeyboardInterrupt:
            raise SystemExit
        except PermissionError:     # needed cause complains when killing sudo process
            raise SystemExit
    else:       # if not Debian Based or skip_dns_patch
        # if skip_dns_patch, do not touch etc/resolv.conf
        if skip_dns_patch is False:
            logger.warning("Your OS '%s' Does not have '/sbin/resolvconf'", detected_os)
            logger.notice("Manually applying patch to tunnel DNS through the VPN tunnel by modifying '/etc/resolv.conf'")
            subprocess.call(["sudo", __basefilepath__ + "scripts/manual-dns-patch.sh"])
        else:
            logger.warning("Not modifying '/etc/resolv.conf', DNS traffic likely won't go through the encrypted tunnel")

        try:
            def run_openvpn(*args):
                cmdline = [
                    "sudo", "openvpn",
                    "--redirect-gateway",
                    "--status", "{}/openvpn-status".format(log_folder), "30",
                    "--auth-retry", "nointeract",
                    "--config", vpn_config_file,
                    "--auth-user-pass", __basefilepath__ + "credentials",
                    *args,
                ] + openvpn_options.split()
                completed = subprocess.run(cmdline, check=True)

                # "sudo killall openvpn" - the default signal sent is SIGTERM
                # SIGTERM signal causes OpenVPN to exit gracefully - OpenVPN exits with 0 status

                if completed.returncode == 0:
                    raise SystemExit

            if silent:
                run_openvpn()
            else:
                run_openvpn(
                    "--management", "127.0.0.1", "7015",
                    "--management-up-down",
                )
        except subprocess.CalledProcessError as openvpn_err:
            # logger.debug(openvpn_err.output)
            if 'Error opening configuration file' in str(openvpn_err.output):
                raise RuntimeError("Error opening config %s, make sure it exists, run 'openpyn --update'" % vpn_config_file)
        except KeyboardInterrupt:
            raise SystemExit
        except PermissionError:     # needed cause complains when killing sudo process
            raise SystemExit


if __name__ == '__main__':
    sys.exit(main())
