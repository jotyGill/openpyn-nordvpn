import subprocess


def install_service():
    openpyn_options = input("Enter Openpyn options to be stored in systemd\
    service file (/etc/systemd/system/openpyn.service, \
    Default is, uk :") or "uk"
    update_service(openpyn_options)


def update_service(openpyn_options, run=False):
    if "--silent" not in openpyn_options:
        openpyn_options += " --silent "
    openpyn_options = openpyn_options.replace("-d ", "")
    openpyn_options = openpyn_options.replace("--daemon", "")
    openpyn_location = str(subprocess.check_output("which openpyn".split())) + " "
    openpyn_location = openpyn_location[2:-4]
    service_text = "[Unit]\nDescription=NordVPN connection manager\nAfter=multi-user.target\n[Service]\nType=simple\nUser=root\nWorkingDirectory=/usr/share/openpyn/\nExecStart=" + openpyn_location + openpyn_options + "\nStandardOutput=syslog\nStandardError=syslog\n[Install]\nWantedBy=multi-user.target\n"

    with open("/etc/systemd/system/openpyn.service", "w+") as service_file:
            service_file.write(service_text)
            service_file.close()

    print("\nThe Following config has been saved in openpyn.service.",
        "You can Run it or/and Enable it with: 'sudo systemctl start openpyn',",
          "'sudo systemctl enable openpyn' \n\n", service_text)

    subprocess.run("systemctl daemon-reload".split())
    if run:
        print("Started Openpyn by running 'systemctl start openpyn'\n\
To check VPN status, run 'systemctl status openpyn'")
        subprocess.run("systemctl start openpyn".split())
