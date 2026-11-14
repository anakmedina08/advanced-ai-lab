import type { AgenteOut, DecisionOut, Ruta } from "../api/types";

const NOMBRES: Record<Ruta, string> = {
  directo: "directo · sin búsqueda",
  datos: "datos · CSV",
  rag: "RAG · documentos",
  mixto: "mixto · documentos + datos",
  fuera_de_alcance: "fuera de alcance · sin LLM",
};

interface Props {
  decision: DecisionOut;
  turno?: AgenteOut;
  toolsEnCurso?: string[];
}

/** Insignia con la ruta del router y detalle plegable: señales, tools con su latencia y fuentes. */
export default function PanelDecision({ decision, turno, toolsEnCurso }: Props) {
  const tiempos = turno?.tiempos_tools ?? [];
  const usadas = tiempos.length ? tiempos : (toolsEnCurso ?? []).map((tool) => ({ tool, ms: undefined }));
  return (
    <div className="decision">
      <span className={`insignia ruta-${decision.ruta}`} title="Decisión del router">
        {NOMBRES[decision.ruta]}
        {decision.cautela && " · cautela"}
      </span>
      <span className="suave mini"> confianza {Math.round(decision.confianza * 100)} %</span>
      {turno && <span className="suave mini"> · {(turno.ms_total / 1000).toFixed(1)} s</span>}
      <details>
        <summary>¿Cómo se resolvió?</summary>
        <dl className="detalle">
          <dt>Señales del router</dt>
          <dd>{decision.senales.join(" · ") || "—"}</dd>
          <dt>Tools habilitadas</dt>
          <dd>{decision.tools.join(", ") || "ninguna (respuesta directa)"}</dd>
          <dt>Tools usadas</dt>
          <dd>
            {usadas.length === 0
              ? "ninguna"
              : usadas.map((t, i) => (
                  <code key={`${t.tool}-${i}`}>
                    {t.tool}
                    {t.ms !== undefined && ` ${Math.round(t.ms)} ms`}
                  </code>
                ))}
          </dd>
          {turno && turno.fuentes_descartadas.length > 0 && (
            <>
              <dt>Fuentes descartadas (no vistas en la búsqueda)</dt>
              <dd>{turno.fuentes_descartadas.join(", ")}</dd>
            </>
          )}
          {turno && (
            <>
              <dt>Memoria del hilo</dt>
              <dd>{turno.mensajes_en_memoria} mensajes guardados</dd>
            </>
          )}
        </dl>
      </details>
    </div>
  );
}
