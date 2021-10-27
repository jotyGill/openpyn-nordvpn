import getpass
import logging
import os
import sys

import verboselogs

from openpyn import credentials_file_path
from openpyn import root

verboselogs.install()
logger = logging.getLogger(__package__)


def check_credentials() -> bool:
    return os.path.exists(credentials_file_path)


def save_credentials() -> None:
    if not sys.__stdin__.isatty():
        raise RuntimeError("Please run %s in interactive mode" % __name__)

    if root.verify_running_as_root() is False:
        raise RuntimeError(
            "Please run as 'sudo openpyn --init' the first time. Root access is needed to store credentials in '%s'."
            % credentials_file_path
        )

    logger.info("Storing credentials in '%s' with openvpn compatible 'auth-user-pass' file format", credentials_file_path)

    username = input("Enter your username for NordVPN, i.e youremail@yourmail.com: ")
    password = getpass.getpass("Enter the password for NordVPN: ")
    try:
        with open(credentials_file_path, "w") as creds:
            creds.write(username + "\n")
            creds.write(password + "\n")
        # change file permission to 600
        os.chmod(credentials_file_path, 0o600)

        logger.info("Awesome, the credentials have been saved in '%s'", credentials_file_path)
    except (IOError, OSError):
        raise RuntimeError("IOError while creating 'credentials' file.") from None
