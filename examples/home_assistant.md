# Home Assistant integration (sketch)

> **Recommended path:** use the dedicated
> [gerber-prime-6000-mqtt-bridge](https://github.com/danielrosehill/gerber-prime-6000-mqtt-bridge)
> instead — MQTT discovery auto-creates switches + positional shutter covers, with
> availability, and needs no HA YAML. The sketch below is the raw-YAML alternative (note:
> HA 2024.x+ removed the legacy template switch/cover platform syntax this sketch used, so
> adapt to the modern `template:` format if you go this way).

Shutter semantics (since confirmed from the UI JS): roller-shutter channels are
**positional** — `switch` with `val` 0–99 (0 = closed); the controller does the time-based
travel itself. **There is no stop command.**

The controller exposes on/off relays over `/sdk.cgi`, so you can drive them from HA with
`rest_command` + a `command_line`/`rest` sensor for state. Because the `json` field is
double-encoded and the values are fixed per channel, the simplest approach is a **precomputed
payload per relay+state**.

> Replace `CONTROLLER_IP` with your unit's (static-reserved) LAN IP, and `UID` with the `uid`
> from `get_all_device`. This is a starting point, not a finished integration — a roller-shutter
> `cover` needs the up/down/stop command, which isn't confirmed yet (see repo README).

## Generate the encoded payloads

```bash
# prints the `json=...` body for a given uid/chid/val
python3 -c 'import sys,urllib.parse as u;
s=sys.argv[1];
eu=u.quote(s,safe="!#$&%\x27()*+,-./:;=?@_~");
print(u.quote(eu,safe="!\x27()*-._~"))' \
  "{\"control\":{\"cmd\":\"switch\",\"uid\":257,\"chid\":3,\"val\":255}}"
```

## `configuration.yaml`

```yaml
rest_command:
  gerber_switch:
    url: "http://CONTROLLER_IP/sdk.cgi"
    method: POST
    username: admin
    password: "888888"
    content_type: "application/x-www-form-urlencoded"
    # payload is the pre-encoded json=... string (generate per uid/chid/val as above)
    payload: "{{ body }}"

# Poll all channel states once, expose as an attribute-rich sensor
command_line:
  - sensor:
      name: gerber_state
      scan_interval: 15
      command: >-
        curl -s -u admin:888888
        --data 'json=%7B%22control%22%3A%7B%22cmd%22%3A%22get_all_device%22%7D%7D'
        http://CONTROLLER_IP/sdk.cgi
      value_template: "ok"
      json_attributes:
        - device

# Example: one relay as a template switch (chid 3)
template:
  - switch:
      - name: "Gerber Relay 3"
        state: >-
          {% set ch = (state_attr('sensor.gerber_state','device')[0].channel
                       | selectattr('chid','eq',3) | first) %}
          {{ ch.basicvalue == 255 if ch else false }}
        turn_on:
          service: rest_command.gerber_switch
          data:
            body: "json=<PRE-ENCODED switch uid/chid=3 val=255>"
        turn_off:
          service: rest_command.gerber_switch
          data:
            body: "json=<PRE-ENCODED switch uid/chid=3 val=0>"
```

Repeat the `template.switch` block per relay channel. Debounce/poll gently — RS485-backed
devices are slow.
