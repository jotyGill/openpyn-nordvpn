import logging
import subprocess

import verboselogs

from openpyn import __basefilepath__, api
from openpyn.converter import T_CLIENT, Converter

verboselogs.install()
logger = logging.getLogger(__package__)


def run(server, c_code, client, rgw=None, comp=None, adns=None, tcp=False, test=False, debug=False):
    with open(__basefilepath__ + "credentials", 'r') as f:
        lines = f.read().splitlines()
        f.close()

    url = "https://api.nordvpn.com/server"
    json_response = api.get_json(url)
    for res in json_response:
        if res["domain"][:2].lower() == c_code.lower():
            country_name = res["country"]
            break

    port = "udp"
    port_name = "1194"
    protocol_name = "udp"
    folder = "ovpn_udp/"
    if tcp:
        port = "tcp"
        port_name = "443"
        protocol_name = "tcp-client"
        folder = "ovpn_tcp/"

    vpn_config_file = server + ".nordvpn.com." + port + ".ovpn"

    c = Converter(debug)
    c.set_username(lines[0])
    c.set_password(lines[1])
    c.set_description("Client" + " " + country_name)
    c.set_port(port_name)
    c.set_protocol(protocol_name)

    c.set_name(server)
    c.set_source_folder(__basefilepath__ + "files/" + folder)
    c.set_certs_folder("/jffs/openvpn/")

    c.set_accept_dns_configuration(adns)
    c.set_compression(comp)
    c.set_redirect_gateway(rgw)
    c.set_client(client)

    extracted_info = c.extract_information(vpn_config_file)
    if not test:
        c.write_certificates(client)

    c.pprint(extracted_info)

    # 'vpn_client_unit'
    key = ""
    value = ""
    unit = ""
    service = "client"

    for key, value in extracted_info.items():
        write(c, key, value, unit, service, test)

    extracted_info = dict(extracted_info)
    if T_CLIENT in extracted_info:
        del extracted_info[T_CLIENT]

    c.pprint(extracted_info)

    # 'vpn_client_unit$'
    key = ""
    value = ""
    unit = client
    service = "client"

    for key, value in extracted_info.items():
        write(c, key, value, unit, service, test)

    # 'vpn_upload_unit'
    key = T_CLIENT
    value = client
    unit = ""
    service = "upload"

    write(c, key, value, unit, service, test)


def write(c, key, value, unit, service, test=False):
    argument1 = "vpn" + "_" + service + unit + "_" + key
    argument2 = argument1 + "=" + value
    try:
        c.pprint("/bin/nvram" + " " + "get" + " " + argument1)
        if not test:
            current = subprocess.run(["/bin/nvram", "get", argument1],
                                     check=True, stdout=subprocess.PIPE).stdout
            if current.decode('utf-8').strip() == value:
                return
        c.pprint("/bin/nvram" + " " + "set" + " " + argument2)
        if not test:
            subprocess.run(["sudo", "/bin/nvram", "set", argument2], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(e.output)
