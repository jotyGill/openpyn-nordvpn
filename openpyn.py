#!/usr/bin/python3

import subprocess
import argparse


def main(server, udp):
    port = "tcp443"
    if udp:
        port = "udp1194"

    subprocess.run(
        ["sudo", "openvpn", "--config", "./files/" + server.lower() +
            ".nordvpn.com." + port + ".ovpn", "--auth-user-pass", "pass.txt"],
        stdin=subprocess.PIPE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script to Connect to OpenVPN')
    parser.add_argument(
        '-s', '--server', help='server name, i.e. ca64 or au10', required=True)
    parser.add_argument(
        '-u', '--udp', help='use port UDP1194 instead of the default TCP443',
        action='store_true')
    args = parser.parse_args()
    main(args.server, args.udp)
