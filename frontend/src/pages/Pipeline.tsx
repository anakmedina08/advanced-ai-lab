import { corpus, etapasPipeline } from "../api/client";
import Icono from "../components/Icono";
import { EstadoCarga, Metrica, useDatos } from "../components/Panel";

/** Pipeline de datos (panel del equipo): etapas Medallion con sus métricas y el corpus Gold. */
export default function Pipeline() {
  const etapas = useDatos(etapasPipeline);
  const documentos = useDatos(corpus);

  return (
    <div className="pila">
      <p className="leyenda">
        Fuente: segurosbolivar.com · respeta robots.txt y sitemap.xml · User-Agent identificado · 1,5 s entre peticiones ·
        Bronze → Silver → Gold. Reprocesar: <code>make process</code>.
      </p>
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
