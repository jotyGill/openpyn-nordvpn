# openpyn
A python3 script to easily connect to and switch between, OpenVPN servers hosted by NordVPN. Quickly Connect to the least busy servers (using current data from Nordvpn's website) with lowest latency from you. Find servers in a specific country or even a city. It Tunnels DNS traffic through the VPN which normally (when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a third party) and completely compromises Privacy!

## Features
* Automatically connect to least busy, low latency servers in a given country.
* Find and connect to servers in a specific city or state.
* Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
* Use Iptables rules to prevent IP leakage if tunnel breaks (Experimental).
* Quickly Connect to any specific server. i.e au10 or us20.
* Downloads and Updates (modifications) the latest config files from NordVPN.
* Option to run the script in background (openvpn daemon mode).
* Options to fine-tune server selection based on "Server Load" or "Ping Latency".
* Auto excludes the servers if ping to them fails or if they don't support OpenVPN \
  (TCP or UDP depending upon which one you are trying to use).
* Finds and displays nord vpn servers (with extra info) in a given country.
* Now list and connect to servers with "Peer To Peer" --p2p, "Dedicated IP" --dedicated, "Tor Over VPN" --tor, \
"Double VPN" --double, "Anti DDos" --anti-ddos support.
* Desktop notification are shown when VPN connects and disconnects. (needs to run without sudo)
* Auto retry if [soft,auth-failure] received, auto failover to next best server if connection dies. (not in daemon mode)

## Demo
![connection](https://user-images.githubusercontent.com/8462091/29347697-0798a52a-823e-11e7-818f-4dad1582e173.gif)

## Instructions
1. Install dependencies if they are not already present. On RedHat based distros, substitute "apt" with "dnf" or "yum"
``` bash
# common dependencies
sudo apt install openvpn python-gobject unzip wget
```
### Installation Methods
1. For Ubuntu / Kali / Debian / based OS's with Python=>3.4
```bash
sudo apt install python3-colorama python3-requests python3-setuptools  #dependencies
wget https://github.com/jotyGill/openpyn-nordvpn/archive/python3-openpyn_1.7.3-1_all.deb
sudo dpkg -i python3-openpyn_1.7.3-1_all.deb
```
2. For Fedora
```bash
wget https://github.com/jotyGill/openpyn-nordvpn/archive/openpyn-1.7.3-1.noarch.rpm
sudo dnf install ./openpyn-1.7.3-1.noarch.rpm
```
3. Install openpyn with pip3. (Python=>3.4, Don't use on Debian, causes issues):
``` bash
sudo apt install python3-pip
sudo pip3 install openpyn --upgrade   # DO NOT USE "sudo -H"
```
4. Alternatively clone and install.
``` bash
git clone https://github.com/jotyGill/openpyn-nordvpn.git
cd openpyn-nordvpn
sudo python3 setup.py install
```
### Setup
Initialise the script with "--init" (store credentials and update/install vpn config files)
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
* When using "-f", To allow custom ports (from internal ip ranges, i.e 192.168 or 10.) through the firewall.
``` bash
sudo openpyn us -f --allow 22  #only accessible from local network
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
sudo openpyn -x   #optionally --allow 22 if using as ssh server
```
* To Download/Update the latest vpn config files from NordVPN by:
``` bash
openpyn --update
```
