import argparse
import fileinput
import logging
import os
import subprocess
import sys

import verboselogs

from openpyn import api

verboselogs.install()
logger = logging.getLogger(__package__)


def install_service() -> None:
    if not sys.__stdin__.isatty():
        raise RuntimeError("Please run %s in interactive mode" % __name__)

    openpyn_options = (
        input(
            "\nEnter Openpyn options to be stored in initd service file (/opt/etc/init.d/S23openpyn, Default(Just Press"
            " Enter) is, uk : "
        )
        or "uk"
    )

    # regex used
    # .*add_argument_group.*\n --> ""
    # \, help='(.|\\\n)+', --> ","
    # \, help='(.|\\\n)+' --> ""
    # (\n).+       ' --> "'"
    # (\n).+       ac --> " ac"

    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('--allow', dest='internally_allowed', nargs='+')
    # parser.add_argument('--allow-config', dest='internally_allowed_config')
    parser.add_argument('--allow-config-json', dest='internally_allowed_config_json')
    parser.add_argument('--allow-locally', dest='allow_locally', action='store_true')
    parser.add_argument('--anti-ddos', dest='anti_ddos', action='store_true')
    parser.add_argument('--dedicated', action='store_true')
    parser.add_argument('--double', dest='double_vpn', action='store_true')
    parser.add_argument('--netflix', dest='netflix', action='store_true')
    parser.add_argument('--p2p', action='store_true')
    parser.add_argument('--silent', action='store_true')
    parser.add_argument('--skip-dns-patch', dest='skip_dns_patch', action='store_true')
    parser.add_argument('--tcp', action='store_true')
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--tor', dest='tor_over_vpn', action='store_true')
    parser.add_argument('--update', action='store_true')
    parser.add_argument('-a', '--area', type=str)
    parser.add_argument('-c', '--country-code', type=str)
    parser.add_argument('-f', '--force-fw-rules', action='store_true')
    parser.add_argument('-loc', '--location', nargs=2, type=float)
    parser.add_argument('-m', '--max-load', type=int, default=70)
    parser.add_argument('-n', '--nvram', type=str)
    parser.add_argument('-o', '--openvpn-options', dest='openvpn_options', type=str)
    parser.add_argument('-s', '--server', type=str)
    parser.add_argument('-t', '--top-servers', type=int, default=10)
    parser.add_argument('country', nargs='?')

    try:
        args = parser.parse_args(openpyn_options.split())
    except SystemExit as e:
        if e.code == 2:
            openpyn_options = (
                input(
                    "\nEnter Openpyn options to be stored in initd service file (/opt/etc/init.d/S23openpyn, Default(Just"
                    " Press Enter) is, uk : "
                )
                or "uk"
            )
            args = parser.parse_args(openpyn_options.split())

    if args.update:
        update_service("--update")
        return

    server = args.server
    country_code = args.country_code
    country = args.country
    area = args.area
    tcp = args.tcp
    max_load = args.max_load
    top_servers = args.top_servers
    force_fw_rules = args.force_fw_rules
    p2p = args.p2p
    dedicated = args.dedicated
    double_vpn = args.double_vpn
    tor_over_vpn = args.tor_over_vpn
    anti_ddos = args.anti_ddos
    netflix = args.netflix
    test = args.test
    internally_allowed = args.internally_allowed
    internally_allowed_config_json = args.internally_allowed_config_json
    skip_dns_patch = args.skip_dns_patch
    silent = args.silent
    nvram = args.nvram
    openvpn_options = args.openvpn_options
    location = args.location

    detected_os = sys.platform
    if detected_os == "linux":
        if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
            force_fw_rules = False
            internally_allowed = None
            silent = True
            skip_dns_patch = True
        elif os.path.exists("/etc/openwrt_release"):
            force_fw_rules = False
            internally_allowed = None
            silent = True
            skip_dns_patch = True
            nvram = None
        else:
            nvram = None

    openpyn_options = ""

    # if only positional argument used
    if country_code is None and server is None:
        # consider the positional arg e.g "us" same as "-c us"
        country_code = country

    # if either "-c" or positional arg f.e "au" is present
    if country_code:
        # if full name of the country supplied get country_code
        if len(country_code) > 2:
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
    if internally_allowed_config_json:
        # Assume at this stage the JSON has been passed as string so it can be directly loaded
        openpyn_options += " --allow-config-json=" + internally_allowed_config_json
    if skip_dns_patch:
        openpyn_options += " --skip-dns-patch"
    if silent:
        openpyn_options += " --silent"
    if nvram:
        openpyn_options += " --nvram " + nvram
    if openvpn_options:
        openpyn_options += " --openvpn-options '" + openvpn_options + "'"
    if location:
        openpyn_options += " --location " + str(location[1]) + " " + str(location[2])

    update_service(openpyn_options)


def update_service(openpyn_options: str, run=False) -> None:
    # logger.debug(openpyn_options)

    os.chmod("/opt/etc/init.d/S23openpyn", 0o755)
    for line in fileinput.FileInput("/opt/etc/init.d/S23openpyn", inplace=1):
        sline = line.strip().split("=")
        if sline[0].startswith("ARGS"):
            sline[1] = '"' + openpyn_options + '"'
        line = "=".join(sline)
        print(line)

    logger.notice(
        "The Following config has been saved in S23openpyn. You can Start it or/and Stop it with:"
        " '/opt/etc/init.d/S23openpyn start', '/opt/etc/init.d/S23openpyn stop' \n"
    )

    if run:
        logger.notice(
            "Started Openpyn by running '/opt/etc/init.d/S23openpyn start'\nTo check VPN status, run"
            " '/opt/etc/init.d/S23openpyn check'"
        )
        subprocess.run(["/opt/etc/init.d/S23openpyn", "start"], check=False)
