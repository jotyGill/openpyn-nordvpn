import getpass
import logging
import os
import subprocess
import sys

import verboselogs
from openpyn import __basefilepath__, root

verboselogs.install()
logger = logging.getLogger(__package__)

credentials_file_path = __basefilepath__ + "credentials"


def check_credentials() -> bool:
    return os.path.exists(credentials_file_path)


def save_credentials() -> None:
    if not sys.__stdin__.isatty():
        raise RuntimeError("Please run %s in interactive mode" % __name__)

    logger.info("Storing credentials in '%s' with openvpn \
compatible 'auth-user-pass' file format", credentials_file_path)

    username = input("Enter your username for NordVPN, i.e youremail@yourmail.com: ")
    password = getpass.getpass("Enter the password for NordVPN: ")
    try:
        with open(credentials_file_path, 'w') as creds:
            creds.write(username + "\n")
            creds.write(password + "\n")
        # Change file permission to 600
        os.chmod(credentials_file_path, 0o600)

        logger.info("Awesome, the credentials have been saved in '%s'", credentials_file_path)
    except (IOError, OSError):
        raise RuntimeError("IOError while creating 'credentials' file.")
