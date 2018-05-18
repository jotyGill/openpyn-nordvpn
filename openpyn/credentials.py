import os
import subprocess
import sys

from colorama import Fore, Style
from openpyn import __basefilepath__, root

credentials_file_path = __basefilepath__ + "credentials"


def check_credentials():
    return os.path.exists(credentials_file_path)


def save_credentials():
    if root.verify_running_as_root() is False:
        print(Fore.RED + "\nPlease run as 'sudo openpyn --init' the first time. Root access is",
              "needed to store credentials in " + "'" + credentials_file_path + "'" + "." + Style.RESET_ALL)
        sys.exit()
    else:
        print(Fore.BLUE + "Storing credentials in " + "'" + credentials_file_path + "'" + " with openvpn",
              "compatible 'auth-user-pass' file format\n")

        username = input("Enter your username for NordVPN, i.e youremail@yourmail.com: ")
        password = input("Enter the password for NordVPN: ")
        try:
            with open(credentials_file_path, 'w') as creds:
                creds.write(username + "\n")
                creds.write(password + "\n")
            creds.close()
            # Change file permission to 600
            subprocess.check_call(["sudo", "chmod", "600", credentials_file_path])

            print("Awesome, the credentials have been saved in " +
                  "'" + credentials_file_path + "'" + "\n" + Style.RESET_ALL)
        except (IOError, OSError):
            print("IOError while creating 'credentials' file.")
    return
