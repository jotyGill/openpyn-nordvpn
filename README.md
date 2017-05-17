# openpyn
A python3 script to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers (using current data from Nordvpn's website) with lowest latency from you. It Tunnels DNS traffic through the VPN which normally (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a thirdparty) and completely compromises Privacy!

## Features
* Automatically connect to least busy, low latency servers in a given country.
* Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
* Use Iptable rules to prevent leakage if tunnel breaks (Experimental).
* Quickly Connect to any specific server. i.e au10 or us20.
* Downloads and Updates (modifications) the latest config files from NordVPN.
* Option to run the script in background (openvpn daemon mode).
* Options to finetune server selection based on "Server Load" or "Ping Latency".
* Excludes the servers that don't support OpenVPN (TCP or UDP depending upon which one you are trying to use).
* Finds and displays nord vpn servers (with extra info) in a given country.
* Country codes mapping for all countries that host servers by Nord (to use 'us','uk' instead of full names).
* Now list and connect to servers with "Peer To Peer" --p2p, "Dedicated IP" --dedicated, "Tor Over VPN" --tor, \
"Double VPN" --double, "Anti DDos" --anti-ddos support.

## Instructions
1. Clone this repo to a desired location:
``` bash
git clone https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn
```
2. Install dependencies if they are not already present.
``` bash
# dependencies
sudo apt install openvpn
sudo pip install requests     # Or sudo apt install python3-requests
sudo pip install beautifulsoup4   #Completely optional Only needed with '--updateCountries'
```
3. Install the script, and provide credentials to be stored in '/usr/share/openpyn/creds'.
``` bash
sudo ./install.sh
```
4. Download/Update the latest vpn config files from NordVPN by:
``` bash
openpyn --update
```
5. That's it, run the script! when done with it, press "Ctr + C" to exit.

## Basic Usage
* At minimum, you only need to specifiy the countryCode, default port is TCP-443, If you want to use
UDP-1194 instead, use "-u" switch.
``` bash
openpyn us -u
```
* To enforce Firewall rules to prevent dns leakage, also from ip leakage if tunnel breaks.
``` bash
openpyn us -f # (Highly Experimental!) Warning, clears IPtables rules!
```
* To quickly connect to a specific server.
``` bash
openpyn -s au10
```
* To list all the Countries and their Country Codes where NordVPN hosts servers.
``` bash
openpyn -l
```
* To find detailed information about the available servers in a given country.
``` bash
openpyn -l uk
```
* To find servers with featurs like "peer-to-peer", "dedicated ip", "tor over vpn",
  "double vpn" in all countries or a given country.
``` bash
openpyn -l uk --p2p
openpyn -l uk --dedicated
openpyn -l --tor  # tor over vpn in all countries
```
* To find the least loaded 10 NordVPN servers in US that support "peer-to-peer", out
  of them, connect to one of the top 2 servers that have the lowest latency from you.
``` bash
openpyn us -t 10 -T 2 --p2p
```
* To run the script in background.
``` bash
sudo openpyn us -d #needs sudo to use openvpn
```
* To kill a running openvpn connection.
``` bash
sudo openpyn -k
```
* To Flush the iptables and kill any running openvpn connections.
``` bash
sudo openpyn -x
```

## Usage Options
``` bash
usage: openpyn.py [-h] [-v] [-s SERVER] [-u] [-c COUNTRY_CODE] [-d]
                  [-m MAX_LOAD] [-t TOP_SERVERS] [-p PINGS]
                  [-T TOPPEST_SERVERS] [-k] [-x] [--update]
                  [--update-countries] [-l [L_LIST]] [-f]
                  [country]

A python3 script to easily connect to and switch between, OpenVPN servers
hosted by NordVPN. Quickly Connect to the least busy servers (using current
data from Nordvpn website) with lowest latency from you. Tunnels DNS traffic
through the VPN which normally (when using OpenVPN with NordVPN) goes through
your ISP''s DNS (still unencrypted, even if you use a thirdparty) and
completely compromises Privacy!

positional arguments:
  country               Country Code can also be speficied without "-c," i.e
                        "openpyn au"

optional arguments:
  -h, --help            show this help message and exit

  -v, --version         show program''s version number and exit

  -s SERVER, --server SERVER
                        server name, i.e. ca64 or au10

  -u, --udp             use port UDP-1194 instead of the default TCP-443

  -c COUNTRY_CODE, --country-code COUNTRY_CODE
                        Specifiy Country Code with 2 letters, i.e au,

  -d, --daemon          Run script in the background as openvpn daemon

  -m MAX_LOAD, --max-load MAX_LOAD
                        Specifiy load threashold, rejects servers with more
                        load than this, DEFAULT=70

  -t TOP_SERVERS, --top-servers TOP_SERVERS
                        Specifiy the number of Top Servers to choose from the
                        NordVPN''s Sever list for the given Country, These will
                        be Pinged. DEFAULT=6

  -p PINGS, --pings PINGS
                        Specifiy number of pings to be sent to each server to
                        determine quality, DEFAULT=5

  -T TOPPEST_SERVERS, --toppest-servers TOPPEST_SERVERS
                        After ping tests the final server count to randomly
                        choose a server from, DEFAULT=3

  -k, --kill            Kill any running Openvnp process, very usefull to kill
                        openpyn process running in background with "-d" switch

  -x, --kill-flush      Kill any running Openvnp process, AND Flush Iptables

  --update              Fetch the latest config files from nord''s site

  --update-countries    Fetch the latest countries from nord''s site and update
                        the country code mappings

  -l [L_LIST], --list [L_LIST]
                        If country code supplied ("-l us"): Displays all
                        servers in a given country with their current load and
                        supported features. Otherwise: display all
                        countries along with thier country-codes

  --p2p                 Only look for servers with "Peer To Peer" support
  --dedicated           Only look for servers with "Dedicated IP" support
  --tor                 Only look for servers with "Tor Over VPN" support
  --double              Only look for servers with "Double VPN" support
  --anti-ddos           Only look for servers with "Anti DDos" support

  -f, --force-fw-rules  Enfore Firewall rules to drop traffic when tunnel
                        breaks , Force disable DNS traffic going to any other
                        interface
  ```
## Todo
- [x] find servers with P2P support, Dedicated ips, Anti DDoS, Double VPN, Onion over VPN
- [x] utilise the frequently updated api at "api.nordvpn.com/server"
- [x] clean exit, handle exceptions
- [x] store creds from user input, if "creds" file exists use that instead.
- [x] sane command-line options following the POSIX guidelines
- [ ] ability to store profiles
- [ ] find and display server's locations (cities)
- [ ] create a combined config of multiple servers (on the fly) for auto failover
- [ ] uninstall.sh
