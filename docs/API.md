# Gerber Prime 6000 — Local API reference (unofficial)

Reverse-engineered from the device's web UI (`js/global.js`, code v2.0.21). All requests use
**HTTP Basic auth** (`admin` / `888888` by default) against the controller's IP.

---

## `/sdk.cgi` — device control & status

**Request:** `POST /sdk.cgi`, body = one form field `json`, whose value is the command object
serialized as JSON then **`encodeURIComponent(encodeURI(<json>))`** (double-encoded, as the UI
does it).

Command object shape:

```json
{"control":{"cmd":"<command>","uid":<int>,"chid":<int>,"val":<int|array>,"home_id":"<id>"}}
```

Only `cmd` is always required; the rest depend on the command.

**Response:** a **URI-encoded** JSON string — URI-decode it, then parse. Success is
`respcode: 100`, `respmsg: "OK"`.

### Commands

| `cmd` | Fields | Purpose |
|-------|--------|---------|
| `get_all_device` | — | Full inventory: every device + channel + state (read-only). |
| `getdevice` | `uid` | One device. |
| `getinterface` | — | Gateway/interface info. |
| `switch` | `uid`, `chid`, `val` (`0`/`255` for relays), `home_id` | **Set a channel.** |
| `switch_color_set` | `uid`, `val` | RGB colour set. |
| `configuration_set` / `configuration_get` | `uid`, `val` | Device config parameters. |
| `include` / `exclude` / `abort` | `uid` | Z-Wave pairing (variants with a Z-Wave dongle). |
| `deldevice` | `uid` | Remove a device. |
| `zwnosecure` | `uid` | Z-Wave security setting. |

> The UI helper is `Switch(uid, chid, val, home_id)` → `{"control":{"cmd":"switch", ...}}`.

### `get_all_device` response (shape)

```jsonc
{
  "control": {"cmd":"get_all_device","respcode":100,"respmsg":"OK"},
  "device": [{
    "uid": 257,
    "home_id": "PAN27",
    "version": "PAN27",
    "channel": [
      {"chid":1,"name":"Wall Switch 0-1","ctrltype":23,"functype":23,"basicvalue":0, ...},
      {"chid":7,"name":"Roller Shutter 0-7","ctrltype":26,"functype":26,"basicvalue":0, ...}
    ],
    "pan27_info": {
      "curtain_sec": [0,0,0,0,0,0,20,0],   // shutter travel time (s) per channel
      "key_type":    [1,1,1,1,2,1,1,1],
      "modbus_addr": 1,
      "modbus_is_slave": 0                  // 0 = master, 1 = slave
    }
  }]
}
```

- `basicvalue`: `0` = off, `255` = on (for relay channels).
- `ctrltype` / `functype`: `23` = on/off relay, `26` = roller shutter. (Dimmer TBD.)

---

## `/network.cgi` — network / Wi-Fi config

**Request:** `POST /network.cgi?`, body = the **raw command string** (not JSON). For setters the
form is `name=value`. **Response** is URI-encoded text ending `...<br><cmd> done`.

| Command | Purpose |
|---------|---------|
| `getwifimode` | Returns `AP`, `STA`, or `OFF`. |
| `setwifimode=AP` \| `STA` \| `OFF` | Set Wi-Fi mode (no AP+STA coexistence). |
| `getssidlist` | Scan — returns visible SSIDs (`<br>`-separated). |
| `getstassid` / `setstassid=<ssid>` | Station (client) SSID to join. |
| `setstapwd=<pwd>` | Station password (empty for open networks). |
| `getapssid` / `setapssid=<ssid>` | This unit's own AP SSID. |
| `setappwd=<pwd>` | This unit's own AP password. |
| `wificommit` | Apply Wi-Fi changes — **reboots the unit**. |
| `jsongetall` / `jsongetuserdata` | App/user data blobs. |

**Save sequence the UI uses** (order matters):

```
STA:  setstassid=<ssid> → setstapwd=<pwd> → setwifimode=STA → wificommit
AP:   setapssid=<ssid>  → setappwd=<pwd>  → setwifimode=AP  → wificommit
OFF:  setwifimode=OFF   → wificommit
```

> ⚠️ In testing, driving the STA switch purely through these calls **did not complete a join**
> (the security type of the target SSID isn't set this way). Doing the STA switch from the web
> UI (selecting the network from the scanned list) and then power-cycling **did** work. See the
> README "gotchas". PRs with a working pure-API STA method welcome.

---

## Request encoding reference

```python
import urllib.parse
# JavaScript encodeURI / encodeURIComponent equivalents:
def encodeURI(s):          return urllib.parse.quote(s, safe="!#$&'()*+,-./:;=?@_~")
def encodeURIComponent(s): return urllib.parse.quote(s, safe="!'()*-._~")

# /sdk.cgi body:
body = "json=" + encodeURIComponent(encodeURI(json_string))
# /network.cgi body is just the raw command string, e.g. "getwifimode"
```
