#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import urllib.parse
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


WEBSITE_ROOT = Path(__file__).resolve().parent
STATIC_ROOT  = WEBSITE_ROOT / "static"
SAMPLES_JSON = WEBSITE_ROOT / "static" / "data" / "samples.json"


@dataclass
class Sample:
    sample_id: str
    key: str
    category: str
    modality: str
    question: str
    explanation: str | None
    clarification: str | None
    answer: str | None
    media_url: str | None
    media_exists: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id":            self.sample_id,
            "key":           self.key,
            "category":      self.category,
            "modality":      self.modality,
            "question":      self.question,
            "explanation":   self.explanation,
            "clarification": self.clarification,
            "answer":        self.answer,
            "media_url":     self.media_url,
            "media_exists":  self.media_exists,
        }


def _sample_matches(sample: Sample, modality: str, search: str) -> bool:
    if modality != "all" and sample.modality != modality:
        return False
    if not search:
        return True
    haystack = " ".join([
        sample.key,
        sample.question,
        sample.explanation or "",
        sample.clarification or "",
        sample.answer or "",
    ]).lower()
    return search in haystack


def _filter_samples(modality: str = "all", search: str = "") -> list[Sample]:
    normalized_search = search.strip().lower()
    return [s for s in SAMPLES if _sample_matches(s, modality=modality, search=normalized_search)]


def _load_samples() -> tuple[list[Sample], dict[str, Any]]:
    payload = json.loads(SAMPLES_JSON.read_text(encoding="utf-8"))
    stats = payload["stats"]
    samples = [
        Sample(
            sample_id=r["id"],
            key=r["key"],
            category=r["category"],
            modality=r["modality"],
            question=r["question"],
            explanation=r.get("explanation"),
            clarification=r.get("clarification"),
            answer=r.get("answer"),
            media_url=r.get("media_url"),
            media_exists=r.get("media_exists", False),
        )
        for r in payload["samples"]
    ]
    return samples, stats


SAMPLES, STATS = _load_samples()
SAMPLE_INDEX = {s.sample_id: s for s in SAMPLES}


class ViewerHandler(BaseHTTPRequestHandler):
    server_version = "OmniUnViewer/0.1"

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/":
            self._serve_file(STATIC_ROOT / "index.html")
            return
        if path.startswith("/static/media/"):
            relative = path.removeprefix("/static/")
            self._serve_media(STATIC_ROOT / relative)
            return
        if path.startswith("/static/"):
            relative = path.removeprefix("/static/")
            self._serve_file(STATIC_ROOT / relative)
            return
        if path == "/api/stats":
            self._send_json(STATS)
            return
        if path == "/api/samples":
            self._handle_samples(parsed.query)
            return
        if path == "/api/category_examples":
            self._handle_category_examples(parsed.query)
            return
        if path.startswith("/api/sample/"):
            sample_id = urllib.parse.unquote(path.removeprefix("/api/sample/"))
            sample = SAMPLE_INDEX.get(sample_id)
            if sample is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown sample id")
                return
            self._send_json(sample.to_dict())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _handle_samples(self, query_string: str) -> None:
        query = urllib.parse.parse_qs(query_string)
        modality = query.get("modality", ["all"])[0]
        search = query.get("search", [""])[0]
        limit = min(max(int(query.get("limit", ["60"])[0]), 1), 250)
        offset = max(int(query.get("offset", ["0"])[0]), 0)

        filtered = _filter_samples(modality=modality, search=search)
        total = len(filtered)
        page = filtered[offset : offset + limit]
        self._send_json(
            {
                "total": total,
                "offset": offset,
                "limit": limit,
                "items": [sample.to_dict() for sample in page],
            }
        )

    def _handle_category_examples(self, query_string: str) -> None:
        query = urllib.parse.parse_qs(query_string)
        modality = query.get("modality", ["all"])[0]
        search = query.get("search", [""])[0]
        per_category = min(max(int(query.get("per_category", ["5"])[0]), 1), 20)

        filtered = _filter_samples(modality=modality, search=search)
        grouped: dict[str, list[Sample]] = {}
        for sample in filtered:
            grouped.setdefault(sample.category, [])
            if len(grouped[sample.category]) < per_category:
                grouped[sample.category].append(sample)

        ordered_categories = sorted(grouped)
        groups = [
            {
                "category": category,
                "items": [sample.to_dict() for sample in grouped[category]],
            }
            for category in ordered_categories
            if grouped[category]
        ]

        total = sum(len(group["items"]) for group in groups)
        self._send_json(
            {
                "modality": modality,
                "per_category": per_category,
                "total": total,
                "groups": groups,
            }
        )

    def _serve_file(self, path: Path) -> None:
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        if STATIC_ROOT not in resolved.parents and resolved != STATIC_ROOT / "index.html":
            self.send_error(HTTPStatus.FORBIDDEN, "Forbidden")
            return

        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        data = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _serve_media(self, path: Path) -> None:
        if not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "Media file not found")
            return
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        file_size = path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header:
            units, _, range_spec = range_header.partition("=")
            if units != "bytes" or "-" not in range_spec:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return
            start_text, _, end_text = range_spec.partition("-")
            start = int(start_text) if start_text else 0
            end = int(end_text) if end_text else file_size - 1
            end = min(end, file_size - 1)
            if start > end or start >= file_size:
                self.send_error(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                return

            length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", content_type)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.end_headers()
            with path.open("rb") as handle:
                handle.seek(start)
                self.wfile.write(handle.read(length))
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)

    def _send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the OmniUn generated data viewer.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8008)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ViewerHandler)
    print(
        f"Serving OmniUn viewer at http://{args.host}:{args.port} "
        f"with {len(SAMPLES)} indexed samples"
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
