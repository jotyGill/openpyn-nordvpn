# openpyn
A python3 script to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly connect to the least busy servers (by grabbing current data from Nordvpn's website) and the ones that have the lowest latency from you. It Tunnels DNS traffic through the VPN which normally (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a thirdparty) and completely compromises Privacy!

## Features
* Automatically connect to least busy, low latency servers in a given country.
* Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
* Use Iptable rules to prevent leakage if tunnel breaks (Experimental).
* Quickly Connect to any specific server. i.e au10 or us20.
* Downloads and Updates (modifications) the latest config files from NordVPN.
* Option to run the script in the background (requires "sudo ./openpyn.py").
* Options to finetune server selection based on "Server Load" or "Ping Latency".
* Excludes the servers that don't support OpenVPN (TCP or UDP depending upon which one you are trying to use)
* Finds and displays nord vpn servers (with extra info) in a given country.
* Country codes mapping for all countries that host servers by Nord (to use 'us','uk' instead of full names).

## Instructions
1. Clone this repo to a desired location:
``` bash
$ git clone https://github.com/jotyGill/openpyn-nordvpn.git
$ cd openpyn-nordvpn
```
2. Install the dependencies if they are not already present.
``` bash
  $ sudo apt install openvpn
  $ sudo pip install requests
  $ sudo pip install beautifulsoup4   #Completely optional Only needed with '--updateCountries'
```
3. Create a "pass.txt" in the root of openpyn with openvpn compatible "auth-user-pass" file format.
``` bash
  youruser@name.com    #first line
  yourpass   #second line
```
4. Download/Update the latest vpn config files from NordVPN by:
``` bash
  $ ./openpyn.py --update
```
5. That's it, run the script! when done with it, press "Ctr + C" to exit.

## Basic Usage
* At minimum, you only need to specifiy the countryCode, default port is TCP-443, If you want to use
UDP-1194 instead, use "-u" switch.
``` bash
  ./openpyn.py us -u
```
* To enforce Firewall rules to prevent dns leakage, also from ip leakage if tunnel breaks.
``` bash
  ./openpyn.py us -f # Warning clears IPtables rules!
```
* To list all the Countries and their Country Codes where NordVPN hosts servers.
``` bash
  ./openpyn.py -ls
```
* To quickly connect to a specific server.
``` bash
  ./openpyn.py -s au10
```
* To find information about (display) the available servers in a given country.
``` bash
  ./openpyn.py -d uk
```
* To find the least loaded 10 NordVPN servers in US and connect to one of the top 2 servers that
have the lowest latency from you.
``` bash
  ./openpyn.py us -t 10 -tt 2
```
* To run the script in background (after it initiates the connection)
``` bash
  sudo ./openpyn.py us -b #needs sudo to use openvpn
```
* To kill a running openvpn connection (background or shell window).
``` bash
  sudo ./openpyn.py -k  # Warning clears IPtables rules!
```

## Usage Options
``` bash
usage: openpyn.py [-h] [-s SERVER] [-u] [-c COUNTRYCODE] [-b] [-l LOADTHRESHOLD] [-t TOPSERVERS]
[-p PINGS] [-tt TOPPESTSERVERS] [-k] [--updateCountries] [-ls] [--update] [country]

A python3 script to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly connect to the least busy servers (by grabbing current data from Nordvpn's website) and the ones that have the lowest latency from you. It Tunnels DNS traffic through the VPN which otherwise would go through your ISP!

positional arguments:
  country               Country Code can also be speficied without "-c," i.em"./openpyn.py au"

optional arguments:
  -h, --help            show this help message and exit

  -s SERVER, --server SERVER
                        server name, i.e. ca64 or au10

  -u, --udp             use port UDP-1194 instead of the default TCP-443

  -c COUNTRYCODE, --countryCode COUNTRYCODE
                        Specifiy Country Code with 2 letters i.e au

  -b, --background      Run script in the background

  -d COUNTRYCODE, --display COUNTRYCODE
                        Display servers and info about them in a given country

  -l LOADTHRESHOLD, --loadThreshold LOADTHRESHOLD
                        Specifiy load threashold, rejects servers with more
                        load than this, DEFAULT=70

  -t TOPSERVERS, --topServers TOPSERVERS
                        Specifiy the number of Top Servers to choose from the
                        NordVPN\'s Sever list for the given Country, These will
                        be Pinged. DEFAULT=6

  -p PINGS, --pings PINGS
                        Specifiy number of pings to be sent to each server to
                        determine quality, DEFAULT=5

  -tt TOPPESTSERVERS, --toppestServers TOPPESTSERVERS
                        After ping tests the final server count to randomly
                        choose a server from, DEFAULT=3

  -k, --kill            Kill any running Openvnp process, very usefull to kill
                        openpyn process running in background with "-b" switch

  --updateCountries     Fetch the latest countries from nord's site and update
                        the country code mappings

  -ls, --listCountries  List all the countries, with Country Codes to Use

  -f, ----forceFW       Enfore Firewall rules to drop traffic when tunnel breaks
                        Force disable DNS traffic going to any other interface

  --update              Fetch the latest config files from nord\'s site
  ```
