#!/usr/bin/python3

import subprocess
import argparse
import requests
import operator
import random
import os.path

# @todo install.sh
# @todo work arround, when used '-b' without 'sudo'
# @todo check for openvpn tcp and udp support on servers()
# @todo find and display server's locations (cities)
# @todo utilise iptables to ensure no ip leakage when reconnecting.
# @todo create a combined config of server list(on fly) for failover


countryDic = {
    'au': 'Australia', 'ca': 'Canada', 'at': 'Austria', 'be': 'Belgium',
    'ba': 'Brazil', 'de': 'Germany', 'fr': 'France', 'fi': 'Finland',
    'uk': 'United Kingdom', 'nl': 'Netherlands', 'se': 'Sweden', 'us': 'United States'}


def main(
    server, countryCode, country, udp, background, loadThreshold,
        topServers, pings, toppestServers, kill, update, display):

    port = "tcp443"
    if udp:
        port = "udp1194"

    if kill:
        killProcess()
        exit()
    elif update:
        updateOpenpyn()
        exit()
    elif display is not None:
        displayServers(display)

    # if only "-c" used then
    if countryCode is None and server is None:
        countryCode = country
    # if either "-c" or positional arg f.e "au" is present
    if countryCode:
        countryCode = countryCode.lower()
        betterServerList = findBetterServers(countryCode, loadThreshold, topServers)
        pingServerList = pingServers(betterServerList, pings)
        chosenServer = chooseBestServer(pingServerList, toppestServers)
        connection = connect(chosenServer, port, background)
    elif server:
        server = server.lower()
        connection = connect(server, port, background)


def getData(countryCode):
    jsonResList = []
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
        exit()
    for i in response:
        jsonResList.append(i)
    return jsonResList


def findBetterServers(countryCode, loadThreshold, topServers):
    jsonResList = getData(countryCode)
    serverList = []
    betterServerList = []

    for res in jsonResList:
        # only add if the server is online
        if res["exists"] is True:
            serverList.append([res["short"], res["load"]])

    # sort list by the server load
    serverList.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in serverList:
        serverLoad = int(server[1])
        if serverLoad < loadThreshold and len(betterServerList) < topServers:
            betterServerList.append(server)

    print("According to NordVPN least busy " + str(len(betterServerList)) + " Servers, in",
          countryCode, "with Load less than", loadThreshold, "are :", betterServerList)
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


def killProcess():
    try:
        print("Killing any running openvpn processes")
        openvpnProcesses = subprocess.check_output(["pgrep", "openvpn"])
        # When it returns "0", proceed
        subprocess.run(["sudo", "killall", "openvpn"])
    except subprocess.CalledProcessError as ce:
        # when Exception, the openvpnProcesses issued non 0 result, "not found"
        print("No openvpn process found")


def updateOpenpyn():
    try:
        subprocess.run(["wget", "-N", "https://nordvpn.com/api/files/zip"])
        subprocess.run(["unzip", "-u", "-o", "zip", "-d", "./files/"])
        subprocess.run(["rm", "zip"])
    except subprocess.CalledProcessError:
        print("Exception occured while wgetting zip")


def displayServers(display):
    jsonResList = getData(display)
    # print server info
    for res in jsonResList:
        print("Server =", res["short"], ", Load =", res["load"], ", Country =",
              res["country"], ", Location =", res["location"])
    exit()


def connect(server, port, background):
    print("CONNECTING TO SERVER", server, " ON PORT", port)
    killProcess()   # kill existing openvpn processes
    osIsDebianBased = os.path.isfile("/sbin/resolvconf")
    osIsDebianBased = False
    if osIsDebianBased:  # Debian Based OS
        # tunnel dns throught vpn by changing /etc/resolv.conf using
        # "update-resolv-conf.sh" to change the dns servers to NordVPN's.
        if background:
            subprocess.Popen(
                ["sudo", "openvpn", "--config", "./files/" + server + ".nordvpn.com."
                    + port + ".ovpn", "--auth-user-pass", "pass.txt", "--script-security", "2",
                    "--up ./update-resolv-conf.sh",
                    "--down ./update-resolv-conf.sh"])
        else:
            subprocess.run(
                ["sudo", "openvpn", "--config", "./files/" + server + ".nordvpn.com."
                    + port + ".ovpn", "--auth-user-pass", "pass.txt", "--script-security", "2",
                    "--up", "./update-resolv-conf.sh",
                    "--down", "./update-resolv-conf.sh"], stdin=subprocess.PIPE)

    else:       # If not Debian Based
        print("NOT DEBAIN BASED OS: MAKE SURE RUNNING AS SUDO!! \
            TO PATCH DNS LEAKS To Manually Change '/etc/resolv.conf'")
        nordDNS1 = 'sudo echo "nameserver 162.242.211.137" > /etc/resolv.conf'
        nordDNS2 = 'sudo echo "nameserver 78.46.223.24" >> /etc/resolv.conf'
        openDNS3 = 'sudo echo "nameserver 208.67.222.220" >> /etc/resolv.conf'
        subprocess.run(nordDNS1, shell=True)
        subprocess.run(nordDNS2, shell=True)
        subprocess.run(openDNS3, shell=True)
        if background:
            subprocess.Popen(
                ["sudo", "openvpn", "--config", "./files/" + server +
                 ".nordvpn.com." + port + ".ovpn", "--auth-user-pass", "pass.txt"])
        else:
            subprocess.run(
                ["sudo", "openvpn", "--config", "./files/" + server + ".nordvpn.com."
                 + port + ".ovpn", "--auth-user-pass", "pass.txt"], stdin=subprocess.PIPE)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script to Connect to OpenVPN')
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
         i.e "./openpyn.py au"')
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
        '--update', help='Fetch the latest config files from nord\'s site',
        action='store_true')
    parser.add_argument(
        '-d', '--display', type=str, help='Display all servers in a given country\
        with their loadThreshold')

    args = parser.parse_args()

    main(
        args.server, args.countryCode, args.country, args.udp, args.background,
        args.loadThreshold, args.topServers, args.pings,
        args.toppestServers, args.kill, args.update, args.display)
