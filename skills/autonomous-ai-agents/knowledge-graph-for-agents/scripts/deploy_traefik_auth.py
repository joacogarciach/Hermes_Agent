#!/usr/bin/env python3
"""Create the auth files and deploy the Traefik ForwardAuth helper container.

Run this on the VPS to add bearer-token + Basic-auth protection to Memgraph
services exposed through Traefik.
"""
import base64
import secrets
import subprocess

TOKEN_PATH = "/docker/traefik/auth_token.txt"
BEARER_PATH = "/docker/traefik/auth_bearer.txt"
BASIC_PATH = "/docker/traefik/auth_basic.txt"


def main():
    token = secrets.token_urlsafe(32)

    # Write files directly with Python so the shell never sees the token.
    for path, content in [
        (TOKEN_PATH, token),
        (BEARER_PATH, f"Bearer {token}"),
        (BASIC_PATH, "Basic " + base64.b64encode(f"memgraph:{token}".encode()).decode()),
    ]:
        with open(path, "w") as f:
            f.write(content)
        print(f"wrote {path} ({len(content)} bytes)")

    print(f"\nUsername: memgraph")
    print(f"Password: {token}\n")

    # Restart the auth server container.
    subprocess.run(["docker", "rm", "-f", "traefik-auth"], check=False)
    subprocess.run(
        [
            "docker", "run", "-d",
            "--name", "traefik-auth",
            "-p", "127.0.0.1:9000:9000",
            "-v", "/docker/traefik/auth_server.py:/auth_server.py:ro",
            "-v", f"{BEARER_PATH}:/auth_bearer.txt:ro",
            "-v", f"{BASIC_PATH}:/auth_basic.txt:ro",
            "--entrypoint", "python3",
            "python:3.12-slim",
            "/auth_server.py",
        ],
        check=True,
    )
    print("traefik-auth container started")


if __name__ == "__main__":
    main()
