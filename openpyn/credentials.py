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
        command_1 = "sudo echo " + '"%s"' % username + " > " + credentials_file_path
        command_2 = "sudo echo " + '"%s"' % password + " >> " + credentials_file_path
        try:
            subprocess.call(["sudo", "mkdir", "-p", __basefilepath__])
            # create Empty file with 600 permissions
            subprocess.call(["sudo", "touch", credentials_file_path])
            subprocess.check_call(command_1, shell=True)
            subprocess.check_call(command_2, shell=True)
            subprocess.check_call(["sudo", "chmod", "600", credentials_file_path])

            print("Awesome, the credentials have been saved in " + "'" + credentials_file_path + "'" + "\n")
        except subprocess.CalledProcessError:
            print("Your OS is not letting modify " + "'" + credentials_file_path + "'",
                  "Please run with 'sudo' to store credentials")
            subprocess.call(["sudo", "rm", credentials_file_path])
            sys.exit()
    return
