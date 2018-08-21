import logging
import subprocess
from typing import List

import verboselogs

from openpyn import root

verboselogs.install()
logger = logging.getLogger(__package__)


def manage_ipv6(disable: bool) -> None:
    value = 1 if disable else 0
    try:
        subprocess.check_call(
            ["sudo", "sysctl", "-w", "net.ipv6.conf.all.disable_ipv6={}".format(value)],
            stdout=subprocess.DEVNULL)
    except subprocess.SubprocessError:      # in case systemd is not used
        logger.warning("Cant disable/enable ipv6 using sysctl, are you even using systemd?")


# Clears Firewall rules, applies basic rules.
def clear_fw_rules() -> None:
    root.verify_root_access("Root access needed to modify 'iptables' rules")
    logger.info("Flushing iptables INPUT and OUTPUT chains AND Applying default Rules")
    subprocess.call(["sudo", "iptables", "-F", "OUTPUT"])
    # allow all outgoing traffic
    subprocess.call("sudo iptables -P OUTPUT ACCEPT".split())

    subprocess.call(["sudo", "iptables", "-F", "INPUT"])
    subprocess.call(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    subprocess.call(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    subprocess.call(
        "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT".split())
    # allow ICMP traffic
    subprocess.call("sudo iptables -A INPUT -p icmp --icmp-type any -j ACCEPT".split())
    # best practice, stops spoofing
    subprocess.call("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP".split())
    # drop anything else incoming
    subprocess.call("sudo iptables -P INPUT DROP".split())
    return


NORDVPN_DNS = [
    "103.86.96.100",
    "103.86.99.100",
]


def do_dns(iface: str, dest: str, what: str) -> None:
    # for pp in ("udp", "tcp"):
    pp = "udp"
    cmd = ["sudo",
           "iptables",
           "-A", "OUTPUT",
           "-p", pp,
           "-d", dest, "--destination-port", "53",
           "-j", what,
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


def apply_fw_rules(interfaces_details: List, vpn_server_ip: str, skip_dns_patch: bool) -> None:
    root.verify_root_access("Root access needed to modify 'iptables' rules")

    # Empty the INPUT and OUTPUT chain of any current rules
    subprocess.check_call(["sudo", "iptables", "-F", "OUTPUT"])
    subprocess.check_call(["sudo", "iptables", "-F", "INPUT"])

    apply_dns_rules()
    logger.notice("Temporarily disabling ipv6 to prevent leakage")
    manage_ipv6(disable=True)

    # Allow all traffic out over the vpn tunnel
    # except for DNS, which is handled by systemd-resolved script
    # NOTE: that def helped with leaky DNS queries, nothing in wireshark too
    # weird that ping ya.ru was showing "operation not permitted"
    subprocess.check_call([
        "sudo", "iptables",
        "-A", "OUTPUT",
        "-o", "tun+",
        # "-p", "all", "-d", "0.0.0.0/0", "!", "--dport", "53",
        "-p", "all", "-d", "0.0.0.0/0",
        "-j", "ACCEPT"
    ])
    # accept traffic that comes through tun that you connect to
    subprocess.check_call(
        "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED\
         -i tun+ -j ACCEPT".split())

    for interface in interfaces_details:
        if len(interface) != 3:
            continue  # TODO what does that mean?
        iname = interface[0]

        if len(iname) == 0:
            print("WARNING: empty {}".format(interface))
            continue

        # allow access to vpn_server_ip
        subprocess.check_call(
            ["sudo", "iptables", "-A", "OUTPUT", "-o", iname,
                "-d", vpn_server_ip, "-j", "ACCEPT"])
        # talk to the vpnServer ip to connect to it
        subprocess.check_call(
            ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                "--ctstate", "ESTABLISHED,RELATED", "-i", iname,
                "-s", vpn_server_ip, "-j", "ACCEPT"])

        # allow access to internal ip range
        # print("internal ip with range", interface[2])
        subprocess.check_call(
            ["sudo", "iptables", "-A", "OUTPUT", "-o", iname, "-d",
                interface[2], "-j", "ACCEPT"])
        subprocess.check_call(
            ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                "--ctstate", "ESTABLISHED,RELATED", "-i", iname,
                "-s", interface[2], "-j", "ACCEPT"])

    # Allow loopback traffic
    subprocess.check_call("sudo iptables -A INPUT -i lo -j ACCEPT".split())
    subprocess.check_call("sudo iptables -A OUTPUT -o lo -j ACCEPT".split())

    # best practice, stops spoofing
    subprocess.check_call("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP".split())

    # Default action if no other rules match
    subprocess.check_call("sudo iptables -P OUTPUT DROP".split())
    subprocess.check_call("sudo iptables -P INPUT DROP".split())
    return


# open sepecified ports for devices in the local network
def internally_allow_ports(interfaces_details: List, internally_allowed: List) -> None:
    for interface in interfaces_details:
        # if interface is active with an IP in it, and not "tun*"
        if len(interface) == 3 and "tun" not in interface[0]:
            # Allow the specified ports on internal network
            for port in internally_allowed:
                subprocess.call(
                    ("sudo iptables -A INPUT -p tcp --dport " + port + " -i " +
                        interface[0] + " -s " + interface[2] + " -j ACCEPT").split())
