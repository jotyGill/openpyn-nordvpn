# openpyn
A python3 script to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers (using current data from Nordvpn's website) with lowest latency from you. Find servers in a specific country or even a city. It Tunnels DNS traffic through the VPN which normally (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a third party) and completely compromises Privacy!

## Features
* Automatically connect to least busy, low latency servers in a given country.
* Find and connect to servers in a specific city or state. (New!)
* Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
* Use Iptable rules to prevent leakage if tunnel breaks (Experimental).
* Quickly Connect to any specific server. i.e au10 or us20.
* Downloads and Updates (modifications) the latest config files from NordVPN.
* Option to run the script in background (openvpn daemon mode).
* Options to finetune server selection based on "Server Load" or "Ping Latency".
* Auto excludes the servers if ping to them fails or if they don't support OpenVPN \
  (TCP or UDP depending upon which one you are trying to use).
* Finds and displays nord vpn servers (with extra info) in a given country.
* Now list and connect to servers with "Peer To Peer" --p2p, "Dedicated IP" --dedicated, "Tor Over VPN" --tor, \
"Double VPN" --double, "Anti DDos" --anti-ddos support.
* Desktop notification are shown when VPN connects and disconnects. (needs to run without sudo) (New!)

## Instructions
1. Install dependencies if they are not already present.
``` bash
# dependencies
Python 3.4
sudo apt install openvpn python3-pip
sudo apt install python3-gi   # Needed on Debian/Rasbian Jessie
```
2. Install openpyn:
``` bash
git clone --branch python3.4 https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn
sudo python3 setup.py install   # Desktop notification won't work for Debian
```
3. Initialise the script with "--init" (store credentials and update/install vpn config files)
``` bash
sudo openpyn --init
```
That's it, run the script! when done with it, press "Ctr + C" to exit.

## Basic Usage
* At minimum, you only need to specify the country-code, default port is TCP-443, If you want to use
UDP-1194 instead, use "-u" switch.
``` bash
openpyn us -u
```
* Now, you can also specify a city or state, useful when companies (like Google) lock your
account if you try to login from an IP that resides in a different physical location.
``` bash
openpyn us -a ny
openpyn us --area "new york"
```
* To enforce Firewall rules to prevent dns leakage, also from ip leakage if tunnel breaks.
``` bash
openpyn us -f # (Highly Experimental!) Warning, clears IPtables rules!
              # (changes are non persistent, simply reboot if having networking issues)
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
* To find servers with features like "peer-to-peer", "dedicated ip", "tor over vpn",
  "double vpn" in all countries or a given country.
``` bash
openpyn -l uk --p2p
openpyn --list uk --dedicated
openpyn -l --tor  # tor over vpn in all countries
```
* To find the least loaded 10 NordVPN servers in US that support "peer-to-peer", out
  of them, connect to one of the top 2 servers that have the lowest latency from you.
``` bash
openpyn us -t 10 -T 2 --p2p
```
* To run the script in background.
``` bash
openpyn us -d
```
* To kill a running openvpn connection.
``` bash
sudo openpyn -k
```
* To Flush the iptables and kill any running openvpn connections.
``` bash
sudo openpyn -x
```
* To Download/Update the latest vpn config files from NordVPN by:
``` bash
openpyn --update
```

## Usage Options
``` bash
usage: openpyn.py [-h] [-v] [-s SERVER] [-u] [-c COUNTRY_CODE] [-a AREA] [-d]
                  [-m MAX_LOAD] [-t TOP_SERVERS] [-p PINGS]
                  [-T TOPPEST_SERVERS] [-k] [-x] [--update] [-f]
                  [-l [LIST_SERVERS]] [--p2p] [--dedicated] [--tor] [--double]
                  [--anti-ddos] [--test]
                  [country]

A python3 script to easily connect to and switch between, OpenVPN servers
hosted by NordVPN. Quickly Connect to the least busy servers (using current
data from Nordvpn website) with lowest latency from you. Tunnels DNS traffic
through the VPN which normally (when using OpenVPN with NordVPN) goes through
your ISP''s DNS (still unencrypted, even if you use a thirdparty) and
completely compromises Privacy!

positional arguments:
  country               Country Code can also be specified without "-c," i.e
                        "openpyn au"

optional arguments:
  -h, --help            show this help message and exit

  -v, --version         show program''s version number and exit

  --init                Initialise, store/change credentials, download/update
                        vpn config files, needs root "sudo" access.

  -s SERVER, --server SERVER
                        server name, i.e. ca64 or au10

  -u, --udp             use port UDP-1194 instead of the default TCP-443

  -c COUNTRY_CODE, --country-code COUNTRY_CODE
                        Specify Country Code with 2 letters, i.e au,

  -a AREA, --area AREA  Specify area: city name or state e.g "openpyn au -a victoria"
                        or "openpyn au -a 'sydney'"

  -d, --daemon          Run script in the background as openvpn daemon

  -m MAX_LOAD, --max-load MAX_LOAD
                        Specify load threshold, rejects servers with more
                        load than this, DEFAULT=70

  -t TOP_SERVERS, --top-servers TOP_SERVERS
                        Specify the number of Top Servers to choose from the
                        NordVPN''s Sever list for the given Country, These will
                        be Pinged. DEFAULT=4

  -p PINGS, --pings PINGS
                        Specify number of pings to be sent to each server to
                        determine quality, DEFAULT=5

  -T TOPPEST_SERVERS, --toppest-servers TOPPEST_SERVERS
                        After ping tests the final server count to randomly
                        choose a server from, DEFAULT=2

  -k, --kill            Kill any running Openvnp process, very useful to kill
                        openpyn process running in background with "-d" switch

  -x, --kill-flush      Kill any running Openvnp process, AND Flush Iptables

  -f, --force-fw-rules  Enforce Firewall rules to drop traffic when tunnel
                        breaks , Force disable DNS traffic going to any other
                        interface

  --update              Fetch the latest config files from nord''s site

  -l [L_LIST], --list [L_LIST]
                        If no argument given prints all Country Names and
                        Country Codes; If country code supplied ("-l us"):
                        Displays all servers in that given country with their
                        current load and openvpn support status. Works in
                        conjunction with (-a | --area, and server types (--p2p,
                        --tor) e.g "openpyn -l it --p2p --area milano"

  --p2p                 Only look for servers with "Peer To Peer" support
  --dedicated           Only look for servers with "Dedicated IP" support
  --tor                 Only look for servers with "Tor Over VPN" support
  --double              Only look for servers with "Double VPN" support
  --anti-ddos           Only look for servers with "Anti DDos" support
  --test                Simulation only, do not actually connect to the vpn
                        server

  ```
## Todo
- [x] find servers with P2P support, Dedicated ips, Anti DDoS, Double VPN, Onion over VPN
- [x] utilise the frequently updated api at "api.nordvpn.com/server"
- [x] clean exit, handle exceptions
- [x] store credentials from user input, if "credentials" file exists use that instead.
- [x] sane command-line options following the POSIX guidelines
- [ ] ability to store profiles
- [x] find and display server's locations (cities)
- [x] accept full country names
- [ ] colourise output
- [x] modularize
- [ ] create a combined config of multiple servers (on the fly) for auto failover
- [x] uninstall.sh   #sudo pip3 uninstall openpyn
- [ ] view status of the connection after launching in --daemon mode.
- [x] desktop notifications.
