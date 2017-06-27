#!/usr/bin/env python3

import gi
import socket
import os
import sys
from time import sleep
from openpyn import root
gi.require_version('Notify', '0.7')
from gi.repository import Notify


def socket_connect(server, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server, port))
    return s


def show():
    sleep(1)
    Notify.init("openpyn")

    while True:
        try:
            s = socket_connect('localhost', 7015)
        except ConnectionRefusedError:
            sleep(3)
            continue
        break
    try:
        # Create the notification object and show once
        notification = Notify.Notification.new(
                "Openpyn", "Initiating connection (If stuck here, try again)")
        notification.show()
        server_name = ""
        last_status_UP = False
        while True:
            data = s.recv(1024)
            data_str = repr(data)
            # print(data_str)
            # if 'UPDOWN:DOWN' or 'UPDOWN:UP' or 'INFO' in data_str:
            if 'UPDOWN:UP' in data_str:
                last_status_UP = True
                # print ('Received AN UP')

            if 'UPDOWN:DOWN' in data_str:
                last_status_UP = False

                # print ('Received A DOWN', data_str)
                notification.update("Openpyn", "Connection Down, Disconnected.")
                # Show again
                notification.show()

            server_name_location = data_str.find("common_name=")
            # print(server_name_location)
            if server_name_location != -1 and last_status_UP is True:
                server_name_start = data_str[server_name_location + 12:]
                server_name = server_name_start[:server_name_start.find(".com") + 4]
                # print("Both True and server_name", server_name)
                notification.update("Openpyn", "Connected! to " + server_name)
                # Show again
                notification.show()

            # break of data stream is empty
            if not data:
                break

    except (KeyboardInterrupt) as err:
        notification.update("Openpyn", "Disconnected, Bye.")
        notification.show()
        print('\nShutting down safely, please wait until process exits\n')
    except ConnectionResetError:
        notification.update("Openpyn", "Disconnected, Bye. (ConnectionReset)")
        notification.show()
        sys.exit()

    s.close()
    return


if __name__ == '__main__':
    show()
