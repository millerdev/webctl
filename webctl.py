#! /usr/bin/env python
import argparse
import json
import re
from os.path import abspath, dirname, join
from subprocess import check_output, call, CalledProcessError

from bottle import (route, run, template, static_file, request, response,
    redirect)

BASE_DIR = join(dirname(abspath(__file__)))
STATIC_DIR = join(BASE_DIR, "static")
AMIXER = "/usr/bin/amixer"
TV_CHANNEL = "Line in"
AMIXER_VOLUME_EXP = re.compile(r"Front Left: \d+ \[(\d+)%\]")
ALSA_LOOP_SERVICE = "/etc/init.d/alsaloop"
SYSINFO_COMMAND = join(BASE_DIR, 'sysinfo.sh')

amixer_state = {}

@route("/")
def index():
    return static_file("index.html", root=STATIC_DIR)

@route("/static/<filepath:path>")
def static(filepath):
    if not filepath or filepath == "index.html":
        return redirect("/")
    return static_file(filepath, root=STATIC_DIR)

def tv_volume(value=None):
    """Get/update TV volume

    :param value: Update TV volume if not None. Must be None or an
        integer between 0 and 100 inclusive.
    :returns: TV volume integer between 0 and 100 inclusive.
    """
    cmd = [AMIXER]
    if value is not None:
        assert value >= 0 and value <= 100, value
        percent = "{}%".format(value)
        out = check_output(cmd + ["sset", TV_CHANNEL, percent])
    else:
        out = check_output(cmd + ["sget", TV_CHANNEL])
    match = AMIXER_VOLUME_EXP.search(out)
    if match:
        return int(match.group(1))
    return None

def loop_status(value=None):
    """Get/update TV loopback status

    :param value: Update TV volume if not None. Acceptable values are
        "on", "off" and None.
    :returns: TV volume integer between 0 and 100.
    """
    if value is not None:
        if value == "off":
            error = call([
                "timeout", "--kill-after", "35s", "36s",
                ALSA_LOOP_SERVICE, "stop",
            ])
            if error:
                call(["killall", "-9", "alsaloop"])
        else:
            assert value == "on"
            call([ALSA_LOOP_SERVICE, "start"])
    try:
        out = check_output([ALSA_LOOP_SERVICE, "status"])
    except CalledProcessError as err:
        return "off"
    return "on" if "alsaloop is running" in out else "off"

@route("/ctl")
def get_ctl():
    """Get the state of the mixer controls"""
    return json.dumps({"volume": tv_volume(), "loopback": loop_status()})

@route("/ctl", method="POST")
def set_ctl(actions=[("volume", tv_volume), ("loopback", loop_status)]):
    """Update mixer controls and return their updated state"""
    data = request.json
    return {field: action(data.get(field)) for field, action in actions}

@route("/system-info")
def system_info():
    try:
        return check_output(SYSINFO_COMMAND)
    except Exception as err:
        return "Cannot load system info:\n{}: {}" \
            .format(type(err).__name__, err)

def main():
    parser = argparse.ArgumentParser(description="Pogo controller web server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", default=80, type=int)
    parser.add_argument("--reload", action="store_true", default=False,
        help="Auto-reload on script change.")
    args = parser.parse_args()
    run(host=args.host, port=args.port, reloader=args.reload)

if __name__ == "__main__":
    main()