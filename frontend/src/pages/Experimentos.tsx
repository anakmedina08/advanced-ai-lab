import { experimentos } from "../api/client";
import type { CorridaOut } from "../api/types";
import Icono from "../components/Icono";
import { EstadoCarga, Metrica, useDatos } from "../components/Panel";

/** Métricas que se muestran por experimento (nombre en MLflow → etiqueta). */
const COLUMNAS: Record<string, [string, string][]> = {
  "asistente-qa": [["tasa_cita_fuente", "Cita fuente"], ["tasa_fallback_correcto", "Rechazo correcto"], ["keyword_hit_promedio", "Palabras clave"]],
  recuperacion: [["hit_at_6", "hit@6"], ["hit_at_10", "hit@10"], ["recall_at_10", "recall@10"], ["ndcg_at_10", "nDCG@10"]],
  recomendador: [["recall_at_5", "Recall@5"], ["ndcg_at_5", "NDCG@5"]],
  "vision-yolo": [["precision", "Precisión"], ["recall", "Recall"], ["f1", "F1"], ["ap50_person", "AP50 person"], ["latencia_p95_ms", "p95 (ms)"]],
};

const formatear = (v: number | undefined) => (v === undefined ? "—" : Math.abs(v) >= 10 ? v.toFixed(0) : v.toFixed(3));

function Tabla({ corridas, columnas }: { corridas: CorridaOut[]; columnas: [string, string][] }) {
  return (
    <div className="tabla-scroll">
      <table className="tabla">
        <thead>
          <tr>
            <th>Corrida</th>
            {columnas.map(([, e]) => (
              <th key={e}>{e}</th>
            ))}
            <th>Commit</th>
          </tr>
        </thead>
        <tbody>
          {corridas.map((c, i) => (
            <tr key={`${c.nombre}-${i}`}>
              <td>{c.nombre}</td>
              {columnas.map(([k]) => (
                <td key={k}>{formatear(c.metricas[k])}</td>
              ))}
              <td>
                <code>{c.commit || "—"}</code>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Experimentos (MLflow): corridas de cada experimento comparadas en tablas. */
export default function Experimentos() {
  const { datos, error, cargando, recargar } = useDatos(experimentos);
  if (cargando || error) return <EstadoCarga cargando={cargando} error={error} onReintentar={() => void recargar()} />;
  if (!datos?.activa) {
    return (
      <p className="leyenda">
        La bitácora de MLflow no está activa. Instálela con <code>uv sync --extra mlflow</code> y levante el servidor con{" "}
        <code>make mlflow-server</code>.
      </p>
    );
  }
  const todas = Object.values(datos.experimentos).flat();
  const ultima = Math.max(0, ...todas.map((c) => c.fecha));
  return (
    <div className="pila">
      <p className="leyenda">Cada corrida guarda lo que se probó (parámetros), cómo salió (métricas) y el commit del código.</p>
      <div className="fila-metricas">
        <Metrica titulo="Corridas registradas" valor={todas.length} icono="science" />
        <Metrica titulo="Experimentos" valor={Object.values(datos.experimentos).filter((c) => c.length).length} icono="folder" />
        <Metrica titulo="Última corrida" valor={ultima ? new Date(ultima).toLocaleString("es-CO", { dateStyle: "short", timeStyle: "short" }) : "—"} icono="schedule" />
      </div>
      <p>
        <a className="boton-enlace" href={datos.url_ui} target="_blank" rel="noreferrer">
          <Icono nombre="open_in_new" /> Abrir MLflow ({datos.url_ui})
        </a>
      </p>
      {Object.entries(datos.experimentos).map(([nombre, corridas]) => (
        <section key={nombre} className="tarjeta">
          <h2>
            <Icono nombre="science" /> {datos.nombres[nombre] ?? nombre}{" "}
            <span className="leyenda">· {nombre} · {corridas.length} corridas</span>
          </h2>
          {corridas.length ? <Tabla corridas={corridas} columnas={COLUMNAS[nombre] ?? []} /> : <p className="leyenda">Sin corridas.</p>}
        </section>
      ))}
    </div>
  );
}
