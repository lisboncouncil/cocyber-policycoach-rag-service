#!/usr/bin/env python3
"""Verify the running server matches the SERVER_VERSION declared in server.py.

Detects deployment drift: a stale process serving on the port while the source
tree has been bumped to a newer version (the bug fixed on 2026-05-06, when an
orphan process from Apr 30 kept port 5050 busy and systemd auto-restart looped
for 2200+ failed attempts).

Exit codes:
  0  running version == declared version
  1  versions differ
  2  server unreachable, no version field, or source unparseable
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


SERVER_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
VERSION_RE = re.compile(r'^SERVER_VERSION\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def declared_version(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        m = VERSION_RE.search(f.read())
    if not m:
        raise RuntimeError(f"SERVER_VERSION not found in {path}")
    return m.group(1)


def running_version(url: str, timeout: float, auth: str | None) -> str:
    req = urllib.request.Request(url)
    if auth:
        import base64
        req.add_header("Authorization", "Basic " + base64.b64encode(auth.encode()).decode())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    version = data.get("serverVersion")
    if not version:
        raise RuntimeError(f"response from {url} has no 'serverVersion' field")
    return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify running server version matches source.")
    parser.add_argument("--url", default=os.environ.get("HEALTHCHECK_URL", "http://localhost:5050/health"))
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--auth", default=os.environ.get("HEALTHCHECK_AUTH"),
                        help="Basic auth as user:pass (or env HEALTHCHECK_AUTH)")
    parser.add_argument("--quiet", action="store_true", help="Print only on mismatch/error")
    args = parser.parse_args()

    try:
        expected = declared_version(SERVER_PY)
    except (OSError, RuntimeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        actual = running_version(args.url, args.timeout, args.auth)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError) as e:
        print(f"ERROR: cannot read version from {args.url}: {e}", file=sys.stderr)
        return 2

    if actual == expected:
        if not args.quiet:
            print(f"OK  version={actual} ({args.url})")
        return 0

    print(f"DRIFT  running={actual}  declared={expected}  ({args.url})", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
