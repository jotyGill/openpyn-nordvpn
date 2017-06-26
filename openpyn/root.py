import subprocess
import os
import pwd


def verify_root_access(message):
    # Check that user has root priveleges. if not print message
    # in a case when starting openpyn without sudo then providing sudo priveleges when asked,
    # sudo priveleges get cached, os.getuid would say user not root and print "root needed"
    # messages, but it would work

    #    if os.getuid() != 0:
    #        print(message, '\n')
    #        return False

    try:
        check_root = subprocess.check_output(
            "sudo -n cat /etc/resolv.conf".split(), stderr=subprocess.DEVNULL)
    # -n 'non-interactive' mode used to, not prompt for password (if user not sudo) but throw err.
    except subprocess.CalledProcessError:
        print(message, '\n')
        return False
    return True


# check if openpyn itself has been started with root access.
def verify_running_as_root():
        if os.getuid() == 0:
            # print(message, '\n')
            return True
        return False


def obtain_root_access():
    # asks for sudo password to be cached
    try:    # try accessing root read only file "600" permission, ask for sudo pass
        check_root = subprocess.run(
            "sudo cat /etc/resolv.conf".split(),
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("except occured while running obtain_root_access() 'sudo ls' command")


def logged_in_user_is_root(username):
    user_record = pwd.getpwnam(username)
    user_id = user_record.pw_gid
    # print(user_record, user_id)
    if user_id == 0:
        return True
    return False


def running_with_sudo():
    if verify_running_as_root():
        logged_in_user = os.getlogin()
        if logged_in_user_is_root(logged_in_user):
            return False    # when loggdin as 'root' user notifications will work.
        else:
            return True     # 'sudo' is used notification won't work.
    return False    # regular user without 'sudo'
