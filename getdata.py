#!/usr/bin/python3

import requests
import operator

country = 'Australia'
url = "https://nordvpn.com/wp-admin/admin-ajax.php?group=Standard+VPN+servers&country=Australia&action=getGroupRows"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
serverList = []

try:
    response = requests.get(url, headers=headers).json()
except HTTPError as e:
    print("Invalid URL Provided")


for i in response:
    #print(i["short"], i["load"], i["exists"])
    #only add if the server is online
    if i["exists"] == True:
        serverList.append([i["short"], i["load"]])

print(serverList)
serverList.sort(key=operator.itemgetter(1))
print(serverList)
