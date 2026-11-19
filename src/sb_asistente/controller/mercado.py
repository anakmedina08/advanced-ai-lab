"""Controlador del corpus de mercado: varias aseguradoras, mismo Medallion (SPEC-069).

Por cada aseguradora activa del registro: robots.txt + sitemap → plan → Bronze → Silver → Gold,
en ``data/{raw,silver,gold}/mercado/<id>/``. Seguros Bolívar no se vuelve a capturar: su corpus
es el del pipeline principal y aquí solo se etiqueta con ``aseguradora = "seguros-bolivar"``.

La cortesía es la misma de la Fase 1 (User-Agent identificable, 1,5 s entre peticiones,
robots.txt) y además hay un tope de páginas por aseguradora (``MERCADO_MAX_PAGINAS``), que
se llena primero con las páginas de producto para personas.
"""

import json
import time
from collections.abc import Callable, Iterable
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from sb_asistente.config import (
    BRONZE_HTML_SUBDIR,
    CHUNKS_JSONL,
    MERCADO_BRONZE_DIR,
    MERCADO_CANDIDATOS_RELEVANCIA,
    MERCADO_CAPTURA,
    MERCADO_CHUNKS_JSONL,
    MERCADO_GOLD_DIR,
    MERCADO_ID_PRINCIPAL,
    MERCADO_MAX_COMPARAR,
    MERCADO_MAX_PAGINAS,
    MERCADO_MAX_SITEMAPS,
    MERCADO_PLAN,
    MERCADO_POR_ASEGURADORA,
    MERCADO_RESUMEN_JSON,
    MERCADO_SILVER_DIR,
    MERCADO_WHATSAPP_MAX,
    MIN_PAGE_CHARS,
    REQUEST_DELAY_S,
    REQUEST_TIMEOUT_S,
    ROBOTS_RUTA,
    SECTION_RULES,
    SITEMAP_RUTA,
    USER_AGENT,
)
from sb_asistente.model.mercado import contactos, secciones
from sb_asistente.model.mercado.comparar import Oferta, comparar
from sb_asistente.model.mercado.registro import Aseguradora, cargar_registro, detectar, por_id
from sb_asistente.model.processing import clean, gold
from sb_asistente.model.rag.fuentes import fragmentos_rag
from sb_asistente.model.rag.hibrido import CorpusVacioError, RecuperadorHibrido
from sb_asistente.model.scraping.discover import (
    SitemapEntry,
    build_robots,
    parse_sitemap,
    select_urls,
)
from sb_asistente.model.scraping.fetch import BronzeFetcher, HttpSession, load_captured, slugify_path


class ClienteCortes:
    """Cliente HTTP con la cortesía de la Fase 1: pausa de ``REQUEST_DELAY_S`` entre peticiones.

    La sesión y el ``sleep`` se inyectan (las pruebas no esperan ni salen a internet). La pausa
    aplica a todas las peticiones del descubrimiento: robots.txt, sitemaps y entre aseguradoras.
    """

    def __init__(
        self,
        session: HttpSession,
        delay_s: float = REQUEST_DELAY_S,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Recibe la sesión HTTP, la pausa entre peticiones y la función de espera."""
        self.session = session
        self.delay_s = delay_s
        self.sleep = sleep
        self._primera = True

    def get(self, url: str) -> tuple[int, bytes]:
        """Estado y contenido de un recurso (0 y vacío si no se pudo conectar)."""
        if not self._primera:
            self.sleep(self.delay_s)
        self._primera = False
        try:
            r = self.session.get(url, timeout=REQUEST_TIMEOUT_S, headers={"User-Agent": USER_AGENT})
        except Exception:  # noqa: BLE001 - un sitio caído no debe detener a las demás aseguradoras
            return 0, b""
        return r.status_code, r.content


def _del_sitio(url: str, a: Aseguradora) -> bool:
    """True si la URL es del mismo host que el sitio (no basta con que empiece igual)."""
    return urlsplit(url).netloc.lower() == a.dominio.lower()


def _sitemaps(robots_txt: str, aseguradora: Aseguradora) -> list[str]:
    """Sitemaps declarados en robots.txt; si no declara ninguno, ``/sitemap.xml``."""
    declarados = [
        linea.split(":", 1)[1].strip()
        for linea in robots_txt.splitlines()
        if linea.lower().startswith("sitemap:")
    ]
    return declarados or [f"{aseguradora.sitio}{SITEMAP_RUTA}"]


def _guardar_plan(plan: dict[str, object], carpeta: Path) -> dict[str, object]:
    """Escribe el plan SIEMPRE, también cuando quedó vacío.

    Así un plan viejo nunca sobrevive a una verificación fallida: si hoy robots.txt no responde,
    ``capturar`` lee un plan sin URLs en lugar de descargar las de ayer.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / MERCADO_PLAN).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    return plan


def descubrir_una(cliente: ClienteCortes, a: Aseguradora, out_dir: Path) -> dict[str, object]:
    """robots.txt + sitemaps de una aseguradora → plan de captura (guardado en su carpeta)."""
    carpeta = out_dir / a.id
    plan: dict[str, object] = {"aseguradora": a.id, "sitio": a.sitio, "estado": "ok", "seleccionadas": []}
    robots_url = f"{a.sitio}{ROBOTS_RUTA}"
    estado, robots_bytes = cliente.get(robots_url)
    if estado not in (200, 404):
        # Sin robots.txt legible no se sabe qué permite el sitio: no se captura nada.
        return _guardar_plan(plan | {"estado": f"robots.txt no disponible (HTTP {estado})"}, carpeta)
    robots_txt = robots_bytes.decode("utf-8", "replace") if estado == 200 else ""
    robots = build_robots(robots_txt, robots_url)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / ROBOTS_RUTA.lstrip("/")).write_text(robots_txt, encoding="utf-8")
    entradas: list[SitemapEntry] = []
    # Igual que los hijos: un sitemap declarado en robots.txt solo se pide si es del mismo sitio.
    pendientes = [u for u in _sitemaps(robots_txt, a) if _del_sitio(u, a)]
    visitados = 0
    while pendientes and visitados < MERCADO_MAX_SITEMAPS:
        url = pendientes.pop(0)
        visitados += 1
        codigo, xml = cliente.get(url)
        if codigo != 200 or not xml:
            continue
        try:
            nuevas, hijos = parse_sitemap(xml)
        except Exception:  # noqa: BLE001 - XML inválido: se sigue con los demás sitemaps
            continue
        entradas.extend(e for e in nuevas if _del_sitio(e.url, a))
        # Un sitemap hijo solo se pide si es del mismo sitio y robots.txt lo permite.
        pendientes.extend(h for h in hijos if _del_sitio(h, a) and robots.can_fetch(USER_AGENT, h))
    if not entradas:
        return _guardar_plan(plan | {"estado": "sin sitemap con páginas del sitio"}, carpeta)
    excluir = list(secciones.EXCLUIR_GENERICO)
    permitidas, descartadas = select_urls(entradas, robots, USER_AGENT, exclude=())
    en_alcance = [e for e in permitidas if secciones.en_alcance(e.url, a.prefijo, excluir)]
    urls_en_alcance = {e.url for e in en_alcance}
    fuera = [(e.url, "fuera de alcance") for e in permitidas if e.url not in urls_en_alcance]
    elegidas = set(secciones.ordenar_por_prioridad((e.url for e in en_alcance), MERCADO_MAX_PAGINAS))
    seleccionadas = [e for e in en_alcance if e.url in elegidas]
    plan |= {
        "total_sitemap": len(entradas),
        "seleccionadas": [asdict(e) for e in seleccionadas],
        "descartadas": [{"url": u, "motivo": m} for u, m in [*descartadas, *fuera]],
        "recortadas_por_tope": len(en_alcance) - len(seleccionadas),
    }
    return _guardar_plan(plan, carpeta)


def activas(registro: Iterable[Aseguradora], solo: Iterable[str] = ()) -> list[Aseguradora]:
    """Aseguradoras a las que se les hace scraping (todas las activas, o solo los ids pedidos).

    Un id pedido que no existe o que no hace scraping es un error (un tipeo no pasa en silencio).
    """
    lista = list(registro)
    pedidas = list(dict.fromkeys(solo))
    validas = {a.id for a in lista if a.hace_scraping}
    malas = [i for i in pedidas if i not in validas]
    if malas:
        raise KeyError(f"No están en el registro o no hacen scraping: {', '.join(malas)}")
    return [a for a in lista if a.id in validas and (not pedidas or a.id in pedidas)]


def descubrir(
    session: HttpSession,
    registro: Iterable[Aseguradora],
    solo: Iterable[str] = (),
    out_dir: Path = MERCADO_BRONZE_DIR,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict[str, object]]:
    """Plan de captura de cada aseguradora activa; resumen por aseguradora (también es la verificación)."""
    # Un solo cliente: la pausa entre peticiones también corre entre una aseguradora y la siguiente.
    cliente = ClienteCortes(session, sleep=sleep)
    resumen = []
    for a in activas(registro, solo):
        plan = descubrir_una(cliente, a, out_dir)
        seleccionadas = plan.get("seleccionadas", [])
        resumen.append(
            {
                "aseguradora": a.id,
                "estado": plan["estado"],
                "en_sitemap": plan.get("total_sitemap", 0),
                "seleccionadas": len(seleccionadas) if isinstance(seleccionadas, list) else 0,
                "recortadas_por_tope": plan.get("recortadas_por_tope", 0),
            }
        )
    return resumen


def capturar(
    session: HttpSession,
    registro: Iterable[Aseguradora],
    solo: Iterable[str] = (),
    out_dir: Path = MERCADO_BRONZE_DIR,
    sleep: Callable[[float], None] | None = None,
) -> dict[str, dict[str, int]]:
    """Descarga a Bronze el plan de cada aseguradora (reanudable, con la cortesía de la Fase 1)."""
    resultado: dict[str, dict[str, int]] = {}
    for a in activas(registro, solo):
        carpeta = out_dir / a.id
        plan_path = carpeta / MERCADO_PLAN
        if not plan_path.is_file():
            continue
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        entradas = [SitemapEntry(**e) for e in plan.get("seleccionadas", [])]
        extra = {"sleep": sleep} if sleep else {}
        registros = BronzeFetcher(session, carpeta, carpeta / MERCADO_CAPTURA, **extra).fetch_all(entradas)
        ok = sum(1 for r in registros if r.status == 200)
        resultado[a.id] = {"total": len(registros), "ok": ok, "fallidas": len(registros) - ok}
    return resultado


def _titulo_sin_marca(titulo: str, a: Aseguradora) -> str:
    """Quita « | Marca» o « - Marca» del final del título (cada sitio lo pone a su manera)."""
    unificado = titulo.replace(" – ", " | ").replace(" - ", " | ")
    partes = [p.strip() for p in unificado.split(" | ") if p.strip()]
    marcas = {a.nombre.lower(), *a.alias}
    utiles = [p for p in partes if p.lower() not in marcas]
    return " | ".join(utiles) or titulo


def procesar_una(
    a: Aseguradora, bronze_dir: Path, silver_dir: Path
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Bronze → Silver → chunks Gold de una aseguradora, con su WhatsApp oficial si lo publica."""
    carpeta = bronze_dir / a.id
    capturas = [r for r in load_captured(carpeta / MERCADO_CAPTURA).values() if r.status == 200 and r.file]
    paginas: list[tuple[str, str, str]] = []  # (url, html, markdown)
    numeros: list[list[str]] = []
    for rec in capturas:
        html = (carpeta / BRONZE_HTML_SUBDIR / str(rec.file)).read_text(encoding="utf-8", errors="replace")
        numeros.append(contactos.whatsapp_de_html(html))
        paginas.append((rec.url, html, clean.trim_noise(clean.html_to_markdown(html))))
    boilerplate = clean.find_boilerplate([md for _, _, md in paginas])
    destino = silver_dir / a.id
    destino.mkdir(parents=True, exist_ok=True)
    docs: list[gold.GoldDoc] = []
    for (url, html, md), rec in zip(paginas, capturas, strict=True):
        texto = clean.remove_lines(md, boilerplate)
        if len(texto) < MIN_PAGE_CHARS:
            continue
        titulo, descripcion = clean.extract_meta(html)
        titulo = _titulo_sin_marca(titulo or clean.title_from_path(rec.path), a)
        doc_id = f"{a.id}--{slugify_path(rec.path)}"
        (destino / f"{doc_id}.txt").write_text(texto, encoding="utf-8")
        docs.append(
            gold.GoldDoc(
                doc_id=doc_id,
                url=url,
                title=titulo,
                description=descripcion,
                section=secciones.clasificar_seccion(url, titulo),
                fetched_at=rec.fetched_at,
                sha256=rec.sha256 or "",
                text=texto,
            )
        )
    docs, duplicadas = gold.dedupe_docs(docs)
    chunks = [c | {"aseguradora": a.id} for d in docs for c in gold.chunk_doc(d)]
    resumen = {
        "paginas_bronze": len(capturas),
        "documentos": len(docs),
        "chunks": len(chunks),
        "duplicadas": len(duplicadas),
        "whatsapp": contactos.whatsapp_principal(numeros)[:MERCADO_WHATSAPP_MAX],
    }
    return chunks, resumen


def procesar(
    registro: Iterable[Aseguradora],
    bronze_dir: Path = MERCADO_BRONZE_DIR,
    silver_dir: Path = MERCADO_SILVER_DIR,
    gold_dir: Path = MERCADO_GOLD_DIR,
) -> dict[str, dict[str, object]]:
    """Regenera Silver y Gold de todas las aseguradoras capturadas (sin volver a la web)."""
    todos: list[dict[str, object]] = []
    resumen: dict[str, dict[str, object]] = {}
    for a in activas(registro):
        if not (bronze_dir / a.id / MERCADO_CAPTURA).is_file():
            continue
        chunks, resumen[a.id] = procesar_una(a, bronze_dir, silver_dir)
        todos.extend(chunks)
    gold_dir.mkdir(parents=True, exist_ok=True)
    (gold_dir / MERCADO_CHUNKS_JSONL.name).write_text(
        "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in todos), encoding="utf-8"
    )
    (gold_dir / MERCADO_RESUMEN_JSON.name).write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return resumen


def leer_resumen(gold_dir: Path = MERCADO_GOLD_DIR) -> dict[str, dict[str, object]]:
    """Resumen del último ``procesar`` (documentos, chunks y WhatsApp por aseguradora)."""
    ruta = gold_dir / MERCADO_RESUMEN_JSON.name
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.is_file() else {}


def chunks_mercado(
    mercado_path: Path = MERCADO_CHUNKS_JSONL, principal_path: Path = CHUNKS_JSONL
) -> list[dict[str, object]]:
    """Chunks de todas las aseguradoras: el corpus principal (Bolívar) más el de mercado."""
    principal = (
        [c | {"aseguradora": MERCADO_ID_PRINCIPAL} for c in fragmentos_rag(principal_path)]
        if principal_path.is_file()
        else []
    )
    mercado = []
    if mercado_path.is_file():
        lineas = mercado_path.read_text(encoding="utf-8").splitlines()
        mercado = [json.loads(linea) for linea in lineas if linea.strip()]
    return principal + mercado


def _huella(ruta: Path) -> float:
    """Fecha de modificación de un archivo (0 si no existe): cambia cuando se regenera el corpus."""
    return ruta.stat().st_mtime if ruta.is_file() else 0.0


@lru_cache(maxsize=1)
def _recuperador_para(huellas: tuple[float, float]) -> RecuperadorHibrido:
    """Buscador construido para una versión concreta de los dos corpus (``huellas``)."""
    chunks = chunks_mercado()
    if not chunks:
        raise CorpusVacioError("Falta el corpus de mercado: ejecute `make data` y `make mercado`.")
    return RecuperadorHibrido(chunks)


def recuperador_mercado() -> RecuperadorHibrido:
    """Buscador BM25 del corpus de mercado.

    Se reconstruye solo si cambió alguno de los dos corpus (``make mercado`` con el servidor
    arriba no deja resultados viejos). Sin corpus lanza ``CorpusVacioError`` (datos no listos).
    """
    return _recuperador_para((_huella(CHUNKS_JSONL), _huella(MERCADO_CHUNKS_JSONL)))


def documentos_principales(principal_path: Path = CHUNKS_JSONL) -> int:
    """Documentos del corpus principal (Seguros Bolívar), que no pasa por ``procesar``."""
    if not principal_path.is_file():
        return 0
    lineas = principal_path.read_text(encoding="utf-8").splitlines()
    return len({json.loads(linea).get("doc_id") for linea in lineas if linea.strip()})


def registro_con_datos(
    gold_dir: Path = MERCADO_GOLD_DIR, principal_path: Path = CHUNKS_JSONL
) -> list[dict[str, object]]:
    """Registro para la API: cada aseguradora con su estado, documentos y WhatsApp oficial.

    Las de ``corpus_propio`` (Seguros Bolívar) cuentan los documentos del corpus principal.
    """
    resumen = leer_resumen(gold_dir)
    filas = []
    for a in cargar_registro():
        datos = dict(resumen.get(a.id, {}))
        if a.corpus_propio:
            datos["documentos"] = documentos_principales(principal_path)
        filas.append(
            {
                "id": a.id,
                "nombre": a.nombre,
                "sitio": a.sitio or None,
                "activo": a.activo,
                "verificado": a.verificado,
                "documentos": datos.get("documentos", 0),
                "whatsapp": datos.get("whatsapp", []),
                "nota": a.nota or None,
            }
        )
    return filas


def aseguradoras(ids: Iterable[str] = ()) -> list[Aseguradora]:
    """Aseguradoras del registro por id (todas las que tienen datos si no se piden ids)."""
    registro = cargar_registro()
    indice = por_id(registro)
    pedidos = list(dict.fromkeys(ids))  # sin repetidos
    faltan = [i for i in pedidos if i not in indice]
    if faltan:
        raise KeyError(f"Aseguradora no registrada: {', '.join(faltan)}")
    if pedidos:
        return [indice[i] for i in pedidos]
    return [a for a in registro if a.corpus_propio or a.hace_scraping]


def detectar_aseguradoras(mensaje: str) -> list[str]:
    """Ids de las aseguradoras del registro que nombra un mensaje (para el clasificador)."""
    return detectar(mensaje, cargar_registro())


def comparar_aseguradoras(
    buscador: RecuperadorHibrido,
    consulta: str,
    ids: Iterable[str] = (),
    por_aseguradora: int = MERCADO_POR_ASEGURADORA,
    seccion: str | None = None,
) -> list[Oferta]:
    """La misma consulta en varias aseguradoras.

    Con ``ids``, compara esas. Sin ``ids``, elige las que aparecen en una búsqueda general, en ese
    orden; si ninguna publica algo sobre la consulta, devuelve una lista vacía (no inventa un orden).
    """
    pedidos = list(dict.fromkeys(ids))  # un id repetido no duplica la oferta
    if pedidos:
        elegidas = aseguradoras(pedidos)
    else:
        candidatas = {a.id: a for a in aseguradoras()}
        encontradas = buscador.buscar(consulta, k=MERCADO_CANDIDATOS_RELEVANCIA, seccion=seccion)
        relevantes = dict.fromkeys(f.aseguradora for f in encontradas if f.aseguradora in candidatas)
        elegidas = [candidatas[i] for i in relevantes][:MERCADO_MAX_COMPARAR]
        if not elegidas:
            return []
    return comparar(buscador, consulta, elegidas, por_aseguradora, seccion)


# Secciones que existen en los dos corpus (reglas del principal y genéricas del mercado).
SECCIONES_VALIDAS: frozenset[str] = frozenset(
    {sec for _, sec in SECTION_RULES}
    | {sec for _, sec in secciones.REGLAS_SECCION}
    | {secciones.SECCION_POR_DEFECTO, "institucional"}
)


def validar_seccion(seccion: str) -> str:
    """Devuelve la sección si existe; si no, ``ValueError`` con las válidas (para la API y la CLI)."""
    if seccion not in SECCIONES_VALIDAS:
        raise ValueError(f"Sección desconocida: «{seccion}». Válidas: {', '.join(sorted(SECCIONES_VALIDAS))}")
    return seccion
