import logging
import os
import shutil
import subprocess
import sys

import verboselogs

from openpyn import __basefilepath__

verboselogs.install()
logger = logging.getLogger(__package__)


def install_service() -> None:
    if not sys.__stdin__.isatty():
        raise RuntimeError("Please run %s in interactive mode" % __name__)

    openpyn_options = (
        input(
            "\nEnter Openpyn options to be stored in systemd service file (/etc/systemd/system/openpyn.service, Default(Just"
            " Press Enter) is, uk : "
        )
        or "uk"
    )
    update_service(openpyn_options)


def update_service(openpyn_options: str, run=False) -> None:
    # if '-f' is used, you'll need to manually clear the killswitch with 'openpyn -x'
    kill_option = " --kill"
    openpyn_options = openpyn_options.replace("-d ", "")
    openpyn_options = openpyn_options.replace("--daemon", "")
    openpyn_location = shutil.which("openpyn")
    sleep_location = shutil.which("sleep")

    service_text = (
        "[Unit]\nDescription=NordVPN connection manager\nWants=network-online.target\n"
        + "After=network-online.target\nAfter=multi-user.target\n[Service]\nType=simple\nUser=root\n"
        + "WorkingDirectory="
        + __basefilepath__
        + "\nExecStartPre="
        + sleep_location
        + " 5\nExecStart="
        + openpyn_location
        + " "
        + openpyn_options
        + "\nExecStop="
        + openpyn_location
        + kill_option
        + "\nStandardOutput=syslog\nStandardError=syslog\n[Install]\nWantedBy=multi-user.target\n"
    )

    systemd_service_path = os.path.join("/", "etc", "systemd", "system")
    systemd_service_file = os.path.join(systemd_service_path, "openpyn.service")

    if not os.path.exists(systemd_service_path):
        os.makedirs(systemd_service_path)
        os.chmod(systemd_service_path, 0o777)
    with open(systemd_service_file, "w+") as service_file:
        service_file.write(service_text)

    logger.notice(
        "The Following config has been saved in openpyn.service. You can Run it or/and Enable it with: 'sudo systemctl start"
        " openpyn', 'sudo systemctl enable openpyn' \n\n"
        + service_text
    )

    subprocess.run(["systemctl", "daemon-reload"])

    if run:
        logger.notice(
            "Starting/Restarting Openpyn by running 'systemctl restart openpyn'\nTo check VPN status, run 'systemctl status"
            " openpyn'"
        )
        subprocess.Popen(["systemctl", "restart", "openpyn"])
