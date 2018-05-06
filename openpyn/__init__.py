import sys
import os.path
import subprocess

__version__ = "2.6.0"
__license__ = "GNU General Public License v3 or later (GPLv3+)"
__data_files__ = []

__basefilepath__ = os.path.dirname(os.path.abspath(__file__)) + "/"
# print("__basefilepath__", __basefilepath__)
if sys.platform == "linux":
    if subprocess.check_output(['/bin/uname', '-o']).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
        __data_files__ = [('/opt/etc/init.d', ['./openpyn/S23openpyn'])]
    elif os.path.exists("/etc/openwrt_release"):
        __data_files__ = [('/opt/etc/init.d', ['./openpyn/S23openpyn'])]
