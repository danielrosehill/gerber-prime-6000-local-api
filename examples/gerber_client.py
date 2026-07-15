#!/usr/bin/env python3
"""
Minimal local client for the Gerber Prime 6000-series controller (PSC05 Wi-Fi module).

Talks to the device's undocumented local HTTP API (/sdk.cgi and /network.cgi) with no vendor
cloud. Pure standard library (urllib) — no dependencies.

Examples:
    python gerber_client.py --host 10.10.10.254 get-devices
    python gerber_client.py --host 10.10.10.254 switch --uid 257 --chid 3 --on
    python gerber_client.py --host 10.10.10.254 wifi-mode
    python gerber_client.py --host 10.10.10.254 scan

Defaults are the vendor defaults (admin/888888). Override with --user/--password.

WARNING: `switch` actuates real relays / shutters.
"""
import argparse
import base64
import json
import sys
import urllib.parse
import urllib.request


# JavaScript encodeURI / encodeURIComponent equivalents (the web UI double-encodes sdk payloads)
def _encode_uri(s):
    return urllib.parse.quote(s, safe="!#$&'()*+,-./:;=?@_~")


def _encode_uri_component(s):
    return urllib.parse.quote(s, safe="!'()*-._~")


class GerberClient:
    def __init__(self, host, user="admin", password="888888", timeout=10):
        self.base = f"http://{host}"
        self.timeout = timeout
        self._auth = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()

    def _post(self, path, body):
        req = urllib.request.Request(
            self.base + path,
            data=body.encode(),
            headers={
                "Authorization": self._auth,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        raw = urllib.request.urlopen(req, timeout=self.timeout).read().decode(errors="replace")
        return urllib.parse.unquote(raw)

    # ---- /sdk.cgi (control + status) ----
    def sdk(self, cmd, **fields):
        control = {"cmd": cmd}
        control.update({k: v for k, v in fields.items() if v is not None})
        payload = json.dumps({"control": control}, separators=(",", ":"))
        body = "json=" + _encode_uri_component(_encode_uri(payload))
        return json.loads(self._post("/sdk.cgi", body))

    def get_all_device(self):
        return self.sdk("get_all_device")

    def switch(self, uid, chid, on, home_id=None):
        """Set an on/off relay channel. on=True -> 255, on=False -> 0."""
        return self.sdk("switch", uid=uid, chid=chid, val=255 if on else 0, home_id=home_id)

    # ---- /network.cgi (Wi-Fi / network) ----
    def net(self, command):
        return self._post("/network.cgi?", command).split("<br>")[0].strip()

    def wifi_mode(self):
        return self.net("getwifimode")

    def scan(self):
        return [s for s in self._post("/network.cgi?", "getssidlist").split("<br>")
                if s and "done" not in s]


def _print_devices(data):
    for dev in data.get("device", []):
        print(f"device uid={dev.get('uid')} home_id={dev.get('home_id')}")
        for c in dev.get("channel", []):
            state = "on" if c.get("basicvalue") == 255 else "off"
            print(f"  chid {c['chid']:>2}  {c.get('name',''):<20} "
                  f"ctrltype={c.get('ctrltype')}  {state}")
        pi = dev.get("pan27_info")
        if pi:
            print(f"  modbus: addr={pi.get('modbus_addr')} "
                  f"is_slave={pi.get('modbus_is_slave')}  curtain_sec={pi.get('curtain_sec')}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Local client for Gerber Prime 6000 / PSC05")
    p.add_argument("--host", required=True, help="controller IP (e.g. 10.10.10.254)")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="888888")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("get-devices", help="list devices/channels + state")
    sub.add_parser("wifi-mode", help="print current Wi-Fi mode (AP/STA/OFF)")
    sub.add_parser("scan", help="list visible SSIDs")

    sw = sub.add_parser("switch", help="turn a relay channel on/off")
    sw.add_argument("--uid", type=int, required=True)
    sw.add_argument("--chid", type=int, required=True)
    sw.add_argument("--home-id", default=None)
    g = sw.add_mutually_exclusive_group(required=True)
    g.add_argument("--on", action="store_true")
    g.add_argument("--off", action="store_true")

    a = p.parse_args(argv)
    c = GerberClient(a.host, a.user, a.password)

    if a.cmd == "get-devices":
        _print_devices(c.get_all_device())
    elif a.cmd == "wifi-mode":
        print(c.wifi_mode())
    elif a.cmd == "scan":
        print("\n".join(c.scan()))
    elif a.cmd == "switch":
        r = c.switch(a.uid, a.chid, on=a.on, home_id=a.home_id)
        print("OK" if r.get("control", {}).get("respcode") == 100 else r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
