#!/usr/bin/python3

import subprocess
import argparse
import requests
import operator
import random

# @todo dynamic files lcation
# @todo work arround, when used '-b' without 'sudo'
# @todo update files on the fly


def main(
    server, countryCode, country, udp, background, loadThreshold,
        topServers, pings, toppestServers, kill, update):
    port = "tcp443"
    if udp:
        port = "udp1194"

    if kill:
        killProcess()
        exit()
    elif update:
        updateOpenpyn()
        exit()

    # if only "-c" used then
    if countryCode is None and server is None:
        countryCode = country
    # not if both "-c" or positional arg are present
    if countryCode:
        countryCode = countryCode.lower()
        betterServerList = findBetterServers(countryCode, loadThreshold, topServers)
        pingServerList = pingServers(betterServerList, pings)
        chosenServer = chooseBestServer(pingServerList, toppestServers)
        connection = connect(chosenServer, port, background)
    elif server:
        server = server.lower()
        connection = connect(server, port, background)


def findBetterServers(countryCode, loadThreshold, topServers):
    serverList = []
    betterServerList = []
    countryDic = {
        'au': 'Australia', 'ca': 'Canada', 'at': 'Austria', 'be': 'Belgium',
        'ba': 'Brazil', 'de': 'Germany', 'fr': 'France', 'fi': 'Finland',
        'uk': 'United Kingdom', 'nl': 'Netherlands', 'se': 'Sweden', 'us': 'United States'}
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
        # only add if the server is online
        if i["exists"] is True:
            serverList.append([i["short"], i["load"]])

    # sort list by the server load
    serverList.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in serverList:
        serverLoad = int(server[1])
        if serverLoad < loadThreshold and len(betterServerList) < topServers:
            betterServerList.append(server)

    print("According to NordVPN least busy " + str(topServers) + " Servers in ",
          countryCode, "are :", betterServerList)
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

    print("Top " + str(toppestServers) + " Servers with best Ping are:", bestServersNameList)
    chosenServerList = bestServersList[random.randrange(0, len(bestServersList))]
    chosenServer = chosenServerList[0][0]  # the first value, "server name"
    print("Out of the Best Available Servers, Randomly Selected ", chosenServer,
          "with Ping of  min/avg/max/mdev = ", chosenServerList[1])
    return chosenServer


def killProcess():
    try:
        openvpnProcesses = subprocess.check_output(["pgrep", "openvpn"])
        print("killing running openvpn processes")
        subprocess.run(["sudo", "killall", "openvpn"])
    except subprocess.CalledProcessError as ce:
        # when Exception, the openvpnProcesses issued non 0 result, "not found"
        print("No openvpn process found")
    # if openvpnProcesses != "openvpn: no process found":


def updateOpenpyn():
    try:
        subprocess.run(["wget", "https://nordvpn.com/api/files/zip"])
        subprocess.run(["unzip", "-u", "-o", "zip", "-d", "./files/"])
    except subprocess.CalledProcessError:
        print("Exception occured while wgetting zip")


def connect(server, port, background):
    print("CONNECTING TO SERVER", server, " ON PORT", port)

    killProcess()   # killing existing openvpn processes
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
        '-c', '--countryCode', type=str, help='Specifiy Country Code with 2 letter name, i.e au,\
         A server among the top 5 servers will be used automatically.')
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
        '-t', '--topServers', type=int, default=10, help='Specifiy the number of Top \
         Servers to choose from the NordVPN\'s Sever list for the given Country, These will be \
         Pinged. DEFAULT=10')
    parser.add_argument(
        '-p', '--pings', type=str, default="10", help='Specifiy number of pings \
        to be sent to each server to determine quality, DEFAULT=10')
    parser.add_argument(
        '-tt', '--toppestServers', type=int, default=5, help='After ping tests \
        the final server count to randomly choose a server from, DEFAULT=5')
    parser.add_argument(
        '-k', '--kill', help='Kill any running Openvnp process, very usefull \
        to kill openpyn process running in background with "-b" switch',
        action='store_true')
    parser.add_argument(
        '--update', help='Fetch the latest config files from nord\'s site',
        action='store_true')

    args = parser.parse_args()

    main(
        args.server, args.countryCode, args.country, args.udp, args.background,
        args.loadThreshold, args.topServers, args.pings,
        args.toppestServers, args.kill, args.update)
