import logging
import subprocess
import sys

import verboselogs

from openpyn import __basefilepath__

verboselogs.install()
logger = logging.getLogger(__package__)


def install_service() -> int:
    if not sys.__stdin__.isatty():
        logger.critical("Please run %s in interactive mode", __name__)
        return 1

    openpyn_options = input("\nEnter Openpyn options to be stored in systemd \
service file (/etc/systemd/system/openpyn.service, \
Default(Just Press Enter) is, uk : ") or "uk"
    update_service(openpyn_options)
    return 0


def update_service(openpyn_options: str, run=False) -> None:
    if "-f" in openpyn_options or "--force-fw-rules" in openpyn_options:
        kill_option = " --kill-flush"
    else:
        kill_option = " --kill"
    openpyn_options = openpyn_options.replace("-d ", "")
    openpyn_options = openpyn_options.replace("--daemon", "")
    openpyn_location = str(subprocess.check_output(["which", "openpyn"]))[2:-3]
    sleep_location = str(subprocess.check_output(["which", "sleep"]))[2:-3]

    service_text = "[Unit]\nDescription=NordVPN connection manager\nWants=network-online.target\n" + \
        "After=network-online.target\nAfter=multi-user.target\n[Service]\nType=simple\nUser=root\n" + \
        "WorkingDirectory=" + __basefilepath__ + "\nExecStartPre=" + sleep_location + " 5\nExecStart=" + \
        openpyn_location + " " + openpyn_options + "\nExecStop=" + openpyn_location + kill_option + \
        "\nStandardOutput=syslog\nStandardError=syslog\n[Install]\nWantedBy=multi-user.target\n"

    with open("/etc/systemd/system/openpyn.service", "w+") as service_file:
        service_file.write(service_text)
        service_file.close()

    logger.notice("The Following config has been saved in openpyn.service. \
You can Run it or/and Enable it with: 'sudo systemctl start openpyn', \
'sudo systemctl enable openpyn' \n" + service_text)

    subprocess.run(["systemctl", "daemon-reload"])
    if run:
        daemon_running = subprocess.call(  # subprocess.run behaves differently
            ["systemctl", "is-active", "openpyn"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) == 0

        if daemon_running:
            logger.notice("Restarting Openpyn by running 'systemctl restart openpyn'\n\
To check VPN status, run 'systemctl status openpyn'")
            subprocess.Popen(["systemctl", "restart", "openpyn"])
        else:
            logger.notice("Starting Openpyn by running 'systemctl start openpyn'\n\
To check VPN status, run 'systemctl status openpyn'")
            subprocess.Popen(["systemctl", "start", "openpyn"])
