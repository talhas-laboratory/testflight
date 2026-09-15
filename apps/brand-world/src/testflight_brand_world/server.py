"""Read-only HTTP server for the Brand World canvas."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from testflight_brand_world.projection import build_record_dossier, build_world_projection


class _State:
    def __init__(self, root: Path, workspace: Path) -> None:
        self.root = root
        self.workspace = workspace
        self.static = Path(__file__).with_name("static")
        self.tokens = root / "packages" / "testflight-design-language" / "tokens.css"

    def projection(self) -> dict[str, object]:
        return build_world_projection(self.root, self.workspace)

    def dossier(self, record_id: str) -> dict[str, object]:
        return build_record_dossier(self.root, self.workspace, record_id)


def _handler(state: _State) -> type[BaseHTTPRequestHandler]:
    class BrandWorldHandler(BaseHTTPRequestHandler):
        def _send(self, content: bytes, content_type: str, status: int = 200) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(content)

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path == "/api/world":
                try:
                    payload = json.dumps(state.projection()).encode()
                except (OSError, ValueError, KeyError) as error:
                    payload = json.dumps({"error": str(error)}).encode()
                    self._send(payload, "application/json; charset=utf-8", 500)
                    return
                self._send(payload, "application/json; charset=utf-8")
                return
            if path.startswith("/api/records/"):
                record_id = unquote(path.removeprefix("/api/records/"))
                try:
                    payload = json.dumps(state.dossier(record_id)).encode()
                except KeyError:
                    payload = json.dumps({"error": f"unknown record: {record_id}"}).encode()
                    self._send(payload, "application/json; charset=utf-8", 404)
                    return
                except (OSError, ValueError) as error:
                    payload = json.dumps({"error": str(error)}).encode()
                    self._send(payload, "application/json; charset=utf-8", 500)
                    return
                self._send(payload, "application/json; charset=utf-8")
                return
            if path == "/design/tokens.css":
                self._send(state.tokens.read_bytes(), "text/css; charset=utf-8")
                return
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/index.html": ("index.html", "text/html; charset=utf-8"),
                "/styles.css": ("styles.css", "text/css; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
            }
            if path not in assets:
                self._send(b"Not found", "text/plain; charset=utf-8", 404)
                return
            filename, content_type = assets[path]
            self._send((state.static / filename).read_bytes(), content_type)

        def log_message(self, format: str, *args: object) -> None:
            return

    return BrandWorldHandler


def serve(root: Path, workspace: Path, host: str, port: int) -> None:
    state = _State(root, workspace)
    projection = state.projection()
    server = ThreadingHTTPServer((host, port), _handler(state))
    print(
        f"Brand World Canvas: http://{host}:{port} "
        f"({len(projection['nodes'])} records, {len(projection['edges'])} relations)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


__all__ = ["serve"]
