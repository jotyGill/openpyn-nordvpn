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

    try:    # try accessing root read only file "600" permission
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


def get_username():
    '''
    try:
        user_output = str(subprocess.check_output("sudo users".split()))
        linux_user = user_output[2:user_output.find(" ")]
        print("users", linux_user)
    except subprocess.CalledProcessError:
        print("except occured while running 'users' command")
    '''
    linux_user = os.getlogin()
    return linux_user


def demote_user(linux_user):
    user_record = pwd.getpwnam(linux_user)
    print(user_record)
    print("old uid", os.getuid())
    print("old euid", os.geteuid())
    os.setuid(user_record.pw_gid)
    os.seteuid(user_record.pw_gid)
    print(os.getlogin())
    print("new uid", os.getuid())
    print("new euid", os.geteuid())
    return
