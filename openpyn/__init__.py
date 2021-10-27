import os.path
import subprocess
import sys

__version__ = "3.0.0"
__license__ = "GNU General Public License v3 or later (GPLv3+)"
__data_files__ = []
__basefilepath__ = os.path.dirname(os.path.abspath(__file__)) + "/"

log_format = "%(asctime)s [%(levelname)s] %(message)s"

ovpn_folder = os.path.join(__basefilepath__, "files")  # .ovpn config files location
log_folder = "/var/log/openpyn"  # logs will be saved here
credentials_file_path = os.path.join(__basefilepath__, "credentials")  # nordvpn username/password

sudo_user = "root"

if sys.platform == "linux":
    if subprocess.check_output(["/bin/uname", "-o"]).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
        __data_files__ = [("/opt/etc/init.d", ["./openpyn/S23openpyn"])]
        # admin is Asuswrt's UID 1. It's root, but with a different name
        # standard installation Entware
        sudo_user = "admin"
        # alternative installation Entware (not recommended)
        # sudo_user = "root"
    elif os.path.exists("/etc/openwrt_release"):
        __data_files__ = [("/opt/etc/init.d", ["./openpyn/S23openpyn"])]


# locally modify the PATH variable, to get around issues on some distros
def add_to_path(bin_path):
    # add pathseperator i.e ":"
    bin_path_str = os.pathsep + bin_path
    if bin_path_str not in os.environ["PATH"]:
        os.environ["PATH"] += bin_path_str


add_to_path("/usr/sbin")        # for Fedora/Debian
add_to_path("/sbin")            # for Debain Buster
add_to_path("/usr/local/bin")   # for openpyn-management on Fedora
add_to_path("/usr/local/sbin")  # for openpyn-management on MacOS
