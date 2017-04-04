A python3 script to easily connect to, VPN servers hosted by NordVPN.

usage: openpyn.py [-h] [-s SERVER] [-u] [-c COUNTRYCODE] [-b]
                  [-l LOADTHRESHOLD] [-t TOPSERVERS] [-p PINGS]
                  [-tt TOPPESTSERVERS]
                  countryCode

Script to Connect to OpenVPN

positional arguments:
  countryCode           Country Code can also be speficied without "-c," i.e
                        "./openpyn.py au"

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
                        NordVPN's Sever list for the given Country, These will
                        be Pinged. DEFAULT=10
  -p PINGS, --pings PINGS
                        Specifiy number of pings to be sent to each server to
                        determine quality, DEFAULT=10
  -tt TOPPESTSERVERS, --toppestServers TOPPESTSERVERS
                        After ping tests the final server count to randomly
                        choose a server from, DEFAULT=5
