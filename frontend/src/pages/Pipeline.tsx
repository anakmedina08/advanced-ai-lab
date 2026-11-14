import { useState } from "react";

import { ApiError, corpus, descubrir, etapasPipeline, reprocesar } from "../api/client";
import Icono from "../components/Icono";
import { EstadoCarga, Metrica, useDatos } from "../components/Panel";

/** Pipeline de datos (panel del equipo): etapas Medallion con sus métricas y el corpus Gold. */
export default function Pipeline() {
  const etapas = useDatos(etapasPipeline);
  const documentos = useDatos(corpus);
  const [accion, setAccion] = useState<{ fase: "idle" | "trabajando" | "listo" | "error"; mensaje: string }>({
    fase: "idle",
    mensaje: "",
  });

  const ejecutar = async (tipo: "procesar" | "descubrir") => {
    setAccion({
      fase: "trabajando",
      mensaje: tipo === "procesar" ? "Limpiando, deduplicando y fragmentando…" : "Consultando robots.txt y sitemap.xml…",
    });
    try {
      if (tipo === "procesar") {
        const r = await reprocesar();
        setAccion({
          fase: "listo",
          mensaje: `Pipeline terminado: ${r.documentos} documentos y ${r.chunks} fragmentos · ${r.duplicadas_descartadas} páginas duplicadas descartadas.`,
        });
        void etapas.recargar();
        void documentos.recargar();
      } else {
        const r = await descubrir();
        setAccion({
          fase: "listo",
          mensaje: `Sitemap: ${r.total_sitemap} URLs · seleccionadas ${r.seleccionadas} · descartadas ${r.descartadas}.`,
        });
      }
    } catch (e) {
      const detalle = e instanceof ApiError ? e.detalle : String(e);
      setAccion({ fase: "error", mensaje: `No se pudo completar: ${detalle}. Se muestran los datos ya capturados.` });
    }
  };

  return (
    <div className="pila">
      <p className="leyenda">
        Fuente: segurosbolivar.com · respeta robots.txt y sitemap.xml · User-Agent identificado · 1,5 s entre peticiones ·
        Bronze → Silver → Gold.
      </p>
      <div className="acciones">
        <button type="button" className="primario" disabled={accion.fase === "trabajando"} onClick={() => void ejecutar("procesar")}>
          <Icono nombre="sync" /> Reprocesar sin volver a la web
        </button>
        <button type="button" disabled={accion.fase === "trabajando"} onClick={() => void ejecutar("descubrir")}>
          <Icono nombre="travel_explore" /> Descubrir en vivo (robots.txt + sitemap)
        </button>
      </div>
      {accion.mensaje && (
        <p className={accion.fase === "error" ? "error" : "exito"} role="status">
          {accion.mensaje}
        </p>
      )}
      <EstadoCarga cargando={etapas.cargando} error={etapas.error} onReintentar={() => void etapas.recargar()} />
      {(etapas.datos ?? []).map((e) => {
        const principales = Object.entries(e.metricas).filter(([k]) => !k.startsWith("  ·"));
        const detalle = Object.entries(e.metricas).filter(([k]) => k.startsWith("  ·"));
        return (
          <section key={e.etapa} className="tarjeta">
            <h2>
              <Icono nombre={e.hecha ? "check_circle" : "pending"} className={e.hecha ? "verde" : ""} /> {e.etapa}{" "}
              <span className="leyenda">· {e.capa}</span>
            </h2>
            <div className="fila-metricas">
              {principales.map(([k, v]) => (
                <Metrica key={k} titulo={k} valor={typeof v === "number" ? v.toLocaleString("es-CO") : v} icono="query_stats" />
              ))}
            </div>
            {detalle.length > 0 && (
              <p className="leyenda">Motivos de descarte: {detalle.map(([k, v]) => `${k.replace(/^\s*·\s*/, "")}: ${v}`).join(" · ")}</p>
            )}
          </section>
        );
      })}
      {documentos.datos && documentos.datos.length > 0 && (
        <section className="tarjeta">
          <h2>
            <Icono nombre="table_chart" /> Corpus Gold · {documentos.datos.length} documentos
          </h2>
          <div className="tabla-scroll">
            <table className="tabla">
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Sección</th>
                  <th>Captura</th>
                  <th>sha256</th>
                  <th>Tokens</th>
                </tr>
              </thead>
              <tbody>
                {documentos.datos.map((d) => (
                  <tr key={d.url}>
                    <td>
                      <a href={d.url} target="_blank" rel="noreferrer">
                        {d.titulo}
                      </a>
                    </td>
                    <td>{d.seccion}</td>
                    <td>{d.fecha_captura.slice(0, 10)}</td>
                    <td>
                      <code>{d.sha256}</code>
                    </td>
                    <td>{d.tokens.toLocaleString("es-CO")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
