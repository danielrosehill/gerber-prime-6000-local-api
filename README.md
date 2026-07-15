# Gerber Prime 6000 — Local HTTP API (unofficial)

Reverse-engineered notes and code samples for controlling the **Gerber Prime 6000-series**
smart-home controller (relay / dimmer / roller-shutter DIN-rail box) **locally over HTTP, with
no vendor cloud**.

If you own one of these and want it in **Home Assistant / Node-RED / a script** instead of the
"Home Mate 2" phone app, this is for you. Everything here was worked out by observing the
device's own web UI — there is no official public API doc.

> ⚠️ Unofficial and community-maintained. Not affiliated with or endorsed by Gerber. Use at
> your own risk — the `switch` command actuates real relays/shutters.

## What device is this?

- Vendor: **Gerber Prime** (gerber-home.net / gerberprime.com), phone app **"Home Mate 2"**.
- DIN-rail controller, **8 outputs** via hot-plug dongles (relay / dimmer / curtain-shutter),
  8 inputs. Marketed as e.g. **GPS-6000** ("Shutter module 5A×4, Relay up to 5A×8"),
  **GPB-6000** (FCC ID `2AQO4GPB-6000`).
- The **Wi-Fi control module** identifies itself as **`PSC05`** (a sibling `PSC03` exists). Its
  config Access Point is named **`PSC05-<wifi-mac>`**.
- Embedded Linux, **Apache/2.4.12**, web UI code version **2.0.21** (2018). Internal platform
  string seen in API responses: **`PAN27`**.

If your unit's setup Wi-Fi is called `PSC05-xx:xx:xx:xx:xx:xx`, this repo applies to you.

## Default credentials (vendor defaults, from the FCC manual)

| What | Value |
|------|-------|
| Web UI / API login | **`admin` / `888888`** (HTTP Basic) |
| Config Wi-Fi (SoftAP) WPA key | **`12345678`** |
| SoftAP gateway IP | `10.10.10.254` |

*(Change these if you can. They are the shipped defaults, published in the FCC manual.)*

## Two local interfaces

The web UI is backed by two CGI endpoints (both HTTP Basic auth):

- **`/sdk.cgi`** — device control & status (turn relays on/off, read all channels, Z-Wave
  include/exclude, config params).
- **`/network.cgi`** — network / Wi-Fi config (AP↔STA mode, SSID, scan, reboot).

Full reference: **[docs/API.md](docs/API.md)**.

## Quick start

```bash
pip install requests   # optional; the sample also works with urllib
python examples/gerber_client.py --host 10.10.10.254 get-devices
# turn relay channel 3 on / off (uid comes from get-devices):
python examples/gerber_client.py --host 10.10.10.254 switch --uid 257 --chid 3 --on
python examples/gerber_client.py --host 10.10.10.254 switch --uid 257 --chid 3 --off
```

See [examples/gerber_client.py](examples/gerber_client.py) (Python client),
[examples/curl.md](examples/curl.md) (raw curl), and
[examples/home_assistant.md](examples/home_assistant.md) (HA `rest_command` sketch).

## Hard-won gotchas

- **Request encoding for `/sdk.cgi`:** the UI sends `POST` with a single form field
  `json=<encodeURIComponent(encodeURI(<json>))>`, i.e. the JSON is **double-encoded**. The
  sample client reproduces this. Responses are **URI-encoded JSON** — decode before parsing.
  `respcode: 100` = OK.
- **Switching the unit to Wi-Fi station (STA) mode via the API does NOT work reliably.** Setting
  `setstassid` / `setstapwd` / `setwifimode=STA` / `wificommit` over `/network.cgi` repeatedly
  failed to complete a join (across WPA2, WPA2/3, and even an open SSID) — the raw calls don't
  seem to set the SSID's security type. **What worked: do the STA switch from the device's own
  web UI**, picking the network from its scanned list, then **power-cycle** the unit. After that
  it joins and is reboot-stable. If you've cracked the pure-API STA path, please open a PR.
- **Old Wi-Fi stack.** In STA mode the (2018-era) client may fail to associate to APs that
  require **802.11w/PMF** or use **fast-roaming/band-steering**. If it won't join, try a
  **2.4 GHz, WPA2-PSK, PMF-disabled** SSID (or briefly an open one to prove it out).
- **Recovery:** if Wi-Fi/config gets wedged, **power-cycle** the unit (mains off/on) — this is
  non-destructive. It falls back to its config AP. **Do NOT hold the Reset button ~5 s** — that
  is a **factory reset** and wipes your scenes / channel names / bindings.
- **Modbus:** the RJ11 port is **RS485/Modbus**. The **master/slave toggle and Modbus address
  are in the web UI** (Settings → *PAN27 Information* → Modbus Mode). Default is **master**; set
  **slave** if you want to poll it from an external Modbus master (e.g. an RS485→TCP gateway).

## Data model (from `get_all_device`)

Each device has channels; each channel has a `ctrltype`/`functype`:

| ctrltype | Meaning | Control |
|----------|---------|---------|
| `23` | On/off relay ("Wall Switch") | `switch` cmd, `val` `0`=off / `255`=on |
| `26` | Roller shutter / curtain | `switch` cmd — **up/down/stop `val` mapping not yet confirmed (help wanted)** |

Shutter travel time (seconds/channel) and Modbus settings appear in a `pan27_info` block.

## Status / help wanted

- ✅ Read all devices/channels; ✅ relay on/off; ✅ Wi-Fi mode/scan/config; ✅ Modbus mode toggle.
- ❓ **Roller-shutter open/close/stop command** — not yet nailed down. PRs welcome.
- ❓ Pure-API STA-mode join (UI flow needed today).
- ❓ Dimmer channel control (`val` as brightness?).

Contributions from other Gerber Prime / PSC05 owners very welcome.

## License

MIT — see [LICENSE](LICENSE).
