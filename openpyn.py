#!/usr/bin/python3

import subprocess
import argparse
import requests
import operator
import random

# @todo dynamic files lcation
# @todo kill switch
# @todo ping to determine quality


def main(server, countryCode, udp, background):
    port = "tcp443"
    if udp:
        port = "udp1194"

    if countryCode:
        countryCode = countryCode.lower()
        bestServers = findBestServers(countryCode)
        chosenServer = chooseBestServer(bestServers)
        connection = connect(chosenServer, port, background)
    elif server:
        server = server.lower()
        connection = connect(server, port, background)


def findBestServers(countryCode):
    serverList = []
    betterServerList = []
    countryDic = {
        'au': 'Australia', 'ca': 'Canada', 'at': 'Austria', 'be': 'Belgium',
        'ba': 'Brazil', 'de': 'Germany', 'fr': 'France', 'fi': 'Finland',
        'uk': 'United Kingdom', 'nl': 'Netherlands', 'se': 'Sweden'}
    countryCode = countryDic[countryCode]
    url = "https://nordvpn.com/wp-admin/admin-ajax.php?group=Standard+VPN\
    +servers&country=" + countryCode + "&action=getGroupRows"

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers).json()
    except HTTPError as e:  # @todo ask for server instead
        print("Cannot GET the json from nordvpn.com")

    for i in response:
        # only add if the server is online
        if i["exists"] is True:
            serverList.append([i["short"], i["load"]])

    # sort list by the server load
    serverList.sort(key=operator.itemgetter(1))
    # only choose servers with < 70% load then top 10 of them
    for server in serverList:
        serverLoad = int(server[1])
        if serverLoad < 70 and len(betterServerList) < 10:
            betterServerList.append(server)

    print("Top Servers in ", countryCode, "are :", betterServerList)
    return betterServerList


def chooseBestServer(betterServerList):
    bestServerList = []
    for i in betterServerList:
        # tempList to append 2  lists into it
        tempList = []
        ping = subprocess.Popen(["ping", i[0] + ".nordvpn.com", "-i", ".2", "-c", "10"], stdout=subprocess.PIPE)
        # pipe the output of ping to grep.
        pingOut = subprocess.check_output(("grep", "min/avg/max/mdev"), stdin=ping.stdout)
        pingString = str(pingOut)
        pingString = pingString[pingString.find("= ") + 2:]
        pingString = pingString[:pingString.find(" ")]
        pingList = pingString.split("/")
        # pingAvg = pingList[1]
        # pingMDev = pingList[3]
        tempList.append(i)
        # change str values in pingList to ints
        pingList = list(map(float, pingList))
        pingList = list(map(int, pingList))
        print(pingList)
        tempList.append(pingList)
        bestServerList.append(tempList)
    # sort by Avg and Median Deveation
    bestServerList = sorted(bestServerList, key=lambda item: (item[1][1], item[1][3]))
    bestServerList2 = []

    # 5 top servers or if less than 5 in total
    for serverCounter in range(5):
        if serverCounter < len(bestServerList):
            bestServerList2.append(bestServerList[serverCounter])
            serverCounter += 1


    print("bestServerList: ", bestServerList)
    print("bestServerList2: ", bestServerList2)
    chosenServerList = bestServerList2[random.randrange(0, len(bestServerList2))]
    chosenServer = bestServerList2[0][0][0]  # the first value, "server name"
    return chosenServer


def connect(server, port, background):
    print("CONNECTING TO SERVER", server, port)
    if background:
        subprocess.Popen(["sudo", "openvpn", "--config", "./files/" + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass", "pass.txt"])
    else:
        subprocess.run(["sudo", "openvpn", "--config", "./files/" + server + ".nordvpn.com." + port + ".ovpn", "--auth-user-pass", "pass.txt"], stdin=subprocess.PIPE)


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
    parser.add_argument(
        'countryCode', help='Country Code can also be speficied without "-c"')
    parser.add_argument(
        '-b', '--background', help='Run script in the background',
        action='store_true')

    args = parser.parse_args()

    main(args.server, args.countryCode, args.udp, args.background)
