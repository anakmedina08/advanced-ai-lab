"""Pruebas de descubrimiento y descarga a Bronze (patrón AAA, sin red)."""

import json

import pytest

from conftest import BASE, FIXTURES, FakeSession
from sb_asistente.config import USER_AGENT
from sb_asistente.scraping.discover import (
    SitemapEntry,
    build_robots,
    in_scope,
    parse_sitemap,
    path_of,
    select_urls,
)
from sb_asistente.scraping.fetch import BronzeFetcher, load_captured, slugify_path

ROBOTS = build_robots((FIXTURES / "robots.txt").read_text(), f"{BASE}/robots.txt")


def test_parse_sitemap_reads_urls_and_lastmod():
    entries, subs = parse_sitemap((FIXTURES / "sitemap.xml").read_bytes())
    assert subs == []
    assert entries[0] == SitemapEntry(f"{BASE}/", "2026-10-01")
    assert len(entries) == 7


def test_parse_sitemap_index_returns_children():
    entries, subs = parse_sitemap((FIXTURES / "sitemap_index.xml").read_text())
    assert entries == []
    assert subs[0].endswith("post-sitemap1.xml")


def test_parse_sitemap_rejects_external_entities():
    evil = (
        b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>'
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>&e;</loc></url></urlset>'
    )
    entries, _ = parse_sitemap(evil)
    assert all("root:" not in (e.url or "") for e in entries)


@pytest.mark.parametrize(("url", "path"), [(f"{BASE}/", "/"), (f"{BASE}/soat/", "/soat"), (f"{BASE}", "/")])
def test_path_of_normalizes(url, path):
    assert path_of(url) == path


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (f"{BASE}/seguro-de-hogar", True),
        (f"{BASE}/canales-de-atencion", True),
        (f"{BASE}/empresas/patrimonio/seguro-robo", False),
        (f"{BASE}/proveedores", False),
        (f"{BASE}/blog/algo", False),
        (f"{BASE}/home", False),
    ],
)
def test_in_scope_personas_y_canales(url, expected):
    assert in_scope(url) is expected


def test_robots_blocks_disallowed_paths():
    assert ROBOTS.can_fetch(USER_AGENT, f"{BASE}/RecaudosElectronicos/pagar") is False
    assert ROBOTS.can_fetch(USER_AGENT, f"{BASE}/soat") is True


def test_select_urls_filters_robots_scope_and_duplicates():
    entries, _ = parse_sitemap((FIXTURES / "sitemap.xml").read_bytes())
    selected, rejected = select_urls(entries, ROBOTS, USER_AGENT)
    reasons = dict(rejected)
    assert [path_of(e.url) for e in selected] == ["/", "/seguro-de-hogar", "/soat", "/quienes-somos"]
    assert reasons[f"{BASE}/empresas/patrimonio/seguro-robo"] == "fuera de alcance"
    assert reasons[f"{BASE}/RecaudosElectronicos/pagar"] == "robots.txt"
    assert reasons[f"{BASE}/soat/"] == "duplicada"


@pytest.mark.parametrize(("path", "slug"), [("/", "index"), ("/a/b-c", "a__b-c"), ("/x?y=1", "x__y__1")])
def test_slugify_path(path, slug):
    assert slugify_path(path) == slug


def test_fetch_one_saves_html_and_hash(tmp_path, session):
    fetcher = BronzeFetcher(session, tmp_path, tmp_path / "capture.jsonl", sleep=lambda s: None)
    rec = fetcher.fetch_one(SitemapEntry(f"{BASE}/soat"))
    assert rec.status == 200
    assert (tmp_path / "html" / "soat.html").is_file()
    assert len(rec.sha256) == 64


def test_fetch_one_sends_identifiable_user_agent(tmp_path):
    seen = {}

    class Spy(FakeSession):
        def get(self, url, *, timeout, headers):
            seen.update(headers)
            return super().get(url, timeout=timeout, headers=headers)

    BronzeFetcher(Spy(), tmp_path, tmp_path / "c.jsonl", sleep=lambda s: None).fetch_one(
        SitemapEntry(f"{BASE}/soat")
    )
    assert "UAO" in seen["User-Agent"]


def test_fetch_one_404_is_recorded_without_file(tmp_path, session):
    rec = BronzeFetcher(session, tmp_path, tmp_path / "c.jsonl", sleep=lambda s: None).fetch_one(
        SitemapEntry(f"{BASE}/no-existe")
    )
    assert rec.status == 404 and rec.file is None


def test_fetch_retries_on_server_error_then_succeeds(tmp_path):
    session = FakeSession(fail={f"{BASE}/soat": [503]})
    sleeps: list[float] = []
    rec = BronzeFetcher(session, tmp_path, tmp_path / "c.jsonl", sleep=sleeps.append).fetch_one(
        SitemapEntry(f"{BASE}/soat")
    )
    assert rec.status == 200
    assert session.calls.count(f"{BASE}/soat") == 2
    assert sleeps  # esperó antes de reintentar


def test_fetch_gives_up_after_retries(tmp_path):
    session = FakeSession(fail={f"{BASE}/soat": [ConnectionError("x")] * 5})
    rec = BronzeFetcher(session, tmp_path, tmp_path / "c.jsonl", sleep=lambda s: None).fetch_one(
        SitemapEntry(f"{BASE}/soat")
    )
    assert rec.status == 0 and "x" in rec.error


def test_fetch_all_waits_between_requests_and_logs(tmp_path, session):
    sleeps: list[float] = []
    fetcher = BronzeFetcher(session, tmp_path, tmp_path / "c.jsonl", delay_s=1.5, sleep=sleeps.append)
    fetcher.fetch_all([SitemapEntry(f"{BASE}/soat"), SitemapEntry(f"{BASE}/seguro-de-hogar")])
    lines = (tmp_path / "c.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["status"] == 200
    assert sleeps == [1.5]


def test_fetch_all_is_resumable(tmp_path, session):
    log = tmp_path / "c.jsonl"
    entries = [SitemapEntry(f"{BASE}/soat")]
    BronzeFetcher(session, tmp_path, log, sleep=lambda s: None).fetch_all(entries)
    session.calls.clear()
    BronzeFetcher(session, tmp_path, log, sleep=lambda s: None).fetch_all(entries)
    assert session.calls == []
    assert len(load_captured(log)) == 1


def test_fetch_all_force_downloads_again(tmp_path, session):
    log = tmp_path / "c.jsonl"
    entries = [SitemapEntry(f"{BASE}/soat")]
    BronzeFetcher(session, tmp_path, log, sleep=lambda s: None).fetch_all(entries)
    session.calls.clear()
    BronzeFetcher(session, tmp_path, log, sleep=lambda s: None).fetch_all(entries, force=True)
    assert session.calls == [f"{BASE}/soat"]
