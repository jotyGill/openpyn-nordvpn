import subprocess
import sys

from openpyn import sudo_user


# Add route to allow traffic to go out of the public ip
# For opening services like ssh/http on anything on public net,
# Needed on VPSs.
def add_route():
    table_number = "175"

    default_route = subprocess.check_output(["ip", "route", "show", "default"]).decode(sys.stdout.encoding).strip().split()
    default_gateway_ip = default_route[2]
    # default_interface = default_route[4]

    # Get the first IP address reported by 'hostname --all-ip-addresses'
    ip_addr = subprocess.check_output(["hostname", "--all-ip-addresses"]).decode(sys.stdout.encoding).strip().split()[0]

    route_rule = "from {} lookup {}".format(ip_addr, table_number)
    # print(route_rule)
    ip_rules = str(subprocess.check_output(["ip", "rule", "list"]))
    if route_rule in ip_rules:
        print("IP route rule already exists, skipping")
    else:
        # Add ip rule and route to send traffic through the default gateway.
        subprocess.call(
            ["sudo", "-u", sudo_user, "ip", "rule", "add", "from", ip_addr, "table", table_number]
        )
        # subprocess.call(
        #     ["sudo", "-u", sudo_user, "ip", "route", "add", "table", table_number, "to", ip_addr + "/32", "dev", default_interface]
        # )

        subprocess.call(
            ["sudo", "-u", sudo_user, "ip", "route", "add", "table", table_number, "default", "via", default_gateway_ip]
        )
