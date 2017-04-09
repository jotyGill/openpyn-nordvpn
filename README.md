# NordVPN server benchmarker
A python3 script to easily connect to, VPN servers hosted by NordVPN. Find the least busy servers (from Nordvpn's website) with lowest latency from you.

## Instructions
1. Clone this repo to a desited location:
``` bash
	$ git clone https://github.com/jotyGill/OpenPyn.git
  $ cd OpenPyn
```
2. Download/Update the latest vpn config files from NordVPN by:
``` bash
  $ ./openpyn --update
```
3. That's it, run the script.

## Usage
``` bash
usage: openpyn.py [-h] [-s SERVER] [-u] [-c COUNTRYCODE] [-b] [-l LOADTHRESHOLD] [-t TOPSERVERS] [-p PINGS]
                  [-tt TOPPESTSERVERS] [-k] [--update] [country]

A python3 script to easily connect to, VPN servers hosted by NordVPN.

positional arguments:
  country               Country Code can also be speficied without "-c," i.em"./openpyn.py au"

optional arguments:
  -h, --help            show this help message and exit

  -s SERVER, --server SERVER
                        server name, i.e. ca64 or au10

  -u, --udp             use port UDP-1194 instead of the default TCP-443

  -c COUNTRYCODE, --countryCode COUNTRYCODE
                        Specifiy Country Code with 2 letter name, i.e au, A
                        server among the top 5 servers will be used
                        automatically.

  -b, --background      Run script in the background

  -l LOADTHRESHOLD, --loadThreshold LOADTHRESHOLD
                        Specifiy load threashold, rejects servers with more
                        load than this, DEFAULT=70

  -t TOPSERVERS, --topServers TOPSERVERS
                        Specifiy the number of Top Servers to choose from the
                        NordVPN\'s Sever list for the given Country, These will
                        be Pinged. DEFAULT=10

  -p PINGS, --pings PINGS
                        Specifiy number of pings to be sent to each server to
                        determine quality, DEFAULT=10

  -tt TOPPESTSERVERS, --toppestServers TOPPESTSERVERS
                        After ping tests the final server count to randomly
                        choose a server from, DEFAULT=5

  -k, --kill            Kill any running Openvnp process, very usefull to kill
                        openpyn process running in background with "-b" switch

  --update              Fetch the latest config files from nord\'s site
  ```
