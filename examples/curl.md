# Raw `curl` examples

Replace `CONTROLLER` with your unit's IP (e.g. `10.10.10.254` on its config AP, or its LAN IP
once in STA mode). Default auth is `admin:888888`.

## `/sdk.cgi` — the `json` field is double-encoded (`encodeURIComponent(encodeURI(...))`)

The simplest robust way is to let a tiny Python one-liner do the encoding:

```bash
CONTROLLER=10.10.10.254
enc() { python3 -c 'import sys,urllib.parse as u;
s=sys.argv[1];
eu=u.quote(s,safe="!#$&%\x27()*+,-./:;=?@_~");
print("json="+u.quote(eu,safe="!\x27()*-._~"))' "$1"; }

# list all devices/channels
curl -s -u admin:888888 --data "$(enc '{"control":{"cmd":"get_all_device"}}')" \
     "http://$CONTROLLER/sdk.cgi" | python3 -c 'import sys,urllib.parse as u;print(u.unquote(sys.stdin.read()))'

# turn relay uid=257 chid=3 ON (val 255) / OFF (val 0)
curl -s -u admin:888888 --data "$(enc '{"control":{"cmd":"switch","uid":257,"chid":3,"val":255}}')" \
     "http://$CONTROLLER/sdk.cgi"
curl -s -u admin:888888 --data "$(enc '{"control":{"cmd":"switch","uid":257,"chid":3,"val":0}}')" \
     "http://$CONTROLLER/sdk.cgi"
```

Responses are URI-encoded JSON; pipe through the `urllib.parse.unquote` one-liner above to read
them. `respcode:100` = OK.

## `/network.cgi` — raw command string in the body

```bash
curl -s -u admin:888888 --data "getwifimode"  "http://$CONTROLLER/network.cgi?"
curl -s -u admin:888888 --data "getssidlist"  "http://$CONTROLLER/network.cgi?"
curl -s -u admin:888888 --data "getstassid"   "http://$CONTROLLER/network.cgi?"
```
