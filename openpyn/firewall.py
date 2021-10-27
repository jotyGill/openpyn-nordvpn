import itertools
import json
import logging
import os
import subprocess
from typing import Dict
from typing import List

import verboselogs
from jsonschema import Draft4Validator

from openpyn import root
from openpyn import sudo_user

verboselogs.install()
logger = logging.getLogger(__package__)


def manage_ipv6(disable: bool) -> None:
    value = 1 if disable else 0
    try:
        subprocess.check_call(
            ["sudo", "-u", sudo_user, "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6={}".format(value)],
            stdout=subprocess.DEVNULL,
        )
    except subprocess.SubprocessError:  # in case systemd is not used
        logger.warning("Cant disable/enable ipv6 using sysctl, are you even using systemd?")


# Clears Firewall rules, applies basic rules.
def clear_fw_rules() -> None:
    root.verify_root_access("Root access needed to modify 'iptables' rules")
    logger.info("Flushing iptables INPUT and OUTPUT chains AND Applying default Rules")

    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-F", "OUTPUT"])

    # allow all outgoing traffic
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-P", "OUTPUT", "ACCEPT"])

    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-F", "INPUT"])
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    subprocess.call([
        "sudo", "-u", sudo_user, "iptables",
        "-A", "INPUT",
        "-m", "conntrack",
        "--ctstate", "ESTABLISHED,RELATED",
        "-j", "ACCEPT"
    ])

    # allow ICMP traffic
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-A", "INPUT", "-p", "icmp", "--icmp-type", "any", "-j", "ACCEPT"])

    # best practice, stops spoofing
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-A", "INPUT", "-s", "127.0.0.0/8", "-j", "DROP"])

    # drop anything else incoming
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-P", "INPUT", "DROP"])


NORDVPN_DNS = [
    "103.86.96.100",
    "103.86.99.100",
]


# flush input and output iptables rules.
def flush_input_output() -> None:
    root.verify_root_access("Root access needed to modify 'iptables' rules")
    logger.info("Flushing ALL INPUT and OUTPUT Rules")
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-F", "OUTPUT"])
    subprocess.call(["sudo", "-u", sudo_user, "iptables", "-F", "INPUT"])


def do_dns(iface: str, dest: str, what: str) -> None:
    # for pp in ("udp", "tcp"):
    pp = "udp"
    cmd = [
        "sudo", "-u", sudo_user, "iptables",
        "-A", "OUTPUT",
        "-p", pp,
        "-d", dest, "--destination-port", "53",
        "-j", what
    ]
    if iface is not None:
        cmd.extend(["-o", iface])
    subprocess.check_call(cmd)


# responsibility of update-systemd-resolved script now...
def apply_dns_rules():
    root.verify_root_access("Root access needed to modify 'iptables' rules")
    for ndns in NORDVPN_DNS:
        do_dns("lo", ndns, "ACCEPT")
        do_dns("tun+", ndns, "ACCEPT")
    # do_dns(None, "0.0.0.0/0", "DROP")


def apply_fw_rules(interfaces_details: List, vpn_server_ips: List, skip_dns_patch: bool) -> None:
    root.verify_root_access("Root access needed to modify 'iptables' rules")

    apply_dns_rules()
    logger.notice("Temporarily disabling ipv6 to prevent leakage")
    manage_ipv6(disable=True)

    # allow all traffic out over the VPN tunnel
    # except for DNS, which is handled by systemd-resolved script
    # NOTE: that def helped with leaky DNS queries, nothing in Wireshark too
    # weird that ping ya.ru was showing "operation not permitted"
    subprocess.check_call([
        "sudo", "-u", sudo_user, "iptables",
        "-A", "OUTPUT",
        "-o", "tun+",
        # "-p", "all", "-d", "0.0.0.0/0", "!", "--dport", "53",
        "-p", "all", "-d", "0.0.0.0/0",
        "-j", "ACCEPT"
    ])

    # accept traffic that comes through tun that you connect to
    subprocess.check_call([
        "sudo", "-u", sudo_user, "iptables",
        "-A", "INPUT",
        "-m", "conntrack",
        "--ctstate", "ESTABLISHED,RELATED",
        "-i", "tun+",
        "-j", "ACCEPT"
    ])

    for interface in interfaces_details:
        if len(interface) != 3:
            continue  # TODO what does that mean?
        iname = interface[0]

        if not iname:
            print("WARNING: empty {}".format(interface))
            continue

        # Allow currently chosen vpn_server_ips
        for vpn_server_ip in vpn_server_ips:
            # allow access to vpn_server_ip
            subprocess.check_call([
                "sudo", "-u", sudo_user, "iptables",
                "-A", "OUTPUT",
                "-o", iname,
                "-d", vpn_server_ip,
                "-j", "ACCEPT"
            ])

            # talk to the vpn_server_ip to connect to it
            subprocess.check_call([
                "sudo", "-u", sudo_user, "iptables",
                "-A", "INPUT",
                "-m", "conntrack",
                "--ctstate", "ESTABLISHED,RELATED",
                "-i", iname,
                "-s", vpn_server_ip,
                "-j", "ACCEPT"
            ])

        # allow access to internal IP range
        # print("internal IP with range", interface[2])
        subprocess.check_call([
            "sudo", "-u", sudo_user, "iptables",
            "-A", "OUTPUT",
            "-o", iname,
            "-d", interface[2],
            "-j", "ACCEPT"
        ])

        subprocess.check_call([
            "sudo", "-u", sudo_user, "iptables",
            "-A", "INPUT",
            "-m", "conntrack",
            "--ctstate", "ESTABLISHED,RELATED",
            "-i", iname,
            "-s", interface[2],
            "-j", "ACCEPT"
        ])

    # allow loopback traffic
    subprocess.check_call(["sudo", "-u", sudo_user, "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    subprocess.check_call(["sudo", "-u", sudo_user, "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])

    # best practice, stops spoofing
    subprocess.check_call(["sudo", "-u", sudo_user, "iptables", "-A", "INPUT", "-s", "127.0.0.0/8", "-j", "DROP"])

    # default action if no other rules match
    subprocess.check_call(["sudo", "-u", sudo_user, "iptables", "-P", "OUTPUT", "DROP"])
    subprocess.check_call(["sudo", "-u", sudo_user, "iptables", "-P", "INPUT", "DROP"])


# Open specified ports for devices in the local network
def internally_allow_ports(interfaces_details: List, internally_allowed: List) -> None:
    for interface in interfaces_details:
        # if interface is active with an IP in it, and not "tun*"
        if len(interface) == 3 and "tun" not in interface[0]:
            # allow the specified ports on internal network
            for port in internally_allowed:
                subprocess.call([
                    "sudo", "-u", sudo_user, "iptables",
                    "-A", "INPUT",
                    "-p", "tcp",
                    "--dport", port,
                    "-i", interface[0],
                    "-s", interface[2],
                    "-j", "ACCEPT"
                ])


# Open all ports for devices in the local network
def internally_allow_all(interfaces_details: List) -> None:
    for interface in interfaces_details:
        # if interface is active with an IP in it, and not "tun*"
        if len(interface) == 3 and "tun" not in interface[0]:
            subprocess.call([
                "sudo", "-u", sudo_user, "iptables",
                "-A", "INPUT",
                "-i", interface[0],
                "-s", interface[2],
                "-j", "ACCEPT"
            ])


# Converts the allwed ports config to a series of iptable rules and applies them
def apply_allowed_port_rules(interfaces_details: List, allowed_ports_config: List) -> bool:

    if not validate_allowed_ports_json(allowed_ports_config):
        return False

    root.verify_root_access("Root access needed to pre load fire wall rules")

    DEFAULT_PORT_CONFIG = {"internal": True, "protocol": "tcp", "allowed_ip_range": None}

    # Merge default config with existing config
    allowed_ports_config = [{**DEFAULT_PORT_CONFIG, **port_config} for port_config in allowed_ports_config]

    ip_table_rules = []

    for port_config in allowed_ports_config:
        # Get perms for the connection type
        port_protocol_permiatations = []

        if port_config["protocol"] in ["tcp", "both"]:
            port_protocol_permiatations.append("tcp")

        if port_config["protocol"] in ["udp", "both"]:
            port_protocol_permiatations.append("udp")

        # Create the flags for the port range / port
        if "-" in str(port_config["port"]):
            port_range = port_config["port"].split("-")
            port_flag = "--match multiport --dports {0}:{1}".format(*port_range)
        else:
            port_flag = "--dport {0}".format(port_config["port"])

        for interface, port_type in itertools.product(interfaces_details, port_protocol_permiatations):
            # Skip any tunnel interfaces that might be invalid
            if len(interface) != 3 or "tun" in interface[0]:
                continue

            ip_flag = ""
            ip_ranges = []

            if port_config["internal"]:
                ip_ranges.append(interface[2])

            if port_config["allowed_ip_range"] is not None:
                if isinstance(port_config["allowed_ip_range"], list):
                    ip_ranges += port_config["allowed_ip_range"]
                else:
                    ip_ranges.append(port_config["allowed_ip_range"])

            if ip_ranges != []:
                ip_flag = " -s " + ",".join(ip_ranges)

            ip_table_rules.append(
                "sudo -u {user} iptables -A INPUT -p {port_type} {port_flag} -i {interface}{ip_flag} -j ACCEPT".format(
                    user=sudo_user, port_type=port_type, port_flag=port_flag, interface=interface[0], ip_flag=ip_flag
                )
            )

    for rule in ip_table_rules:
        subprocess.call(rule.split(" "))

    return True


# Load allowed ports config from path (does not include validation)
def load_allowed_ports(path_to_allowed_ports: str) -> bool:
    # Ensure paths are resolved to real paths
    path_to_allowed_ports = os.path.realpath(path_to_allowed_ports)

    if not os.path.isfile(path_to_allowed_ports):
        logger.warn("Cannot preload allowed ports: file {0} does not exist".format(path_to_allowed_ports))
        return False

    try:
        with open(path_to_allowed_ports, "rt") as file_handle:
            try:
                allowed_ports_config = json.load(file_handle)
            except json.JSONDecodeError as json_decode_error:
                logger.error(
                    "Failed to decode allowed ports JSON Error at line {line}:{col} {msg} ".format(
                        line=json_decode_error.lineno, col=json_decode_error.colno, msg=json_decode_error.msg
                    )
                )
                return False

    except EnvironmentError as file_read_error:
        logger.error(
            'Cannot preload allowed ports: failed to load "{filename}" {strerr}'.format(
                filename=file_read_error.filename, strerr=file_read_error.strerror
            )
        )

    return allowed_ports_config


# Validates if the allowed ports JSON is valid before loading it
def validate_allowed_ports_json(allowed_ports_config: Dict) -> bool:
    validation_schema = {
        "description": "Root config node",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "port": {
                    "anyOf": [
                        {
                            "name": "Port number",
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 65535
                        },
                        {
                            "type": "string",
                            "pattern": "^\\d{1,5}(-\\d{1,5})?$"
                        }
                    ]
                },
                "protocol": {
                    "type": "string",
                    "pattern": "^(tcp|ip|both)$"
                },
                "internal": {
                    "type": "boolean",
                },
                "allowed_ip_range": {
                    "anyOf": [
                        {
                            "$ref": "#/definitions/ip_address_block"
                        },
                        {
                            "items": {"$ref": "#/definitions/ip_address_block"},
                            "uniqueItems": True
                        }
                    ]

                }
            },
            "required": ["port"]
        },
        "definitions": {
            "ip_address_block": {
                "type": "string",
                "pattern": "^([0-9]{1,3}\.){3}[0-9]{1,3}(\/([0-9]|[1-2][0-9]|3[0-2]))?$"
            }
        }
    }

    # Create the config validator
    allowed_ports_config_validator = Draft4Validator(validation_schema)

    # If the passed config is not valid enumerate errors and print them in human readable form
    if not allowed_ports_config_validator.is_valid(allowed_ports_config):

        error_message = "Errors were raise when validating the allowed ports config:"
        # Retrieve all validation errors yielded in schema
        for validation_error in allowed_ports_config_validator.iter_errors(allowed_ports_config):
            error_message += "\n\nError at root.{0} in config: {1}".format(
                ".".join([str(part) for part in validation_error.absolute_path]), validation_error.message
            )

        logger.error(error_message)

        return False

    return True
