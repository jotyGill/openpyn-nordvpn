|PyPI version| |license|

openpyn : A wrapper around openvpn
===============

A python3 script to easily connect to and switch between, **OpenVPN servers hosted by NordVPN**.
Quickly Connect to the **least busy** servers (using current data from Nordvpn's website) with **lowest latency** from you.
Find servers in a **specific country** or even a **city**. It **Tunnels DNS traffic** through the VPN which normally
(when using OpenVPN with NordVPN) goes through your ISP's DNS (still unencrypted, even if you use a thirdparty)
and completely compromises Privacy!

Features
--------
- Automatically connect to least busy, low latency servers in a given country.
- Find and connect to servers in a specific city or state. (New!)
- Uses NordVPN's DNS servers and tunnels DNS queries through the VPN Tunnel.
- Use Iptable rules to prevent leakage if tunnel breaks (Experimental).
- Quickly Connect to any specific server. i.e au10 or us20.
- Downloads and Updates (modifications) the latest config files from NordVPN.
- Option to run the script in background (openvpn daemon mode).
- Options to finetune server selection based on "Server Load" or "Ping Latency".
- Excludes the servers that don't support OpenVPN (TCP or UDP depending upon which one you are trying to use).
- Finds and displays nord vpn servers (with extra info) in a given country.
- Now list and connect to servers with "Peer To Peer" --p2p, "Dedicated IP" --dedicated, "Tor Over VPN" --tor, \
"Double VPN" --double, "Anti DDos" --anti-ddos support.

To Install
--------------

::

    pip3 install openpyn

To Upgrade
-------------

::

    pip3 install --upgrade openpyn

To Uninstall
----------------

::

    pip3 uninstall openpyn
