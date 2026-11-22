#!/usr/bin/env python3
"""Serve the shared assembly viewer for every project in this repo.

A project shows up when it has binary STLs in <project>/preview/.
Optional <project>/preview.json sets the title, part colors, tilt,
named cameras, and groups (two poses in one folder).

    python3 tools/preview_server.py

Open http://127.0.0.1:8765/ and pick a project, or go straight to
http://127.0.0.1:8765/?project=aio_frame
"""
import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viewer", "index.html")

_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_STL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*\.stl$", re.IGNORECASE)


def read_manifest(name):
    path = os.path.join(ROOT, name, "preview.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(name + "/preview.json must be a JSON object")
    return data


def stl_names(preview_dir):
    if not os.path.isdir(preview_dir):
        return []
    names = []
    for entry in os.listdir(preview_dir):
        if not _STL.match(entry):
            continue
        if os.path.isfile(os.path.join(preview_dir, entry)):
            names.append(entry)
    names.sort()
    return names


def projects():
    found = []
    for name in sorted(os.listdir(ROOT)):
        if not _NAME.match(name):
            continue
        folder = os.path.join(ROOT, name)
        if not os.path.isdir(folder):
            continue
        files = stl_names(os.path.join(folder, "preview"))
        if files:
            found.append((name, files))
    return found


def stl_path(project, filename):
    if not _NAME.match(project) or not _STL.match(filename):
        return None
    root = os.path.realpath(os.path.join(ROOT, project, "preview"))
    path = os.path.realpath(os.path.join(root, filename))
    if not path.startswith(root + os.sep):
        return None
    if not os.path.isfile(path):
        return None
    return path


def group_names(manifest):
    if not isinstance(manifest, dict):
        return []
    groups = manifest.get("groups")
    if not isinstance(groups, dict):
        return []
    return [key for key, value in groups.items() if isinstance(key, str) and isinstance(value, str)]


def title_of(manifest, name):
    if isinstance(manifest, dict) and isinstance(manifest.get("title"), str):
        return manifest["title"]
    return name


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        parts = [p for p in path.split("/") if p]
        try:
            if not parts or parts == ["index.html"]:
                self._file(VIEWER, "text/html; charset=utf-8")
            elif parts == ["api", "projects"]:
                self._project_list()
            elif len(parts) == 3 and parts[0] == "api" and parts[1] == "project":
                self._project(parts[2])
            elif len(parts) == 3 and parts[0] == "mesh":
                self._mesh(parts[1], parts[2])
            else:
                self._json(404, {"error": "not found"})
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._json(500, {"error": str(exc)})

    def _project_list(self):
        items = []
        for name, _files in projects():
            manifest = None
            try:
                manifest = read_manifest(name)
            except (OSError, ValueError, json.JSONDecodeError):
                manifest = None
            items.append({
                "name": name,
                "title": title_of(manifest, name),
                "groups": group_names(manifest),
            })
        self._json(200, items)

    def _project(self, name):
        if not _NAME.match(name):
            self._json(404, {"error": "unknown project"})
            return
        files = stl_names(os.path.join(ROOT, name, "preview"))
        if not files:
            self._json(404, {"error": "unknown project"})
            return
        self._json(200, {
            "name": name,
            "files": files,
            "manifest": read_manifest(name),
        })

    def _mesh(self, project, filename):
        path = stl_path(project, filename)
        if path is None:
            self._json(404, {"error": "mesh not found"})
            return
        self._file(path, "model/stl")

    def _file(self, path, content_type):
        if not os.path.isfile(path):
            self._json(500, {"error": "missing " + os.path.basename(path)})
            return
        size = os.path.getsize(path)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(256 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _json(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser(description="Preview assembled meshes for any project.")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    httpd = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"http://{args.bind}:{args.port}/", flush=True)
    for name, _files in projects():
        print(f"  ?project={name}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
