import subprocess
from openpyn import root


# Clears Firewall rules, applies basic rules.
def clear_fw_rules():
    root.verify_root_access("Root access needed to modify 'iptables' rules")
    print("Flushing iptables INPUT and OUTPUT chains AND Applying default Rules")
    subprocess.run(["sudo", "iptables", "-F", "OUTPUT"])
    # allow all outgoing traffic
    subprocess.run("sudo iptables -P OUTPUT ACCEPT".split())

    subprocess.run(["sudo", "iptables", "-F", "INPUT"])
    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    subprocess.run(
        "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT".split())
    # allow ICMP traffic
    subprocess.run("sudo iptables -A INPUT -p icmp --icmp-type any -j ACCEPT".split())
    # best practice, stops spoofing
    subprocess.run("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP".split())
    # drop anything else incoming
    subprocess.run("sudo iptables -P INPUT DROP".split())
    return


def apply_fw_rules(interfaces_details, vpn_server_ip):
    root.verify_root_access("Root access needed to modify 'iptables' rules")

    # Empty the INPUT and OUTPUT chain of any current rules
    subprocess.run(["sudo", "iptables", "-F", "OUTPUT"])
    subprocess.run(["sudo", "iptables", "-F", "INPUT"])

    # Allow all traffic out over the vpn tunnel
    subprocess.run("sudo iptables -A OUTPUT -o tun+ -j ACCEPT".split())
    # accept traffic that comes through tun that you connect to
    subprocess.run(
        "sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED\
         -i tun+ -j ACCEPT".split())
    for interface in interfaces_details:

        # if interface is active with an IP in it, don't send DNS requests to it
        if len(interface) == 3 and "tun" not in interface[0]:
            subprocess.run(
                ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-p",
                    "udp", "--destination-port", "53", "-j", "DROP"])
            # subprocess.run(
            #     ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-p",
            #         "tcp", "--destination-port", "53", "-j", "DROP"])
            if interface[0] != "lo":
                # allow access to vpn_server_ip
                subprocess.run(
                    ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0],
                        "-d", vpn_server_ip, "-j", "ACCEPT"])
                # talk to the vpnServer ip to connect to it
                subprocess.run(
                    ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                        "--ctstate", "ESTABLISHED,RELATED", "-i", interface[0],
                        "-s", vpn_server_ip, "-j", "ACCEPT"])

                # allow access to internal ip range
                # print("internal ip with range", interface[2])
                subprocess.run(
                    ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-d",
                        interface[2], "-j", "ACCEPT"])
                subprocess.run(
                    ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                        "--ctstate", "ESTABLISHED,RELATED", "-i", interface[0],
                        "-s", interface[2], "-j", "ACCEPT"])

    # Allow loopback traffic
    subprocess.run("sudo iptables -A INPUT -i lo -j ACCEPT".split())
    subprocess.run("sudo iptables -A OUTPUT -o lo -j ACCEPT".split())

    # best practice, stops spoofing
    subprocess.run("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP".split())

    # Default action if no other rules match
    subprocess.run("sudo iptables -P OUTPUT DROP".split())
    subprocess.run("sudo iptables -P INPUT DROP".split())
    return


def internally_allow_ports(interfaces_details, internally_allowed):
    for interface in interfaces_details:
        # if interface is active with an IP in it, and not "tun*"
        if len(interface) == 3 and "tun" not in interface[0]:
            # Allow the specified ports on internal network
            for port in internally_allowed:
                subprocess.run(
                    ("sudo iptables -A INPUT -p tcp --dport " + port + " -i " +
                        interface[0] + " -s " + interface[2] + " -j ACCEPT").split())
