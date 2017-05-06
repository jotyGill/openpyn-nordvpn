#!/usr/bin/env sh

mkdir -p /usr/share/openpyn/files

touch /usr/share/openpyn/creds
echo "Storing credentials in '/usr/share/openpyn/creds with openvpn compatible 'auth-user-pass' file format"
read -p "Input the username for NordVPN, i.e youremail@yourmail.com: " username
read -p "Input the password for NordVPN: " password
echo $username > creds
echo $password >> creds

install -Dm755 openpyn.py "/usr/share/openpyn/openpyn.py"
install -Dm755 manual-dns-patch.sh "/usr/share/openpyn/manual-dns-patch.sh"
install -Dm755 update-resolv-conf.sh "/usr/share/openpyn/update-resolv-conf.sh"
install -Dm666 country-mappings.json "/usr/share/openpyn/country-mappings.json"
install -Dm644 LICENSE.md "/usr/share/openpyn/LICENSE.md"
install -Dm644 README.md "/usr/share/openpyn/README.md"
install -Dm600 creds "/usr/share/openpyn/creds"

ln -sf "/usr/share/openpyn/openpyn.py" "/usr/bin/openpyn"

echo "Installation Successful, Enjoy!"
