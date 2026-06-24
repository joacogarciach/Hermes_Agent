# Reference: Memgraph Lab UI Access

How to access Memgraph Lab visually from your browser.

## Preferred: Traefik reverse proxy (no SSH tunnel)

When the VPS already runs Traefik, expose Lab UI through HTTPS + bearer-token
auth. See the "Remote access via Traefik reverse proxy" section in the main
SKILL.md for the full pattern. Quick summary:

```bash
docker run -d --name memgraph-lab-ui \
  -p 127.0.0.1:3000:3000 \
  -l "traefik.enable=true" \
  -l "traefik.http.routers.memgraph-lab.entrypoints=websecure" \
  -l "traefik.http.routers.memgraph-lab.rule=Host(\`lab.72.62.243.12.nip.io\`)" \
  -l "traefik.http.routers.memgraph-lab.tls.certresolver=letsencrypt" \
  -l "traefik.http.routers.memgraph-lab.middlewares=auth@docker" \
  -l "traefik.http.services.memgraph-lab.loadbalancer.server.port=3000" \
  memgraph/lab:latest
```

Then open `https://lab.<ip>.nip.io/` in your browser with the bearer token.

## Fallback: SSH tunnel

When Traefik isn't available, use an SSH tunnel from your local machine.

## What image to run

The `memgraph/memgraph:latest` container does **not** include a web UI. Run the
separate Lab image:

```bash
docker run -d --name memgraph-lab-ui \
  -p 127.0.0.1:3000:3000 \
  --restart unless-stopped \
  memgraph/lab:latest
```

## SSH tunnel

From your local machine:

```bash
ssh -L 3000:localhost:3000 -L 7687:localhost:7687 root@YOUR_VPS_IP
```

Open http://localhost:3000 in your browser.

## Quick Connect

- Host: `127.0.0.1`
- Port: `7687`
- SSL: off
- Username/password: leave blank

## Security warning

Do not expose port 3000 or 7687 to the public internet. The free Memgraph
single-node image has no user/password authentication. A public Nginx reverse
proxy behind only basic auth + a self-signed certificate is a liability. Keep
the UI localhost-only and use an SSH tunnel (or a VPN) for remote access.
