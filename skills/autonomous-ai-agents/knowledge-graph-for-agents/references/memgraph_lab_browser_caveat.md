# Memgraph Lab UI: browser-side connection pitfall

When Memgraph Lab UI is exposed through a reverse proxy (Traefik, nginx,
etc.), the HTML/JS page reaches the browser from the remote server, but the
Lab UI frontend tries to open the **Bolt connection from the browser**.

By default the page is configured with:

```javascript
window.qcMgHost = '127.0.0.1';
window.qcMgPort = '7687';
```

`127.0.0.1` here means **the machine running the browser**, not the VPS. So
after you log into Lab UI, "Memgraph not detected" appears because the browser
cannot reach port 7687 on your local machine.

## Fix 1: SSH tunnel (recommended, no extra exposure)

From your local machine:

```bash
ssh -L 7687:localhost:7687 root@YOUR_VPS_IP
```

Then open `https://lab.YOUR_DOMAIN.nip.io/`, log in, and click Quick Connect.
The browser now connects to `127.0.0.1:7687` on your Mac, which tunnels to
the VPS.

Bolt port stays localhost-only on the VPS. This is the safest setup.

## Fix 2: Expose Bolt through Traefik (no SSH needed, more exposure)

Add a Traefik TCP router for port 7687 with auth, then override the Lab UI
connection host to point at that TCP endpoint. Not covered here because:

- Memgraph Lab's default host is hardcoded to `127.0.0.1`.
- You must override it in the UI each time ("Connect" → custom host).
- Exposing the Bolt protocol to the internet adds attack surface even with
  auth.

Use Fix 1 unless you genuinely cannot run an SSH tunnel.
