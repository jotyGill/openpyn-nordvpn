import sys
import os.path
import subprocess

__version__ = "2.4.5"
__license__ = "GNU General Public License v3 or later (GPLv3+)"
__data_files__ = []

install_dir = os.path.dirname(os.path.abspath(__file__))
# find "/", Excluding the very last one, +1 to keep '/' at the end
__basefilepath__ = install_dir[:install_dir.rfind('/', 0, -1) + 1]
print(__basefilepath__)

if sys.platform == "linux":
    if subprocess.check_output(['/bin/uname', '-o']).decode(sys.stdout.encoding).strip() == "ASUSWRT-Merlin":
        __data_files__ = [('/opt/etc/init.d', ['./openpyn/S23openpyn'])]
