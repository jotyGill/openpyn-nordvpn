import sys
import subprocess

__version__ = "2.4.2"
__license__ = "GNU General Public License v3 or later (GPLv3+)"
__basefilepath__ = "/usr/share/openpyn/"
__data_files__ = []     # will be overwritten for non Mac OS

if sys.platform == "linux":
    if subprocess.check_output(['/bin/uname', '-o']).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
        __basefilepath__ = "/opt/usr/share/openpyn/"
        __data_files__ = [('/opt/etc/init.d', ['./openpyn/S23openpyn'])]
    else:
        __data_files__ = [(__basefilepath__[:-1],
                           ['./openpyn/scripts/manual-dns-patch.sh',
                            './openpyn/scripts/update-resolv-conf.sh', './openpyn/config.json'])]
