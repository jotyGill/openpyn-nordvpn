# openpyn
A python3 script (systemd service as well) to manage openvpn connections. Created to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers with lowest latency from you (using current data from Nordvpn's API). Find servers in a specific country or even a city. It Tunnels DNS traffic through the VPN which normally (when using OpenVPN) goes through your ISP's DNS (unencrypted) and compromises Privacy!

## Features
* Automatically connect to least busy, low latency servers in a given country.
* Systemd integration, easy to check VPN status, autostart at startup.
* Find and connect to servers in a specific city or state.
* Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
* Use Iptables rules to prevent IP leakage if tunnel breaks (Experimental), ie KILL SWITCH.
* Quickly Connect to any specific server. i.e au10 or us20.
* Downloads and Updates (modifications) the latest config files from NordVPN.
* Option to run the script in background (as a systemd service).
* Options to finetune server selection based on "Server Load" or "Ping Latency".
* Auto excludes the servers if a ping to them fails or some packets drops when pinging \
or if they don't support OpenVPN \ (TCP or UDP depending upon which one you are trying to use).
* Finds and displays nord vpn servers (with extra info) in a given country.
* Now list and connect to servers with "Netflix" --netflix, "Peer To Peer" --p2p, "Dedicated IP" --dedicated, \
"Tor Over VPN" --tor, "Double VPN" --double, "Anti DDos" --anti-ddos support.
* Desktop notification are shown when VPN connects and disconnects. (needs to run without sudo)
* Auto retry if [soft,auth-failure] received, auto failover to next best server if connection dies.
* NVRAM write support for Asuswrt-merlin
* Pass through openvpn options, e.g. openpyn uk -o '--status /var/log/status.log --log /var/log/log.log'
* Logs stored in '/var/log/openpyn/' for information and troubleshooting.

## Demo
![connection](https://user-images.githubusercontent.com/8462091/29347697-0798a52a-823e-11e7-818f-4dad1582e173.gif)

## Instructions
1. Install dependencies if they are not already present.
``` bash
# common dependencies
sudo apt install openvpn unzip wget python3-setuptools python3-pip
```
2. The following python dependencies are needed and will be installed when using pip.
``` bash
'requests', 'colorama', 'coloredlogs', 'verboselogs'
```
### Installation Methods
1. Install openpyn with pip3 (Python=>3.5)
**Recommended method to get the latest version and receive frequent updates.**
``` bash
sudo python3 -m pip install --upgrade openpyn
```
2. Alternatively clone and install.
``` bash
git clone https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn && sudo python3 -m pip install --upgrade .
```
For the latest/ in development features, try the 'test' branch instead
```bash
 git clone --branch test https://github.com/jotyGill/openpyn-nordvpn.git
 cd openpyn-nordvpn && sudo python3 -m pip install --upgrade -e .
```
3. For macOS with Python=>3.5 (credit: [1951FDG](https://github.com/1951FDG))
``` bash
# common dependencies
xcode-select --install
/usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
echo 'export PATH="/usr/local/sbin:$PATH"' >> ~/.bash_profile
brew install python3 wget openvpn
sudo brew services start openvpn
```
``` bash
git clone https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn
git pull
sudo pip3 install --upgrade .
```
4. On Asuswrt-merlin, install [Entware-ng-3x](https://gist.github.com/1951FDG/3cada1211df8a59a95a8a71db6310299#file-asuswrt-merlin-md) (credit: [1951FDG](https://github.com/1951FDG))
``` bash
# common dependencies
opkg install git git-http iputils-ping procps-ng-pgrep python3 python3-pip sudo unzip wget

```
``` bash
cd /tmp/share/
git clone https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn/
git pull
pip3 install --upgrade setuptools
pip3 install --upgrade .
```

## Setup
Initialise the script with "--init" (store credentials, install Systemd service, update/install vpn config files)
``` bash
sudo openpyn --init
```
Note: if you get ' openpyn: command not found' when using sudo on Fedora, create a symbolic link.
`sudo ln -s /usr/local/bin/openpyn /bin/openpyn`

That's it, run the script! when done with it, press "Ctr + C" to exit.

## Basic Usage
* At minimum, you only need to specify the country-code, default port is UDP-1194, If you want to use
TCP-443 instead, use "--tcp" switch.
``` bash
openpyn us
```
* Now, you can also specify a city or state, useful when companies (like Google) lock your
account if you try to login from an IP that resides in a different physical location.
``` bash
openpyn us -a ny
openpyn us --area "new york"
```
* To enforce Firewall rules to prevent dns leakage, also from ip leakage if tunnel breaks. i.e KILL SWITCH
``` bash
openpyn us -f # Experimental!, Warning, clears IPtables rules!
              # (changes are non persistent, simply reboot if having networking issues)
```
* When using "-f", To allow custom ports (from internal ip ranges, i.e 192.168 or 10.) through the firewall.
``` bash
openpyn us -f --allow 22 80 443  #only accessible from local network
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
* To find servers with features like "peer-to-peer", "netflix", "tor over vpn",
  "double vpn" in all countries or a given country.
``` bash
openpyn -l uk --p2p
openpyn --list uk --dedicated
openpyn -l --tor  # tor over vpn in all countries
```
* To find the least loaded 10 NordVPN servers in US that support "peer-to-peer",
sort them by the lowest latency from you, connect to the best one, if connection fails
try the next one and so on.
``` bash
openpyn us -t 10 --p2p
```
* To update and run the systemd openpyn.service, use "-d" or "--daemon"
``` bash
sudo openpyn us -d
```
* To check the status of the systemd openpyn.service.
``` bash
systemctl status openpyn
```
* To kill a running openvpn connection.
``` bash
sudo openpyn -k
```
* To Flush the iptables and kill any running openvpn connections.
``` bash
sudo openpyn -x   #optionally --allow 22 if using as ssh server
```
* To Download/Update the latest vpn config files from NordVPN by:
``` bash
openpyn --update
```

* To quickly save best NordVPN server in US to NVRAM for "OpenVPN Client 5"
(ASUSWRT-Merlin):
``` bash
openpyn us --nvram 5
```

## Usage Options
``` bash
usage: openpyn.py [-h] [-v] [-s SERVER] [-u] [-c COUNTRY_CODE] [-a AREA] [-d]
                  [-m MAX_LOAD] [-t TOP_SERVERS] [-p PINGS]
                  [-k] [-x] [--update] [-f]
                  [-l [LIST_SERVERS]] [--p2p] [--dedicated] [--tor] [--double] [--anti-ddos] [--test]]
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

  --tcp                 use port TCP-443 instead of the default UDP-1194

  -c COUNTRY_CODE, --country-code COUNTRY_CODE
                        Specify Country Code with 2 letters, i.e au,

  -a AREA, --area AREA  Specify area: city name or state e.g "openpyn au -a victoria"
                        or "openpyn au -a 'sydney'"

  -d, --daemon          Update and start Systemd service openpyn.service,
                        running it as a background process, to check status
                        "systemctl status openpyn",

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

  -k, --kill            Kill any running Openvnp process, very useful to kill
                        openpyn process running in background with "-d" switch

  -x, --kill-flush      Kill any running Openvnp process, AND Flush Iptables

  -f, --force-fw-rules  Enforce Firewall rules to drop traffic when tunnel
                        breaks , Force disable DNS traffic going to any other
                        interface

  --allow INTERNALLY_ALLOWED [INTERNALLY_ALLOWED ...]
                        To be used with "f" to allow ports but ONLY to
                        INTERNAL IP RANGE. e.g, you can use your PC as
                        SSH, HTTP server for local devices (e.g 192.168.1.*
                        range) by using "openpyn us -f --allow 22 80"

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
  --netflix             Only look for servers that are optimised for "Netflix"
  --test                Simulation only, do not actually connect to the vpn
                        server
  -n NVRAM, --nvram NVRAM
                        Specify client to save configuration to NVRAM
                        (ASUSWRT-Merlin)
  -o OPENVPN_OPTIONS, --openvpn-options OPENVPN_OPTIONS
                        Pass through openvpn options, e.g. openpyn uk -o '--
                        status /var/log/status.log --log /var/log/log.log'

  ```
## Todo
- [x] find servers with P2P support, Dedicated ips, Anti DDoS, Double VPN, Onion over VPN
- [x] utilise the frequently updated api at "api.nordvpn.com/server"
- [x] clean exit, handle exceptions
- [x] store credentials from user input, if "credentials" file exists use that instead
- [x] sane command-line options following the POSIX guidelines
- [ ] ability to store profiles (sort of works as the systemd service file stores last state)
- [x] find and display server's locations (cities)
- [x] accept full country names
- [x] colourise output
- [x] modularize
- [x] create a combined config of multiple servers (on the fly) for auto failover
- [x] uninstall.sh   #sudo pip3 uninstall openpyn
- [x] view status of the connection after launching in --daemon mode
- [x] desktop notifications
- [x] initd script for Asuswrt-merlin: "/opt/etc/init.d/S23openpyn start"
