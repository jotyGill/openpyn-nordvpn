#!/usr/bin/env sh

install -Dm755 openpyn.py "/usr/share/openpyn/openpyn.py"
install -Dm755 manual-dns-patch.sh "/usr/share/openpyn/manual-dns-patch.sh"
install -Dm755 update-resolv-conf.sh "/usr/share/openpyn/update-resolv-conf.sh"
install -Dm644 country-mappings.json "/usr/share/openpyn/country-mappings.json"
install -Dm644 LICENSE.md "/usr/share/openpyn/LICENSE.md"
install -Dm644 README.md "/usr/share/openpyn/README.md"
install -Dm640 pass.txt "/usr/share/openpyn/pass.txt"
mkdir /usr/share/openpyn/files

ln -sf "/usr/share/openpyn/openpyn.py" "/usr/bin/openpyn"
