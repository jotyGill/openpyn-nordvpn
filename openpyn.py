#!/usr/bin/python3

import subprocess
import argparse
import requests
import operator
import random
import os.path
import json
import sys

# @todo uninstall.sh
# @todo find and display server's locations (cities)
# @todo create a combined config of server list(on fly) for failover

countryDic = {}
with open("/usr/share/openpyn/country-mappings.json", 'r') as countryMappingsFile:
    countryDic = json.load(countryMappingsFile)
    countryMappingsFile.close()


def main(
    server, countryCode, country, udp, background, loadThreshold, topServers,
        pings, toppestServers, kill, killFW, update, display, updateCountries,
        listCountries, forceFW):

    port = "tcp443"
    if udp:
        port = "udp1194"

    if kill:
        killVpnProcesses()  # dont touch iptable rules
        sys.exit()
    elif killFW:
        killVpnProcesses()
        clearFWRules()      # also clear iptable rules
        sys.exit()
    elif update:
        updateOpenpyn()
        sys.exit()
    elif display is not None:
        displayServers(display)
    elif updateCountries:
        updateCountryCodes()
    elif listCountries:
        listAllCountries()
    # only clear/touch FW Rules if "-f" used
    elif forceFW:
        clearFWRules()

    # if only "-c" used then
    if countryCode is None and server is None:
        countryCode = country
    # if either "-c" or positional arg f.e "au" is present
    if countryCode:
        countryCode = countryCode.lower()
        betterServerList = findBetterServers(countryCode, loadThreshold, topServers, udp)
        pingServerList = pingServers(betterServerList, pings)
        chosenServer = chooseBestServer(pingServerList, toppestServers)
        # if "-f" used appy Firewall rules
        if forceFW:
            networkInterfaces = findInterfaces()
            vpnServerIp = findVpnServerIP(chosenServer, port)
            applyFirewallRules(networkInterfaces, vpnServerIp)
        connection = connect(chosenServer, port, background)
    elif server:
        server = server.lower()
        # if "-f" used appy Firewall rules
        if forceFW:
            networkInterfaces = findInterfaces()
            vpnServerIp = findVpnServerIP(server, port)
            applyFirewallRules(networkInterfaces, vpnServerIp)
        connection = connect(server, port, background)
    else:
        parser.print_help()
        sys.exit()


def getData(countryCode=None, countryName=None):
    jsonResList = []
    if countryName is not None:
        countryCode = countryName
    else:
        countryCode = countryDic[countryCode]
    url = "https://nordvpn.com/wp-admin/admin-ajax.php?group=Standard+VPN\
    +servers&country=" + countryCode + "&action=getGroupRows"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers).json()
    except HTTPError as e:  # @todo ask for server instead
        print("Cannot GET the json from nordvpn.com, Manually Specifiy a Server\
        using '-s' for example '-s au10'")
        sys.exit()
    for i in response:
        jsonResList.append(i)
    return jsonResList


def findBetterServers(countryCode, loadThreshold, topServers, udp):
    jsonResList = getData(countryCode=countryCode)
    serverList = []
    betterServerList = []

    for res in jsonResList:
        # only add if the server is online
        if res["exists"] is True:
            # when connecting using UDP only append if it supports OpenVPN-UDP
            if udp is True and res["feature"]["openvpn_udp"] is True:
                serverList.append([res["short"], res["load"]])
                # print("UDP SERVESR :", res["feature"], res["feature"]["openvpn_udp"])
            # when connecting using TCP only append if it supports OpenVPN-TCP
            elif udp is False and res["feature"]["openvpn_tcp"] is True:
                serverList.append([res["short"], res["load"]])
                # print("TCP SERVESR :", res["feature"], res["feature"]["openvpn_tcp"])

    # sort list by the server load
    serverList.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in serverList:
        serverLoad = int(server[1])
        if serverLoad < loadThreshold and len(betterServerList) < topServers:
            betterServerList.append(server)
    if udp:
        usedProtocol = "OPENVPN-UDP"
    else:
        usedProtocol = "OPENVPN-TCP"
    print("According to NordVPN, Least Busy " + str(len(betterServerList)) + " Servers, In",
          countryCode.upper(), "With 'Load' less than", loadThreshold,
          "Which Support", usedProtocol, "are :", betterServerList)
    return betterServerList


def pingServers(betterServerList, ping):
    pingServerList = []
    for i in betterServerList:
        # tempList to append 2  lists into it
        tempList = []
        try:
            pingP = subprocess.Popen(["ping", i[0] + ".nordvpn.com", "-i", ".2", "-c", ping], stdout=subprocess.PIPE)
            # pipe the output of ping to grep.
            pingOut = subprocess.check_output(("grep", "min/avg/max/mdev"), stdin=pingP.stdout)
        except subprocess.CalledProcessError as e:
            print("Ping Failed to :", i[0], "Skipping it")
            continue
        pingString = str(pingOut)
        pingString = pingString[pingString.find("= ") + 2:]
        pingString = pingString[:pingString.find(" ")]
        pingList = pingString.split("/")
        # change str values in pingList to ints
        pingList = list(map(float, pingList))
        pingList = list(map(int, pingList))
        print("Pinging Server " + i[0] + " min/avg/max/mdev = ", pingList)
        tempList.append(i)
        tempList.append(pingList)
        pingServerList.append(tempList)
    # sort by Ping Avg and Median Deveation
    pingServerList = sorted(pingServerList, key=lambda item: (item[1][1], item[1][3]))
    return pingServerList


def chooseBestServer(pingServerList, toppestServers):
    bestServersList = []
    bestServersNameList = []

    # 5 top servers or if less than 5 totel servers
    for serverCounter in range(toppestServers):
        if serverCounter < len(pingServerList):
            bestServersList.append(pingServerList[serverCounter])
            serverCounter += 1
    # populate bestServerList
    for i in bestServersList:
        bestServersNameList.append(i[0][0])

    print("Top " + str(len(bestServersList)) + " Servers with best Ping are:", bestServersNameList)
    chosenServerList = bestServersList[random.randrange(0, len(bestServersList))]
    chosenServer = chosenServerList[0][0]  # the first value, "server name"
    print("Out of the Best Available Servers, Randomly Selected ", chosenServer,
          "with Ping of  min/avg/max/mdev = ", chosenServerList[1])
    return chosenServer


def killVpnProcesses():
    try:
        print("Killing any running openvpn processes")
        openvpnProcesses = subprocess.check_output(["pgrep", "openvpn"])
        # When it returns "0", proceed
        subprocess.run(["sudo", "killall", "openvpn"])
    except subprocess.CalledProcessError as ce:
        # when Exception, the openvpnProcesses issued non 0 result, "not found"
        print("No openvpn process found")
        return


def clearFWRules():
    print("Flushing iptables INPUT and OUTPUT chains AND Applying defualt Rules")
    subprocess.run(["sudo", "iptables", "-F", "OUTPUT"])
    # allow all outgoing traffic
    subprocess.run("sudo iptables -P OUTPUT ACCEPT", shell=True)

    subprocess.run(["sudo", "iptables", "-F", "INPUT"])
    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"])
    subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"])
    subprocess.run("sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT", shell=True)
    # best practice, stops spoofing
    subprocess.run("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP", shell=True)
    # drop anything else incoming
    subprocess.run("sudo iptables -P INPUT DROP", shell=True)
    return


def updateOpenpyn():
    try:
        subprocess.run(["sudo", "wget", "-N", "https://nordvpn.com/api/files/zip", "-P", "/usr/share/openpyn/"])
        subprocess.run(["sudo", "unzip", "-u", "-o", "/usr/share/openpyn/zip", "-d", "/usr/share/openpyn/files/"])
        subprocess.run(["sudo", "rm", "/usr/share/openpyn/zip"])
    except subprocess.CalledProcessError:
        print("Exception occured while wgetting zip")


def displayServers(display):
    jsonResList = getData(countryCode=display)
    fromWebset = set()      # servers shown on the website
    serversSet = set()      # servers from .openvpn files
    newServersset = set()   # new Servers, not published on website yet
    print("The NordVPN Servers In", display.upper(), "Are :")
    for res in jsonResList:
        print("Server =", res["short"], ", Load =", res["load"], ", Country =",
              res["country"], ", OpenVPN TCP Support =", res["feature"]["openvpn_tcp"],
              ", OpenVPN UDP Support =", res["feature"]["openvpn_udp"], '\n')
        fromWebset.add(res["short"])
    serverFiles = subprocess.check_output("ls /usr/share/openpyn/files/" + display + "*", shell=True)
    serverFilesStr = str(serverFiles)
    serverFilesStr = serverFilesStr[2:-3]
    serverFilesList = serverFilesStr.split("\\n")
    for item in serverFilesList:
        serverName = item[item.find("files/") + 6:item.find(".")]
        serversSet.add(serverName)
    print("The following server (if any) have not even been listed on the nord's site yet",
          "they usally are the fastest or Dead.\n")
    for item in serversSet:
        if item not in fromWebset:
            newServersset.add(item)
    print(newServersset)
    sys.exit()


def updateCountryCodes():
    from bs4 import BeautifulSoup

    countryNames = set()
    countryMappings = {}
    url = "https://nordvpn.com/servers/"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers)
    except HTTPError as e:  # @todo ask for server instead
        print("Cannot GET")

    try:
        bsObj = BeautifulSoup(response.text, "html.parser")
    except AttributeError as e:
        print("html.parser CANT parse the URL's text")

    for ref in bsObj.find_all('span', {"class": "country-name hidden-xs"}):
        countryNames.add((ref.get_text()).strip())
    print("Updating Country Code Mappings: \n")
    for eachCountry in countryNames:
        jsonResList = getData(countryName=eachCountry)
        print(jsonResList[0]["short"][0:2], jsonResList[0]["country"])
        countryMappings.update({jsonResList[0]["short"][0:2]: jsonResList[0]["country"]})
    with open("/usr/share/openpyn/country-mappings.json", 'w') as countryMappingsFile:
        json.dump(countryMappings, countryMappingsFile)
        countryMappingsFile.close()
    sys.exit()


def listAllCountries():
    for key in countryDic.keys():
        print("Full Name : " + countryDic[key] + "      Country Code : " + key + '\n')
    sys.exit()


def findInterfaces():
    interfaceList = []
    interfaceDetailsList = []

    interfaces = subprocess.check_output("ls /sys/class/net", shell=True)
    interfaceString = str(interfaces)
    interfaceString = interfaceString[2:-3]
    interfaceList = interfaceString.split('\\n')

    for interface in interfaceList:
        showInterface = subprocess.check_output(["ip", "addr", "show", interface])
        showInterfaceStr = str(showInterface)
        ipaddress = showInterfaceStr[showInterfaceStr.find("inet") + 5:]
        ipaddress = ipaddress[:ipaddress.find(" ")]

        showInterfaceStr = showInterfaceStr[5:showInterfaceStr.find(">")+1]
        showInterfaceStr = showInterfaceStr.replace(":", "").replace("<", "").replace(">", "")

        showInterfaceList = showInterfaceStr.split(" ")
        if ipaddress != "":
            showInterfaceList.append(ipaddress)
        interfaceDetailsList.append(showInterfaceList)
    return interfaceDetailsList


def findVpnServerIP(server, port):
    # grab the ip address of vpnserver from the config file
    fullPath = "/usr/share/openpyn/files/" + server + ".nordvpn.com." + port + ".ovpn"
    with open(fullPath, 'r') as configFile:
        for line in configFile:
            if "remote " in line:
                vpnServerIp = line[7:]
                vpnServerIp = vpnServerIp[:vpnServerIp.find(" ")]
        configFile.close()
        return vpnServerIp


def applyFirewallRules(interfaceDetailsList, vpnServerIp):
    # Empty the INPUT and OUTPUT chain of any current rules
    subprocess.run(["sudo", "iptables", "-F", "OUTPUT"])
    subprocess.run(["sudo", "iptables", "-F", "INPUT"])

    # Allow all traffic out over the vpn tunnel
    subprocess.run("sudo iptables -A OUTPUT -o tun+ -j ACCEPT", shell=True)
    # accept traffic that comes through tun that you connect to
    subprocess.run("sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -i tun+ -j ACCEPT", shell=True)
    for interface in interfaceDetailsList:

        # if interface is active with an IP in it, don't send DNS requests to it
        if len(interface) == 3 and "tun" not in interface[0]:
            subprocess.run(
                ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-p",
                    "udp", "--destination-port", "53", "-j", "DROP"])
            # subprocess.run(
            #     ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-p",
            #         "tcp", "--destination-port", "53", "-j", "DROP"])
            if interface[0] != "lo":
                # allow access to vpnServerIp
                subprocess.run(
                    ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-d", vpnServerIp, "-j", "ACCEPT"])
                # talk to the vpnServer ip to connect to it
                subprocess.run(
                    ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                        "--ctstate", "ESTABLISHED,RELATED", "-i", interface[0], "-s", vpnServerIp, "-j", "ACCEPT"])

                # allow access to internal ip range
                # print("internal ip with range", interface[2])
                subprocess.run(
                    ["sudo", "iptables", "-A", "OUTPUT", "-o", interface[0], "-d",
                        interface[2], "-j", "ACCEPT"])
                subprocess.run(
                    ["sudo", "iptables", "-A", "INPUT", "-m", "conntrack",
                        "--ctstate", "ESTABLISHED,RELATED", "-i", interface[0], "-s", interface[2], "-j", "ACCEPT"])

    # Allow loopback traffic
    subprocess.run("sudo iptables -A INPUT -i lo -j ACCEPT", shell=True)
    subprocess.run("sudo iptables -A OUTPUT -o lo -j ACCEPT", shell=True)

    # best practice, stops spoofing
    subprocess.run("sudo iptables -A INPUT -s 127.0.0.0/8 -j DROP", shell=True)

    # Default action if no other rules match
    subprocess.run("sudo iptables -P OUTPUT DROP", shell=True)
    subprocess.run("sudo iptables -P INPUT DROP", shell=True)
    return


def connect(server, port, background):
    killVpnProcesses()   # kill existing openvpn processes
    print("CONNECTING TO SERVER", server, " ON PORT", port)
    osIsDebianBased = os.path.isfile("/sbin/resolvconf")
    # osIsDebianBased = False
    if osIsDebianBased:  # Debian Based OS
        # tunnel dns throught vpn by changing /etc/resolv.conf using
        # "update-resolv-conf.sh" to change the dns servers to NordVPN's.
        if background:
            subprocess.Popen(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass",
                    "/usr/share/openpyn/creds", "--script-security", "2",
                    "--up", "/usr/share/openpyn/update-resolv-conf.sh",
                    "--down", "/usr/share/openpyn/update-resolv-conf.sh", "--daemon"])
        else:
            subprocess.run(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass",
                    "/usr/share/openpyn/creds", "--script-security", "2",
                    "--up", "/usr/share/openpyn/update-resolv-conf.sh",
                    "--down", "/usr/share/openpyn/update-resolv-conf.sh"])

    else:       # If not Debian Based
        print("NOT DEBIAN BASED OS ('/sbin/resolvconf' not Found): Mannully Applying Patch to Tunnel DNS Through " +
              "The VPN Tunnel By Modifying '/etc/resolv.conf'")
        dnsPatch = subprocess.run(
            ["sudo", "/usr/share/openpyn/manual-dns-patch.sh"])

        if background:
            subprocess.Popen(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn",
                    "--auth-user-pass", "/usr/share/openpyn/creds", "--daemon"])
        else:
            subprocess.run(
                ["sudo", "openvpn", "--redirect-gateway", "--config", "/usr/share/openpyn/files/"
                    + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass",
                    "/usr/share/openpyn/creds"])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="A python3 script to easily connect to and switch between, OpenVPN \
        servers hosted by NordVPN. Quickly Connect to the least busy servers (using current \
        data from Nordvpn website) with lowest latency from you. Tunnels DNS traffic through \
        the VPN which normally (when using OpenVPN with NordVPN) goes through your ISP's DNS \
        (still unencrypted, even if you use a thirdparty) and completely compromises Privacy!")
    parser.add_argument(
        '-s', '--server', help='server name, i.e. ca64 or au10',)
    parser.add_argument(
        '-u', '--udp', help='use port UDP-1194 instead of the default TCP-443',
        action='store_true')
    parser.add_argument(
        '-c', '--countryCode', type=str, help='Specifiy Country Code with 2 letters, i.e au,')
    # use nargs='?' to make a positional arg optinal
    parser.add_argument(
        'country', nargs='?', help='Country Code can also be speficied without "-c,"\
         i.e "openpyn au"')
    parser.add_argument(
        '-b', '--background', help='Run script in the background',
        action='store_true')
    parser.add_argument(
        '-l', '--loadThreshold', type=int, default=70, help='Specifiy load threashold, \
        rejects servers with more load than this, DEFAULT=70')
    parser.add_argument(
        '-t', '--topServers', type=int, default=6, help='Specifiy the number of Top \
         Servers to choose from the NordVPN\'s Sever list for the given Country, These will be \
         Pinged. DEFAULT=6')
    parser.add_argument(
        '-p', '--pings', type=str, default="5", help='Specifiy number of pings \
        to be sent to each server to determine quality, DEFAULT=5')
    parser.add_argument(
        '-tt', '--toppestServers', type=int, default=3, help='After ping tests \
        the final server count to randomly choose a server from, DEFAULT=3')
    parser.add_argument(
        '-k', '--kill', help='Kill any running Openvnp process, very usefull \
        to kill openpyn process running in background with "-b" switch',
        action='store_true')
    parser.add_argument(
        '-kf', '--killFW', help='Kill any running Openvnp process, AND Flush Iptables',
        action='store_true')
    parser.add_argument(
        '--update', help='Fetch the latest config files from nord\'s site',
        action='store_true')
    parser.add_argument(
        '--updateCountries', help='Fetch the latest countries from nord\'s site\
        and update the country code mappings', action='store_true')
    parser.add_argument(
        '-d', '--display', type=str, help='Display all servers in a given country\
        with their loadThreshold')
    parser.add_argument(
        '-ls', '--listCountries', help='List all the countries, with Country \
        Codes to Use', action='store_true')
    parser.add_argument(
        '-f', '--forceFW', help='Enfore Firewall rules to drop traffic when tunnel breaks\
        , Force disable DNS traffic going to any other interface', action='store_true')

    args = parser.parse_args()

    main(
        args.server, args.countryCode, args.country, args.udp, args.background,
        args.loadThreshold, args.topServers, args.pings, args.toppestServers,
        args.kill, args.killFW, args.update, args.display, args.updateCountries, args.listCountries,
        args.forceFW)
