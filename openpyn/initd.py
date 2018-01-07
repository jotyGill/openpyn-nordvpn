import subprocess
import os
import fileinput


def install_service():
    openpyn_options = input("Enter Openpyn options to be stored in initd \
service file (/opt/etc/init.d/S23openpyn, \
Default(Just Press Enter) is, uk : ") or "uk"
    update_service(openpyn_options)


def update_service(openpyn_options, run=False):
    if "--silent" not in openpyn_options:
        openpyn_options += " --silent"
    openpyn_options = openpyn_options.replace("-d ", "")
    openpyn_options = openpyn_options.replace("--daemon", "")
    openpyn_options = openpyn_options.replace("openpyn ", "")

    os.chmod("/opt/etc/init.d/S23openpyn", 0o755)
    for line in fileinput.FileInput("/opt/etc/init.d/S23openpyn", inplace=1):
        sline = line.strip().split("=")
        if sline[0].startswith("ARGS"):
            sline[1] = "\"" + openpyn_options + "\""
        line = '='.join(sline)
        print(line)

    print("\nThe Following config has been saved in S23openpyn.",
          "You can Start it or/and Stop it with: '/opt/etc/init.d/S23openpyn start',",
          "'/opt/etc/init.d/S23openpyn stop' \n\n")

    subprocess.run("/opt/etc/init.d/S23openpyn stop".split())
    if run:
        print("Started Openpyn by running '/opt/etc/init.d/S23openpyn start'\n\
To check VPN status, run '/opt/etc/init.d/S23openpyn check'")
        subprocess.run("/opt/etc/init.d/S23openpyn start".split())
