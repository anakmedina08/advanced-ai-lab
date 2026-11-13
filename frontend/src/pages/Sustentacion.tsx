import { useState } from "react";

import { proyecto } from "../api/client";
import Icono from "../components/Icono";
import { EstadoCarga, Metrica, useDatos } from "../components/Panel";

const ESTADOS = [
  { id: "cumplido", icono: "check_circle", clase: "estado-ok" },
  { id: "en curso", icono: "pending", clase: "estado-curso" },
  { id: "pendiente", icono: "schedule", clase: "estado-pendiente" },
] as const;

const PESTANAS: Record<string, [string, string]> = {
  "Gestión de Proyectos en IA y CD": ["Gestión de Proyectos", "account_tree"],
  "Técnicas Avanzadas de IA en Modelos de Lenguaje": ["Técnicas Avanzadas", "psychology"],
  "Comunes a los dos cursos (gobernanza y herramientas)": ["Comunes", "handshake"],
};

const PRUEBAS_MINIMAS = 120;

/** Muestra como código lo que va entre comillas invertidas en `docs/requisitos.md`. */
function ConCodigo({ texto }: { texto: string }) {
  return (
    <>
      {texto.split("`").map((parte, i) => (i % 2 ? <code key={i}>{parte}</code> : <span key={i}>{parte}</span>))}
    </>
  );
}

/** Entregables por curso: requisitos de `docs/requisitos.md` con estado, evidencia y cifras en vivo. */
export default function Sustentacion() {
  const { datos, error, cargando, recargar } = useDatos(proyecto);
  const [pestana, setPestana] = useState(0);
  const [filtro, setFiltro] = useState<Set<string>>(new Set(ESTADOS.map((e) => e.id)));

  if (cargando || error || !datos) return <EstadoCarga cargando={cargando} error={error} onReintentar={() => void recargar()} />;
  const secciones = Object.entries(datos.secciones);
  const [nombre, requisitos] = secciones[Math.min(pestana, secciones.length - 1)];
  const cumplidos = requisitos.filter((r) => r.estado === "cumplido").length;
  const visibles = requisitos.filter((r) => filtro.has(r.estado));
  const c = datos.contadores;

  const alternar = (id: string) =>
    setFiltro((actual) => {
      const nuevo = new Set(actual);
      if (nuevo.has(id)) nuevo.delete(id);
      else nuevo.add(id);
      return nuevo;
    });

  return (
    <div className="pila">
      <p className="leyenda">
        Lo que contiene el proyecto, organizado por curso. Cada requisito muestra su estado y dónde está la evidencia en el
        repositorio; las cifras se calculan en vivo.
      </p>
      <div className="fila-metricas">
        <Metrica titulo="Pruebas automatizadas" valor={c.funciones_de_prueba} icono="verified" nota={`mínimo ${PRUEBAS_MINIMAS}`} />
        <Metrica titulo="Specs (SDD)" valor={c.specs} icono="description" />
        <Metrica titulo="Decisiones (ADR)" valor={c.adr} icono="gavel" />
        <Metrica titulo="Tareas hechas" valor={`${c.tareas_hechas} / ${c.tareas_hechas + c.tareas_pendientes}`} icono="task_alt" />
        <Metrica titulo="Corridas en MLflow" valor={datos.corridas_mlflow ?? "—"} icono="science" />
      </div>
      <div className="enlaces">
        {Object.entries(datos.enlaces).map(([texto, url]) => (
          <a key={url} className="boton-enlace" href={url} target="_blank" rel="noreferrer">
            <Icono nombre="open_in_new" /> {texto}
          </a>
        ))}
      </div>
      <div className="pestanas" role="tablist" aria-label="Cursos">
        {secciones.map(([s], i) => {
          const [etiqueta, icono] = PESTANAS[s] ?? [s, "folder"];
          return (
            <button key={s} type="button" role="tab" aria-selected={i === pestana} className={i === pestana ? "activo" : undefined} onClick={() => setPestana(i)}>
              <Icono nombre={icono} /> {etiqueta}
            </button>
          );
        })}
      </div>
      <section className="tarjeta" role="tabpanel" aria-label={nombre}>
        <div className="fila-progreso">
          <div className="progreso" aria-label={`${cumplidos} de ${requisitos.length} cumplidos`}>
            <span style={{ width: `${(cumplidos / requisitos.length) * 100}%` }} />
          </div>
          <span className="leyenda">
            {cumplidos} de {requisitos.length} cumplidos
          </span>
          <div className="pildoras" role="group" aria-label="Filtrar por estado">
            {ESTADOS.map((e) => (
              <button key={e.id} type="button" aria-pressed={filtro.has(e.id)} className={filtro.has(e.id) ? "activo" : undefined} onClick={() => alternar(e.id)}>
                {e.id}
              </button>
            ))}
          </div>
        </div>
        <div className="requisitos">
          {visibles.map((r) => {
            const estilo = ESTADOS.find((e) => e.id === r.estado) ?? ESTADOS[2];
            return (
              <article key={r.requisito} className="requisito">
                <span className={`insignia ${estilo.clase}`}>
                  <Icono nombre={estilo.icono} /> {r.estado.charAt(0).toUpperCase() + r.estado.slice(1)}
                </span>
                <p className="requisito-nombre">
                  <ConCodigo texto={r.requisito} />
                </p>
                <p className="leyenda">
                  <ConCodigo texto={r.evidencia} />
                </p>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
