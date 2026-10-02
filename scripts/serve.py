#!/usr/bin/env python3
"""Serve only generated public files; source CVs are outside the document root."""
import argparse
import subprocess
import sys
import tempfile
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", type=int, default=8787)
parser.add_argument("--background", action="store_true", help="Run a detached preview that stays available after the chat ends")
args = parser.parse_args()
root = Path(__file__).resolve().parents[1] / "_site"
if not (root / "index.html").is_file():
    parser.error("Run python3 scripts/build.py first.")
if args.background:
    log_path = Path(tempfile.gettempdir()) / f"xiufeng-website-preview-{args.port}.log"
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--port", str(args.port)],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    for _ in range(40):
        if process.poll() is not None:
            raise SystemExit("Preview failed to start:\n" + log_path.read_text(encoding="utf-8")[-1500:])
        try:
            with urlopen(f"http://127.0.0.1:{args.port}/", timeout=0.5) as response:
                if response.status == 200:
                    print(f"Background preview started (PID {process.pid}).", flush=True)
                    print(f"Website: http://127.0.0.1:{args.port}/", flush=True)
                    print(f"Design options: http://127.0.0.1:{args.port}/preview/", flush=True)
                    print(f"Log: {log_path}", flush=True)
                    sys.exit(0)
        except OSError:
            pass
        time.sleep(0.1)
    raise SystemExit(f"Preview did not become ready. Check {log_path}.")
server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=str(root)))
print(f"Website: http://127.0.0.1:{args.port}/", flush=True)
print(f"Design options: http://127.0.0.1:{args.port}/preview/", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
