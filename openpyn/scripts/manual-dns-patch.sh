#!/usr/bin/env sh

nordDNS1="103.86.99.100"
nordDNS2="103.86.96.100"
openDNS3="208.67.222.220"

echo "Changing DNS servers to NordVPN's DNS Servers"
echo "nameserver nordDNS1 = $nordDNS1"
echo "nameserver nordDNS2 = $nordDNS2"
echo "nameserver openDNS3 = $openDNS3"

# try to move current resolv.conf to a backup file before overwriting
# if backup already exists, do not overwrite backup
mv -n /etc/resolv.conf /etc/resolv.conf.backup

echo "nameserver $nordDNS1" >  /etc/resolv.conf
echo "nameserver $nordDNS2" >> /etc/resolv.conf
echo "nameserver $openDNS3" >> /etc/resolv.conf
