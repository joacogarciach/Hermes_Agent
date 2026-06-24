# Memgraph Lab UI setup behind Nginx

Recipe for exposing Memgraph Lab from a VPS to a browser with basic auth and
WebSocket support. Used for the Job Impulse Japan K.K. recruiting OS shared
knowledge graph.

## Layout

- `memgraph-hub` container: Memgraph database, bound to `127.0.0.1:7687`.
- `memgraph-lab-ui` container: Memgraph Lab web UI. Use `--network host` so it
  can reach `127.0.0.1:3000` (Lab's default port) from the host.
- `nginx-memgraph-lab` container: reverse proxy `https://VPS_IP:8444` →
  `http://127.0.0.1:3000` with basic auth and WebSocket upgrade headers.

## Why not just port-forward?

A plain SSH TCP tunnel (`ssh -L 7444:localhost:7444`) often fails because
Memgraph Lab requires WebSocket upgrade headers. The `memgraph/memgraph` image
also does not serve the Lab UI on port 7444 — it serves Bolt-ish protocol, so
browsers show "WebSocket handshake Upgrade field is missing". The fix is a
separate `memgraph/lab` container + Nginx proxy.

## Files

Create under the project repo (e.g. `nginx-memgraph-lab/`):

### `.htpasswd`

Generate with `openssl passwd -apr1 <password>`:

```bash
openssl passwd -apr1 YOUR_PASSWORD > .htpasswd.tmp
printf 'rec-auth-app:%s\n' "$(cat .htpasswd.tmp)" > .htpasswd
rm .htpasswd.tmp
```

### Self-signed SSL cert

```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/nginx.key -out ssl/nginx.crt \
  -subj "/C=JP/O=JobImpulse/CN=memgraph-lab"
```

### `memgraph-lab.conf`

```nginx
server {
    listen 8444 ssl;

    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;

    auth_basic "Memgraph Lab";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Containers

```bash
# Memgraph database (localhost only)
docker run -d --name memgraph-hub \
  -p 127.0.0.1:7687:7687 -p 127.0.0.1:7444:7444 \
  --restart unless-stopped \
  memgraph/memgraph:latest

# Memgraph Lab UI (host network, reaches localhost:7687)
docker run -d --name memgraph-lab-ui \
  --network host \
  --restart unless-stopped \
  memgraph/lab:latest

# Nginx proxy
docker run -d --name nginx-memgraph-lab --network host \
  -v /path/to/nginx-memgraph-lab/memgraph-lab.conf:/etc/nginx/conf.d/default.conf:ro \
  -v /path/to/nginx-memgraph-lab/ssl:/etc/nginx/ssl:ro \
  -v /path/to/nginx-memgraph-lab/.htpasswd:/etc/nginx/.htpasswd:ro \
  --restart unless-stopped nginx:alpine
```

## Browser access

1. Open `https://VPS_IP:8444`.
2. Accept the self-signed certificate warning.
3. Enter basic-auth credentials.
4. Quick Connect: host `127.0.0.1`, port `7687`, SSL off, no username/password.

## SSH tunnel alternative

If you prefer no public exposure, keep all ports localhost-only and tunnel
both Lab and Bolt:

```bash
ssh -L 3000:localhost:3000 -L 7687:localhost:7687 root@VPS_IP
```

Then open `http://localhost:3000` and connect to `bolt://localhost:7687`.

## Pitfalls

- `memgraph/memgraph` does not serve the Lab UI. You need `memgraph/lab`.
- Lab's default config hardcodes `127.0.0.1:7687` in the page, so the browser
  must be able to reach `localhost:7687` (tunnel) or the Lab container must run
  on the same machine as Memgraph (host network).
- Plain `ssh -L 7444:localhost:7444` fails because 7444 in the database image
  is not HTTP/WebSocket.
- Choose an Nginx port that does not collide with Tailscale (`8443` may be in
  use); `8444` worked in practice.
