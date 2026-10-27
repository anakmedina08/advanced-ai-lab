"""Etapa 2 · Descargar a Bronze: HTML crudo + registro de captura (capture.jsonl).

Bronze nunca se edita a mano: es el respaldo histórico desde el que se regeneran
Silver y Gold sin volver a la web.
"""

import hashlib
import json
import re
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from sb_asistente.config import (
    MAX_RETRIES,
    REQUEST_DELAY_S,
    REQUEST_TIMEOUT_S,
    USER_AGENT,
)
from sb_asistente.scraping.discover import SitemapEntry, path_of


class HttpResponse(Protocol):
    """Lo mínimo que se usa de una respuesta HTTP."""

    status_code: int
    content: bytes


class HttpSession(Protocol):
    """Contrato del cliente HTTP (requests.Session lo cumple)."""

    def get(self, url: str, *, timeout: float, headers: dict[str, str]) -> HttpResponse:  # noqa: D102
        ...


@dataclass(slots=True)
class CaptureRecord:
    """Una línea de capture.jsonl."""

    url: str
    path: str
    status: int
    fetched_at: str
    file: str | None
    sha256: str | None
    bytes: int
    lastmod: str | None
    error: str | None = None


def slugify_path(path: str) -> str:
    """Convierte una ruta en nombre de archivo seguro: '/a/b-c' → 'a__b-c'."""
    if path in ("", "/"):
        return "index"
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "__", path.strip("/"))
    return slug[:150]


def load_captured(log_path: Path) -> dict[str, CaptureRecord]:
    """Lee capture.jsonl y devuelve la última captura por URL."""
    records: dict[str, CaptureRecord] = {}
    if not log_path.is_file():
        return records
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = CaptureRecord(**json.loads(line))
            records[rec.url] = rec
    return records


class BronzeFetcher:
    """Descarga páginas con cortesía (delay, timeout, reintentos) y las guarda crudas."""

    def __init__(
        self,
        session: HttpSession,
        bronze_dir: Path,
        log_path: Path,
        delay_s: float = REQUEST_DELAY_S,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        """Recibe sus dependencias por inyección (sesión HTTP, reloj y sleep)."""
        self.session = session
        self.html_dir = bronze_dir / "html"
        self.log_path = log_path
        self.delay_s = delay_s
        self.sleep = sleep
        self.now = now
        self.html_dir.mkdir(parents=True, exist_ok=True)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _get(self, url: str) -> HttpResponse:
        last_exc: Exception | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    url, timeout=REQUEST_TIMEOUT_S, headers={"User-Agent": USER_AGENT}
                )
                if response.status_code < 500:
                    return response
                last_exc = RuntimeError(f"HTTP {response.status_code}")
            except Exception as exc:  # noqa: BLE001 - se registra y se reintenta
                last_exc = exc
            if attempt < MAX_RETRIES:
                self.sleep(self.delay_s * (attempt + 2))
        raise RuntimeError(str(last_exc))

    def fetch_one(self, entry: SitemapEntry) -> CaptureRecord:
        """Descarga una URL, guarda el HTML y devuelve su registro de captura."""
        path = path_of(entry.url)
        stamp = self.now().isoformat(timespec="seconds")
        try:
            response = self._get(entry.url)
        except RuntimeError as exc:
            return CaptureRecord(entry.url, path, 0, stamp, None, None, 0, entry.lastmod, str(exc))
        body = response.content
        file_name = None
        if response.status_code == 200 and body:
            file_name = f"{slugify_path(path)}.html"
            (self.html_dir / file_name).write_bytes(body)
        return CaptureRecord(
            url=entry.url,
            path=path,
            status=response.status_code,
            fetched_at=stamp,
            file=file_name,
            sha256=hashlib.sha256(body).hexdigest() if body else None,
            bytes=len(body),
            lastmod=entry.lastmod,
        )

    def fetch_all(self, entries: Iterable[SitemapEntry], force: bool = False) -> list[CaptureRecord]:
        """Descarga todas las URLs (reanudable: salta las ya capturadas con 200)."""
        done = {} if force else load_captured(self.log_path)
        results: list[CaptureRecord] = []
        first = True
        with self.log_path.open("a", encoding="utf-8") as log:
            for entry in entries:
                previous = done.get(entry.url)
                if previous and previous.status == 200:
                    results.append(previous)
                    continue
                if not first:
                    self.sleep(self.delay_s)
                first = False
                record = self.fetch_one(entry)
                log.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
                log.flush()
                results.append(record)
        return results
