from openpyn import __basefilepath__
from openpyn import root
import subprocess
import sys


def check_credentials():
    credentials_file_path = __basefilepath__ + "credentials"
    try:
        serverFiles = subprocess.check_output(
            "ls " + credentials_file_path, shell=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return False
    return True


def save_credentials():
    credentials_file_path = __basefilepath__ + "credentials"
    if root.verify_running_as_root() is False:
        print("Please run as 'sudo openpyn --init' the first time. Root access is",
              "needed to store credentials in " + "'" + credentials_file_path + "'" + ".")
        sys.exit()
    else:
        print("Storing credentials in " + "'" + credentials_file_path + "'" + " with openvpn",
              "compatible 'auth-user-pass' file format\n")

        username = input("Enter your username for NordVPN, i.e youremail@yourmail.com: ")
        password = input("Enter the password for NordVPN: ")
        try:
            subprocess.call(["sudo", "mkdir", "-p", __basefilepath__])
            with open(credentials_file_path, 'w') as creds:
                creds.write(username + "\n")
                creds.write(password + "\n")
            creds.close()
            # Change file permission to 600
            subprocess.check_call(["sudo", "chmod", "600", credentials_file_path])

            print("Awesome, the credentials have been saved in " +
                  "'" + credentials_file_path + "'" + "\n")
        except subprocess.CalledProcessError:
            print("Your OS is not letting modify " + "'" + credentials_file_path + "'",
                  "Please run with 'sudo' to store credentials")
            subprocess.call(["sudo", "rm", credentials_file_path])
            sys.exit()
    return
