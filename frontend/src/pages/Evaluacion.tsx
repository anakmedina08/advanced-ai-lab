import { useEffect, useState } from "react";

import { detalleEvaluacion, evaluaciones } from "../api/client";
import Icono from "../components/Icono";
import { Barra, EstadoCarga, Metrica, pct, useDatos } from "../components/Panel";

const METRICAS = [
  ["tasa_cita_fuente", "Cita la fuente"],
  ["tasa_fallback_correcto", "Rechazo correcto"],
  ["keyword_hit_promedio", "Palabras clave"],
] as const;

/** Evaluación (panel del equipo): compara las corridas de `sb eval` por versión del prompt y modo. */
export default function Evaluacion() {
  const { datos, error, cargando, recargar } = useDatos(evaluaciones);
  const [corrida, setCorrida] = useState<string>("");
  const [detalle, setDetalle] = useState<Record<string, string | number | boolean>[]>([]);
  const lista = datos ?? [];
  const elegida = corrida || (lista[0] ? `${lista[0].modelo}|${lista[0].version}` : "");

  useEffect(() => {
    if (!elegida) return;
    const [modelo, version] = elegida.split("|");
    detalleEvaluacion(modelo, version).then(setDetalle).catch(() => setDetalle([]));
  }, [elegida]);

  if (cargando || error) return <EstadoCarga cargando={cargando} error={error} onReintentar={() => void recargar()} />;
  if (lista.length === 0) return <p className="leyenda">Aún no hay resultados. Ejecute, por ejemplo: <code>uv run sb eval --version v3</code></p>;

  const mejor = lista.reduce((a, b) => (b.tasa_cita_fuente > a.tasa_cita_fuente ? b : a));
  return (
    <div className="pila">
      <div className="fila-metricas">
        <Metrica titulo="Corridas" valor={lista.length} icono="playlist_add_check" />
        <Metrica titulo="Mejor cita de fuente" valor={pct(mejor.tasa_cita_fuente)} icono="link" />
        <Metrica titulo="Corrida con mejor cita" valor={`${mejor.modelo} · ${mejor.version}`} icono="emoji_events" />
      </div>
      <section className="tarjeta">
        <h2>
          <Icono nombre="bar_chart" /> Comparación de corridas
        </h2>
        <p className="leyenda">Proporción de 0 a 1 sobre el banco de preguntas (evaluacion/preguntas.yaml); más alto es mejor.</p>
        <div className="corridas">
          {lista.map((c) => (
            <div key={`${c.modelo}-${c.version}`} className="corrida">
              <p className="corrida-nombre">
                {c.modelo} · {c.version} <span className="leyenda">· {c.latencia_promedio_s.toFixed(1)} s</span>
              </p>
              {METRICAS.map(([clave, etiqueta]) => (
                <Barra key={clave} etiqueta={etiqueta} valor={c[clave]} formato={pct} />
              ))}
            </div>
          ))}
        </div>
      </section>
      <section className="tarjeta">
        <h2>
          <Icono nombre="list_alt" /> Detalle por pregunta
        </h2>
        <label>
          Corrida{" "}
          <select value={elegida} onChange={(e) => setCorrida(e.target.value)}>
            {lista.map((c) => (
              <option key={`${c.modelo}|${c.version}`} value={`${c.modelo}|${c.version}`}>
                {c.modelo} · {c.version}
              </option>
            ))}
          </select>
        </label>
        <div className="tabla-scroll">
          <table className="tabla">
            <thead>
              <tr>
                <th>Id</th>
                <th>Pregunta</th>
                <th>Palabras clave</th>
                <th>Cita fuente</th>
                <th>Rechazo correcto</th>
                <th>Latencia</th>
              </tr>
            </thead>
            <tbody>
              {detalle.map((f) => (
                <tr key={String(f.id)}>
                  <td>{String(f.id)}</td>
                  <td>{String(f.pregunta)}</td>
                  <td>{pct(Number(f.keyword_hit))}</td>
                  <td>{String(f.cita_fuente) === "true" || f.cita_fuente === true ? "✓" : "—"}</td>
                  <td>{String(f.fallback_ok) === "true" || f.fallback_ok === true ? "✓" : "—"}</td>
                  <td>{Number(f.latencia_s).toFixed(1)} s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
