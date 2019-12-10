#!/usr/bin/env sh

echo "Reverting /etc/resolv.conf back to original"

# force overwrites resolv.conf with the backup
mv -f /etc/resolv.conf.backup /etc/resolv.conf
