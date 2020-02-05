import subprocess
import sys


# Add route to allow traffic to go out of the public ip
# For opening services like ssh/http on anything on public net,
# Needed for VPS.
def add_route(interfaces_details: List) -> None:
    count = 175
    # print(interfaces_details)
    # sys.exit()
    for interface in interfaces_details:
        # print(interface)

        # if interface is active with an IP in it, and not "tun*"
        if len(interface) == 3 and "tun" not in interface[0]:
            ip_addr = interface[2][:interface[2].find("/")]
            count+=1
            route_rule = "from {} lookup {}".format(ip_addr,count)
            print(route_rule)
            ip_rules = str(subprocess.check_output(["ip","rule","list"]))
            if route_rule in ip_rules:
                print("IP route rule already exists")
                continue
            subprocess.call([
                "sudo", "ip",
                "rule", "add",
                "from", ip_addr,
                "table", str(count),
            ])
            subprocess.call([
                "sudo", "ip",
                "route", "add",
                "table", str(count),
                "to", ip_addr,
            ])
