#!/usr/bin/env sh

nordDNS1="162.242.211.137"
nordDNS2="78.46.223.24"
openDNS3="208.67.222.220"

echo "Changing DNS servers to NordVPN's DNS Servers"
echo "nameserver nordDNS1 = $nordDNS1"
echo "nameserver nordDNS2 = $nordDNS2"
echo "nameserver openDNS3 = $openDNS3"

echo "nameserver $nordDNS1" >  /etc/resolv.conf
echo "nameserver $nordDNS2" >> /etc/resolv.conf
echo "nameserver $openDNS3" >> /etc/resolv.conf
