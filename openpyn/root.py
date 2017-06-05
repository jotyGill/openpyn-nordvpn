import subprocess


def verify_root_access(message):
    # Check that user has root priveleges.
    # in a case when starting openpyn without sudo then providing sudo priveleges when asked,
    # sudo priveleges get cached, os.getuid would say user not root and print "root needed"
    # messages, but it would work

    #    if os.getuid() != 0:
    #        print(message, '\n')
    #        return False

    try:    # try accessing root read only file "600" permission
        check_root = subprocess.check_output(
            "sudo -n cat /usr/share/openpyn/credentials".split(), stderr=subprocess.DEVNULL)
    # -n 'non-interactive' mode used to, not prompt for password but throw err.
    except subprocess.CalledProcessError:
        print(message, '\n')
        return False
    return True


def obtain_root_access():
    try:    # try accessing root read only file "600" permission, ask for sudo pass
        check_root = subprocess.run(
            "sudo ls /usr/share/openpyn/credentials".split(),
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("except occured while running a 'sudo ls' command")
