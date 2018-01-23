import subprocess
import os
import json
from openpyn.converter import Converter, T_CLIENT
from openpyn import api


def run(server, country_code, client="1", compression="adaptive", adns="Strict", tcp=False, test=False, debug_mode=False):
    with open("/opt/usr/share/openpyn/credentials", 'r') as f:
        lines = f.read().splitlines()
        f.close()

    url = "https://api.nordvpn.com/server"
    json_response = api.get_json(url)
    for res in json_response:
        if res["domain"][:2].lower() == country_code.lower():
            country_name = res["country"]
            break

    port = "udp1194"
    port_name = "1194"
    protocol_name = "udp"
    if tcp:
        port = "tcp443"
        port_name = "443"
        protocol_name = "tcp-client"

    vpn_config_file = server + ".nordvpn.com." + port + ".ovpn"

    c = Converter(debug_mode)
    c.set_username(lines[0])
    c.set_password(lines[1])
    c.set_description(country_name)
    c.set_port(port_name)
    c.set_protocol(protocol_name)

    c.set_name(server)
    c.set_source_folder("/opt/usr/share/openpyn/files/")
    c.set_certs_folder("/jffs/openvpn/")

    c.set_accept_dns_configuration(adns)
    c.set_compression(compression)
    c.set_client(client)

    extracted_info = c.extract_information(vpn_config_file)
    if not test:
        c._write_certificates(client)

    c.pprint(extracted_info)

    # 'vpn_client_unit'
    key = ""
    value = ""
    unit = ""
    service = "client"

    for key, value in extracted_info.items():
        set(c, key, value, unit, service, test)

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
        set(c, key, value, unit, service, test)

    # 'vpn_upload_unit'
    key = T_CLIENT
    value = client
    unit = ""
    service = "upload"

    set(c, key, value, unit, service, test)

def set(c, key, value, unit, service, test=False):
    argument1 = "vpn" + "_" + service + unit + "_" + key
    argument2 = argument1 + "=" + value
    try:
        c.pprint("/bin/nvram" + " " + "get" + " " + argument1)
        if not test:
            current = subprocess.run(["/bin/nvram", "get", argument1], check=True, stdout=subprocess.PIPE).stdout
            if current.decode('utf-8').strip() == value:
                return
        c.pprint("/bin/nvram" + " " + "set" + " " + argument2)
        if not test:
            subprocess.run(["sudo", "/bin/nvram", "set", argument2], check=True)
            pass
    except subprocess.CalledProcessError as e:
        print(e.output)
