import getpass
import logging
import os
import subprocess
import sys
from typing import List

import verboselogs
from openpyn import __basefilepath__, root

verboselogs.install()
logger = logging.getLogger(__package__)

credentials_file_path = __basefilepath__ + "credentials"


def check_credentials() -> bool:
    return os.path.exists(credentials_file_path)


def save_credentials() -> None:
    if not sys.__stdin__.isatty():
        logger.critical("Please run %s in interactive mode", __name__)
        sys.exit(1)

    if root.verify_running_as_root() is False:
        logger.error("Please run as 'sudo openpyn --init' the first time. \
Root access is needed to store credentials in '%s'.", credentials_file_path)
        sys.exit(1)
    else:
        logger.info("Storing credentials in '%s' with openvpn \
compatible 'auth-user-pass' file format", credentials_file_path)

        username = input("Enter your username for NordVPN, i.e youremail@yourmail.com: ")
        password = getpass.getpass("Enter the password for NordVPN: ")
        try:
            with open(credentials_file_path, 'w') as creds:
                creds.write(username + "\n")
                creds.write(password + "\n")
            creds.close()
            # Change file permission to 600
            subprocess.check_call(["sudo", "chmod", "600", credentials_file_path])

            logger.info("Awesome, the credentials have been saved in '%s'", credentials_file_path)
        except (IOError, OSError):
            logger.error("IOError while creating 'credentials' file.")
    return
