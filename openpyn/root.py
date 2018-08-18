import logging
import os
import pwd
import subprocess
import sys

import verboselogs

verboselogs.install()
logger = logging.getLogger(__package__)


def verify_root_access(message: str) -> bool:
    # Check that user has root privileges. if not print message
    # in a case when starting openpyn without sudo then providing sudo privileges when asked,
    # sudo privileges get cached, os.getuid would say user not root and prints "root needed"
    # messages, but it would work

    #    if os.getuid() != 0:
    #        logger.debug(message)
    #        return False

    try:
        subprocess.check_output(
            ["sudo", "-n", "cat", "/etc/resolv.conf"], stderr=subprocess.DEVNULL)
    # -n 'non-interactive' mode used to, not prompt for password (if user not sudo) but throw err.
    except subprocess.CalledProcessError:
        logger.notice(message)
        return False
    return True


# check if openpyn itself has been started with root access.
def verify_running_as_root() -> bool:
    if os.getuid() == 0:
        # logger.debug(message)
        return True
    return False


def obtain_root_access() -> None:
    # asks for sudo password to be cached
    try:    # try accessing root read only file "600" permission, ask for sudo pass
        subprocess.call(
            ["sudo", "cat", "/etc/resolv.conf"],
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        logger.error("except occurred while running obtain_root_access() 'sudo ls' command")
    except KeyboardInterrupt:
        logger.info('(KeyboardInterrupt) Ctrl+C received, Bye')
        sys.exit()


def logged_in_user_is_root(username: str) -> bool:
    user_record = pwd.getpwnam(username)
    user_id = user_record.pw_gid
    # logger.debug("user_record %s", user_id)
    if user_id == 0:
        return True
    return False


def running_with_sudo() -> bool:
    if verify_running_as_root():
        try:
            logged_in_user = os.getlogin()
            if logged_in_user_is_root(logged_in_user):
                return False    # when logged in as 'root' user notifications will work.
            return True     # 'sudo' is used notification won't work.
        except FileNotFoundError:
            logger.verbose(
                "os.getlogin(), returned FileNotFoundError, assuming 'openpyn' is running with 'SUDO'")
            return True
        except OSError:
            logger.verbose(
                "os.getlogin(), returned error, assuming 'openpyn' is running with 'SUDO'")
            return True

    return False    # regular user without 'sudo'
