"""Controlador del pipeline de datos: descubrir → Bronze → Silver → Gold."""

import json
from dataclasses import asdict
from pathlib import Path

import requests

from sb_asistente.config import (
    BRONZE_DIR,
    CAPTURE_LOG,
    GOLD_DIR,
    MIN_PAGE_CHARS,
    ROBOTS_URL,
    SILVER_DIR,
    SITEMAP_URL,
    USER_AGENT,
)
from sb_asistente.processing import clean, gold
from sb_asistente.scraping.discover import SitemapEntry, build_robots, in_scope, parse_sitemap, select_urls
from sb_asistente.scraping.fetch import BronzeFetcher, HttpSession, load_captured, slugify_path


def new_session() -> requests.Session:
    """Sesión HTTP con User-Agent identificable."""
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    return session


def discover(session: HttpSession, out_dir: Path = BRONZE_DIR) -> dict[str, object]:
    """Lee robots.txt y el sitemap, filtra el alcance y guarda el plan de captura."""
    headers = {"User-Agent": USER_AGENT}
    robots_txt = session.get(ROBOTS_URL, timeout=15, headers=headers).content.decode("utf-8", "replace")
    robots = build_robots(robots_txt, ROBOTS_URL)
    entries, subs = parse_sitemap(session.get(SITEMAP_URL, timeout=15, headers=headers).content)
    for sub in subs:  # si el sitemap principal fuera un índice
        more, _ = parse_sitemap(session.get(sub, timeout=15, headers=headers).content)
        entries.extend(more)
    selected, rejected = select_urls(entries, robots, USER_AGENT)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "robots.txt").write_text(robots_txt, encoding="utf-8")
    plan = {
        "total_sitemap": len(entries),
        "seleccionadas": [asdict(e) for e in selected],
        "descartadas": [{"url": u, "motivo": m} for u, m in rejected],
    }
    (out_dir / "plan_captura.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return plan


def scrape(session: HttpSession, out_dir: Path = BRONZE_DIR, force: bool = False) -> dict[str, int]:
    """Descarga a Bronze las URLs del plan (reanudable)."""
    plan = json.loads((out_dir / "plan_captura.json").read_text(encoding="utf-8"))
    entries = [SitemapEntry(**e) for e in plan["seleccionadas"]]
    records = BronzeFetcher(session, out_dir, out_dir / CAPTURE_LOG.name).fetch_all(entries, force=force)
    ok = sum(1 for r in records if r.status == 200)
    return {"total": len(records), "ok": ok, "fallidas": len(records) - ok}


def process(
    bronze_dir: Path = BRONZE_DIR, silver_dir: Path = SILVER_DIR, gold_dir: Path = GOLD_DIR
) -> dict[str, object]:
    """Regenera Silver y Gold desde Bronze, sin volver a la web."""
    captures = [
        r for r in load_captured(bronze_dir / CAPTURE_LOG.name).values() if r.status == 200 and r.file
    ]
    pages: list[tuple[object, str]] = []
    out_of_scope: list[str] = []
    footer = ""
    for rec in captures:
        html = (bronze_dir / "html" / rec.file).read_text(encoding="utf-8", errors="replace")
        footer = footer or clean.extract_footer(html)
        # El alcance se vuelve a aplicar aquí: si cambia en config.py, basta con `sb process`
        # (Bronze conserva la página, pero no pasa a Silver/Gold).
        if not in_scope(rec.url):
            out_of_scope.append(rec.url)
            continue
        pages.append((rec, html))

    # Deduplicar ANTES de detectar boilerplate: páginas idénticas (p. ej. "/" y
    # "/quienes-somos") harían que todo su contenido pareciera repetido.
    raw_texts: list[str] = []
    unique_pages: list[tuple[object, str]] = []
    duplicated: list[str] = []
    seen: set[str] = set()
    for rec, html in pages:
        raw = clean.trim_noise(clean.html_to_markdown(html))
        key = gold.text_hash(raw)
        if key in seen:
            duplicated.append(rec.url)
            continue
        seen.add(key)
        unique_pages.append((rec, html))
        raw_texts.append(raw)
    pages = unique_pages
    boilerplate = clean.find_boilerplate(raw_texts)
    silver_dir.mkdir(parents=True, exist_ok=True)

    docs: list[gold.GoldDoc] = []
    skipped: list[str] = []
    for (rec, html), raw in zip(pages, raw_texts, strict=True):
        text = clean.remove_lines(raw, boilerplate)
        if len(text) < MIN_PAGE_CHARS:
            skipped.append(rec.url)
            continue
        title, description = clean.extract_meta(html)
        doc_id = slugify_path(rec.path)
        (silver_dir / f"{doc_id}.txt").write_text(text, encoding="utf-8")
        docs.append(
            gold.GoldDoc(
                doc_id=doc_id,
                url=rec.url,
                title=title or clean.title_from_path(rec.path),
                description=description,
                section=gold.classify_section(rec.url),
                fetched_at=rec.fetched_at,
                sha256=rec.sha256 or "",
                text=text,
            )
        )
    pdfs = {rec.url: clean.pdf_links(html) for rec, html in pages if clean.pdf_links(html)}
    gold_dir.mkdir(parents=True, exist_ok=True)
    (gold_dir / "pdf_links.json").write_text(json.dumps(pdfs, ensure_ascii=False, indent=2), encoding="utf-8")
    docs, also_duplicated = gold.dedupe_docs(docs)
    duplicated += also_duplicated
    summary = gold.write_gold(docs, gold_dir, channels_text=footer)
    summary |= {
        "paginas_bronze": len(captures),
        "lineas_boilerplate": len(boilerplate),
        "descartadas_fuera_de_alcance": out_of_scope,
        "descartadas_cortas": skipped,
        "descartadas_duplicadas": duplicated,
        "paginas_con_pdf": len(pdfs),
    }
    (gold_dir / "resumen.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


def _read_json(path: Path) -> dict[str, object]:
    """Lee un JSON si existe; si no, devuelve un diccionario vacío."""
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def stage_report(bronze_dir: Path = BRONZE_DIR, gold_dir: Path = GOLD_DIR) -> list[dict[str, object]]:
    """Métricas de cada etapa del scraping a partir de los archivos que dejó el pipeline.

    No vuelve a la web: lee ``plan_captura.json``, ``capture.jsonl`` y ``resumen.json``.
    Devuelve una lista ordenada (descubrir → extraer → limpiar → deduplicar → enriquecer) en la que
    cada etapa trae ``etapa``, ``capa``, ``hecha`` y ``metricas`` (nombre → valor).
    """
    plan = _read_json(bronze_dir / "plan_captura.json")
    captures = list(load_captured(bronze_dir / CAPTURE_LOG.name).values())
    summary = _read_json(gold_dir / "resumen.json")
    ok = [c for c in captures if c.status == 200]
    motivos: dict[str, int] = {}
    for d in plan.get("descartadas", []):
        motivos[d["motivo"]] = motivos.get(d["motivo"], 0) + 1
    return [
        {
            "etapa": "1. Descubrir",
            "capa": "robots.txt + sitemap.xml",
            "hecha": bool(plan),
            "metricas": {
                "URLs en el sitemap": plan.get("total_sitemap", 0),
                "URLs seleccionadas": len(plan.get("seleccionadas", [])),
                "URLs descartadas": len(plan.get("descartadas", [])),
                **{f"  · {m}": n for m, n in sorted(motivos.items())},
            },
        },
        {
            "etapa": "2. Extraer",
            "capa": "Bronze (data/raw)",
            "hecha": bool(captures),
            "metricas": {
                "Páginas descargadas (200)": len(ok),
                "Fallidas": len(captures) - len(ok),
                "KB de HTML": round(sum(c.bytes for c in ok) / 1024),
            },
        },
        {
            "etapa": "3. Limpiar",
            "capa": "Silver (data/silver)",
            "hecha": bool(summary),
            "metricas": {
                "Líneas de boilerplate quitadas": summary.get("lineas_boilerplate", 0),
                "Descartadas por fuera de alcance": len(summary.get("descartadas_fuera_de_alcance", [])),
                "Descartadas por cortas": len(summary.get("descartadas_cortas", [])),
            },
        },
        {
            "etapa": "4. Deduplicar",
            "capa": "hash SHA-256 del texto",
            "hecha": bool(summary),
            "metricas": {"Páginas duplicadas descartadas": len(summary.get("descartadas_duplicadas", []))},
        },
        {
            "etapa": "5. Enriquecer",
            "capa": "Gold (data/gold)",
            "hecha": bool(summary),
            "metricas": {
                "Documentos": summary.get("documentos", 0),
                "Chunks": summary.get("chunks", 0),
                "Tokens del conocimiento (aprox.)": summary.get("tokens_conocimiento_est", 0),
                "Secciones": len(summary.get("documentos_por_seccion", {})),
            },
        },
    ]


def corpus_table(gold_dir: Path = GOLD_DIR) -> list[dict[str, object]]:
    """Metadatos de cada documento Gold (sin el texto): URL, título, sección, fecha, hash y tokens."""
    path = gold_dir / "corpus.jsonl"
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        doc = json.loads(line)
        rows.append(
            {
                "url": doc["url"],
                "titulo": doc["title"],
                "seccion": doc["section"],
                "fecha_captura": doc["fetched_at"],
                "sha256": doc["sha256"][:12],
                "tokens": doc.get("tokens_est", 0),
            }
        )
    return rows
