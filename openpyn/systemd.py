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

    openpyn_options = input("\nEnter Openpyn options to be stored in systemd \
service file (/etc/systemd/system/openpyn.service, \
Default(Just Press Enter) is, uk : ") or "uk"
    update_service(openpyn_options)


def update_service(openpyn_options: str, run=False) -> None:
    if "-f" in openpyn_options or "--force-fw-rules" in openpyn_options:
        kill_option = " --kill-flush"
    else:
        kill_option = " --kill"
    openpyn_options = openpyn_options.replace("-d ", "")
    openpyn_options = openpyn_options.replace("--daemon", "")
    openpyn_location = shutil.which("openpyn")
    sleep_location = shutil.which("sleep")

    service_text = "[Unit]\nDescription=NordVPN connection manager\nWants=network-online.target\n" + \
        "After=network-online.target\nAfter=multi-user.target\n[Service]\nType=simple\nUser=root\n" + \
        "WorkingDirectory=" + __basefilepath__ + "\nExecStartPre=" + sleep_location + " 5\nExecStart=" + \
        openpyn_location + " " + openpyn_options + "\nExecStop=" + openpyn_location + kill_option + \
        "\nStandardOutput=syslog\nStandardError=syslog\n[Install]\nWantedBy=multi-user.target\n"

    _xdg_config_home = os.environ['XDG_CONFIG_HOME']
    if not _xdg_config_home:
        _xdg_config_home = os.path.expanduser(os.path.join('~', '.config'))
    systemd_service_path = os.path.join(_xdg_config_home, 'systemd', 'user', 'openpyn.service')
    with open(systemd_service_path, 'w') as fp:
        fp.write(service_text)

    logger.notice("The Following config has been saved in openpyn.service. \
You can Run it or/and Enable it with: 'sudo systemctl start openpyn', \
'systemctl --user enable openpyn' \n" + service_text)

    subprocess.run(["systemctl", "--user", "daemon-reload"])
    if run:
        subprocess.call(  # subprocess.run behaves differently
            ["systemctl", "--user", "is-active", "openpyn"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        logger.notice("Restarting Openpyn by running 'systemctl restart openpyn'\n\
To check VPN status, run 'systemctl status openpyn'")
        subprocess.Popen(["systemctl", "--user", "restart", "openpyn"])
