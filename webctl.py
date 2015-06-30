#! /usr/bin/env python
import argparse
import json
import re
import sys
import traceback
from functools import partial
from os.path import abspath, dirname, join
from subprocess import check_output, call, CalledProcessError
from threading import Thread
from time import sleep

from bottle import (route, run, template, static_file, request, response,
    redirect)

BASE_DIR = join(dirname(abspath(__file__)))
STATIC_DIR = join(BASE_DIR, "static")

AMIXER = "/usr/bin/amixer"
AMIXER_VOLUME_EXP = re.compile(r"Front Left: \d+ \[(\d+)%\]")
AMIXER_MUTE_EXP = re.compile(r"Front Left: [^\n]+\[(on|off)\]")
TV_CHANNEL = "Line in"
AIRPOGO_CHANNEL = "AirPogo"

ALSALOOP_SERVICE = "/etc/init.d/alsaloop"
ALSALOOP_CONF = "/etc/default/alsaloop"
ALSALOOP_ARGS = {
    "squeeze": 'DAEMON_ARGS="-C squeeze_loop -P line_out --sync=0 --tlatency=50000"',
    "airpogo": 'DAEMON_ARGS="-C airpogo_loop -P line_out --sync=0 --tlatency=50000"',
    "tv": 'DAEMON_ARGS="-C line_in -P line --sync=0 --tlatency=50000"',
}
ALSALOOP_STATUS = {
    "squeeze": '/proc/asound/Loopback/pcm0p/sub1/status',
    "airpogo": '/proc/asound/Loopback/pcm0p/sub2/status',
    #"tv":      '/proc/asound/Loopback/pcm0p/sub0/status',
}
ALSALOOP_PROC_CHECK = "ps x | grep alsaloop | grep -v grep"
ALSALOOP_PROC_REGEX = re.compile("alsaloop -C ([a-z]+)_")

SYSINFO_COMMAND = join(BASE_DIR, 'sysinfo.sh')


def mute(value=None):
    """Get/set mute setting of master output device

    :param value: Mute master output if true, unmute if false. Do not change
        mute setting if None.
    :returns: True if master output is muted else false. None if unknown.
    """
    if value is not None:
        cmd = [AMIXER, "sset", "PCM", ("mute" if value else "unmute")]
    else:
        cmd = [AMIXER, "sget", "PCM"]
    try:
        out = check_output(cmd)
    except CalledProcessError as err:
        traceback.print_exc(file=sys.stderr)
        return None
    match = AMIXER_MUTE_EXP.search(out)
    return match.group(1) == "off" if match else None

def source(value=None):
    """Get/set selected sound source

    :param value: Set sound source if not None. Acceptable values are
        "squeeze", "tv", "airpogo" and None.
    :returns: "squeeze", "tv", "airpogo", or None.
    """
    if value in ["squeeze", "tv", "airpogo"]:
        with open(ALSALOOP_CONF, "w") as f:
            f.write(ALSALOOP_ARGS[value] + "\n")
        call([ALSALOOP_SERVICE, "restart"])
    try:
        out = check_output(ALSALOOP_PROC_CHECK, shell=True)
    except CalledProcessError as err:
        return None
    match = ALSALOOP_PROC_REGEX.search(out)
    newval = match.group(1) if match else None
    return "tv" if newval == "line" else newval

def volume(channel, value=None):
    """Get/set volume

    :param channel: Alsa mixer channel to read/adjust.
    :param value: Update volume if not None. Must be None or an
        integer between 0 and 100 inclusive.
    :returns: Volume integer between 0 and 100 inclusive.
    """
    if isinstance(value, (int, long)) and value >= 0 and value <= 100:
        percent = "{}%".format(value)
        cmd = [AMIXER, "sset", channel, percent]
    else:
        cmd = [AMIXER, "sget", channel]
    try:
        out = check_output(cmd)
    except CalledProcessError as err:
        traceback.print_exc(file=sys.stderr)
        return None
    match = AMIXER_VOLUME_EXP.search(out)
    return int(match.group(1)) if match else None

def source_stats():
    def stat(device):
        with open(device) as fh:
            return next(iter(fh), 'closed').strip() != 'closed'
    return {src: stat(device) for src, device in ALSALOOP_STATUS.items()}

def auto_source_switch():
    stats = source_stats()
    if stats.get(source()):
        return # do not switch when current source is active
    for src, status in stats.items():
        if status:
            source(src)
            break

control_map = {
    "mute": mute,
    "source": source,
    "tv_volume": partial(volume, TV_CHANNEL),
    "airpogo_volume": partial(volume, AIRPOGO_CHANNEL),
}


@route("/")
def index():
    return static_file("index.html", root=STATIC_DIR)

@route("/static/<filepath:path>")
def static(filepath):
    if not filepath or filepath == "index.html":
        return redirect("/")
    return static_file(filepath, root=STATIC_DIR)

@route("/ctl")
def get_ctl():
    """Get the state of the mixer controls"""
    return json.dumps({key: action()
        for key, action in control_map.iteritems()})

@route("/ctl", method="POST")
def set_ctl():
    """Update mixer controls and return their updated state"""
    data = request.json
    ignore = lambda value: None
    return {key: control_map.get(key, ignore)(value)
        for key, value in data.iteritems()}

@route("/system-info")
def system_info():
    try:
        out = check_output(SYSINFO_COMMAND)
        stats = sorted(k for k, v in source_stats().items() if v)
        out += "\nActive sources: %s" % " ".join(stats)
        return out
    except Exception as err:
        return "Cannot load system info:\n{}: {}\n{}" \
            .format(type(err).__name__, err, traceback.format_exc())

def setup_auto_source_switch():
    def run():
        while True:
            auto_source_switch()
            sleep(2)
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()

def main():
    parser = argparse.ArgumentParser(description="Pogo controller web server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("-p", "--port", default=80, type=int)
    parser.add_argument("--reload", action="store_true", default=False,
        help="Auto-reload on script change.")
    args = parser.parse_args()
    setup_auto_source_switch()
    run(host=args.host, port=args.port, reloader=args.reload)

if __name__ == "__main__":
    main()
