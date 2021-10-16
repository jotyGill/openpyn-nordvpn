#!/usr/bin/env python3

import argparse
import logging
import os
import socket
import sys
from time import sleep
from typing import List

import verboselogs

from openpyn import log_folder
from openpyn import log_format

verboselogs.install()
logger = logging.getLogger(__package__)

logger.setLevel(logging.INFO)

# Add another rotating handler to log to .log files
file_handler = logging.FileHandler(log_folder + "/openpyn-notifications.log")
file_handler_formatter = logging.Formatter(log_format)
file_handler.setFormatter(file_handler_formatter)
logger.addHandler(file_handler)


def socket_connect(server, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    return s


# pylint: disable=C0415,E0401
def show(do_notify) -> bool:
    detected_os = sys.platform
    sleep(1)
    if do_notify:
        try:
            import gi
        except ImportError:
            logger.error("Python3-gi not found, expected on a non-gui os")
            return 1
        try:
            gi.require_version("Notify", "0.7")
            from gi.repository import Notify
        except ValueError:
            logger.error("Notify 0.7 not found, expected on a non-gui os")
            return 1

        if detected_os == "linux":
            Notify.init("openpyn")

    while True:
        try:
            s = socket_connect("localhost", 7015)
        except ConnectionRefusedError:
            sleep(3)
            continue
        break

    try:
        # create the notification object and show once
        summary = "Openpyn"
        body = "Initiating connection (If stuck here, try again)"
        if detected_os == "linux":
            if do_notify:
                notification = Notify.Notification.new(summary, body)
                notification.show()
            logger.warning("%s %s", summary, body)
        elif detected_os == "darwin":
            if do_notify:
                notification = '"{}" with title "{}"'.format(body, summary)
                os.system("""osascript -e 'display notification {}'""".format(notification))
        last_status_UP = False
        # s.send(str.encode("state on"))
        while True:
            data = s.recv(1024)
            data_str = repr(data)
            # logger.debug(data_str)
            # if 'UPDOWN:DOWN' or 'UPDOWN:UP' or 'INFO' in data_str:
            if "UPDOWN:UP" in data_str:
                last_status_UP = True
                # logger.debug("Received AN UP")

            if "UPDOWN:DOWN" in data_str:
                last_status_UP = False

                # logger.debug("Received A DOWN" + data_str)
                body = "Connection Down, Disconnected."
                if detected_os == "linux":
                    if do_notify:
                        notification.update(summary, body)
                        # show again
                        notification.show()
                    logger.info("%s %s", summary, body)
                elif detected_os == "darwin":
                    if do_notify:
                        notification = '"{}" with title "{}"'.format(body, summary)
                        os.system("""osascript -e 'display notification {}'""".format(notification))

            server_name_location = data_str.find("common_name=")
            # logger.debug(server_name_location)
            if server_name_location != -1 and last_status_UP is True:
                server_name_start = data_str[server_name_location + 12:]
                server_name = server_name_start[:server_name_start.find(".com") + 4]
                # logger.debug("Both True and server_name %s", server_name)
                body = "Connected! to " + server_name
                if detected_os == "linux":
                    if do_notify:
                        notification.update(summary, body)
                        notification.show()
                    logger.info("%s %s", summary, body)
                elif detected_os == "darwin":
                    if do_notify:
                        notification = '"{}" with title "{}"'.format(body, summary)
                        os.system("""osascript -e 'display notification {}'""".format(notification))

            # break of data stream is empty
            if not data:
                break

    except KeyboardInterrupt:
        body = "Disconnected, Bye."
        logger.info("%s %s", summary, body)
        if detected_os == "linux":
            if do_notify:
                notification.update(summary, body)
                notification.show()
        elif detected_os == "darwin":
            if do_notify:
                notification = '"{}" with title "{}"'.format(body, summary)
                os.system("""osascript -e 'display notification {}'""".format(notification))
    except ConnectionResetError:
        body = "Disconnected, Bye. (ConnectionReset)"
        logger.info("%s %s", summary, body)
        if detected_os == "linux":
            if do_notify:
                notification.update(summary, body)
                notification.show()
        elif detected_os == "darwin":
            if do_notify:
                notification = '"{}" with title "{}"'.format(body, summary)
                os.system("""osascript -e 'display notification {}'""".format(notification))

    s.close()
    return 0


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Management interface for openpyn to display notifications and log"
        " them to {}/openpyn-notifications.log".format(log_folder),
        allow_abbrev=False,
    )
    parser.add_argument("--do-notify", dest="do_notify", help="try to display desktop notifications.", action="store_true")

    return parser.parse_args(argv[1:])


def main() -> bool:
    args = parse_args(sys.argv)
    return show(args.do_notify)


if __name__ == "__main__":
    sys.exit(main())
