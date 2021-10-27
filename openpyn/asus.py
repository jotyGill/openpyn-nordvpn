import logging
import os
import subprocess

import verboselogs

from openpyn import api
from openpyn import credentials_file_path
from openpyn import ovpn_folder
from openpyn import sudo_user
from openpyn.converter import T_CLIENT
from openpyn.converter import Converter

verboselogs.install()
logger = logging.getLogger(__package__)


def run(server, client, options=None, rgw=None, comp=None, adns=None, tcp=False, test=False, debug=False):
    country_name = api.get_country_name(server[:2])

    with open(credentials_file_path, "r") as f:
        lines = f.read().splitlines()

    port = "udp"
    port_name = "1194"
    protocol_name = "udp"
    folder = "/ovpn_udp/"
    if tcp:
        port = "tcp"
        port_name = "443"
        protocol_name = "tcp-client"
        folder = "/ovpn_tcp/"

    vpn_config_file = server + ".nordvpn.com." + port + ".ovpn"

    certs_folder = "/jffs/openvpn/"

    if not os.path.exists(certs_folder):
        os.mkdir(certs_folder, 0o700)
        os.chmod(certs_folder, 0o700)

    c = Converter(debug)
    c.set_username(lines[0])
    c.set_password(lines[1])
    c.set_description("Client" + " " + country_name)
    c.set_port(port_name)
    c.set_protocol(protocol_name)

    c.set_name(server)
    c.set_source_folder(ovpn_folder + folder)
    c.set_certs_folder(certs_folder)

    c.set_accept_dns_configuration(adns)
    c.set_compression(comp)
    c.set_redirect_gateway(rgw)
    c.set_client(client)

    if options:
        c.set_openvpn_options("\n".join(filter(None, options.split("--"))) + "\n")

    extracted_info = c.extract_information(vpn_config_file)
    if not test:
        c.write_certificates(client)

    # 'vpn_client_unit'
    key = ""
    value = ""
    unit = ""
    service = "client"

    for key, value in extracted_info.items():
        write(key, value, unit, service, test)

    extracted_info = dict(extracted_info)
    if T_CLIENT in extracted_info:
        del extracted_info[T_CLIENT]

    # 'vpn_client_unit$'
    key = ""
    value = ""
    unit = client
    service = "client"

    for key, value in extracted_info.items():
        write(key, value, unit, service, test)

    # 'vpn_upload_unit'
    key = T_CLIENT
    value = client
    unit = ""
    service = "upload"

    write(key, value, unit, service, test)


def write(key, value, unit, service, test=False):
    argument1 = "vpn" + "_" + service + unit + "_" + key
    argument2 = argument1 + "=" + value
    try:
        pprint("/bin/nvram" + " " + "get" + " " + argument1)
        if not test:
            process = subprocess.run(["/bin/nvram", "get", argument1], check=True, stdout=subprocess.PIPE)
            if process.stdout.decode("utf-8").strip() == value:
                return
        pprint("/bin/nvram" + " " + "set" + " " + argument2)
        if not test:
            subprocess.run(["sudo", "-u", sudo_user, "/bin/nvram", "set", argument2], check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output) from e


def connect(unit, test=False):
    argument1 = "vpnclient" + unit
    argument2 = "start" + "_" + "vpnclient" + unit
    try:
        pprint("/bin/pidof" + " " + argument1)
        if not test:
            process = subprocess.run(["/bin/pidof", argument1], stdout=subprocess.DEVNULL, check=False)
            if process.returncode == 0:  # Connected
                return
        pprint("/sbin/service" + " " + argument2)
        if not test:
            subprocess.run(["sudo", "-u", sudo_user, "/sbin/service", argument2], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output) from e


def disconnect(unit, test=False):
    argument1 = "vpnclient" + unit
    argument2 = "stop" + "_" + "vpnclient" + unit
    try:
        pprint("/bin/pidof" + " " + argument1)
        if not test:
            process = subprocess.run(["/bin/pidof", argument1], stdout=subprocess.DEVNULL, check=False)
            if process.returncode == 1:  # Disconnected
                return
        pprint("/sbin/service" + " " + argument2)
        if not test:
            subprocess.run(["sudo", "-u", sudo_user, "/sbin/service", argument2], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output) from e


def state(unit, test=False) -> bool:
    argument1 = "vpn" + "_" + "client" + unit + "_" + "state"
    try:
        pprint("/bin/nvram" + " " + "get" + " " + argument1)
        if not test:
            client_state = subprocess.run(["/bin/nvram", "get", argument1], check=True, stdout=subprocess.PIPE).stdout
            code = client_state.decode("utf-8").strip()
            if code == "1":
                logger.success("Connecting...")
            elif code == "2":
                logger.success("Connected")
            elif code == "-1":
                return errno(unit, test)

        return 0
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output) from e


def errno(unit, test=False) -> bool:
    argument1 = "vpn" + "_" + "client" + unit + "_" + "errno"
    try:
        pprint("/bin/nvram" + " " + "get" + " " + argument1)
        if not test:
            client_errno = subprocess.run(["/bin/nvram", "get", argument1], check=True, stdout=subprocess.PIPE).stdout
            code = client_errno.decode("utf-8").strip()
            if code == "1":
                logger.error("Error - IP conflict!")
            elif code == "2":
                logger.error("Error - Routing conflict!")
            elif code == "4":
                logger.error("Error - SSL/TLS issue!")
            elif code == "5":
                logger.error("Error - DH issue!")
            elif code == "6":
                logger.error("Error - Authentication failure!")
            else:
                logger.error("Error - check configuration!")

        return 1
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output) from e


def pprint(msg, debug=False):
    if debug:
        logger.debug(msg)
