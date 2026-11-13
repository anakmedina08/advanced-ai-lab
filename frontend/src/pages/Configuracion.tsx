import { sistema } from "../api/client";
import { AYUDA_MODOS, type Ajustes, MODOS, VERSIONES } from "../chat/ajustes";
import { PROVEEDORES } from "../chat/proveedor";
import type { EstadoSalud } from "../chat/salud";
import Icono from "../components/Icono";
import { Metrica, useDatos } from "../components/Panel";
import Estado from "./Estado";

interface Props {
  ajustes: Ajustes;
  onCambiar: (cambio: Partial<Ajustes>) => void;
  salud: EstadoSalud;
  onReintentar: () => void;
}

const AYUDA: Record<string, string> = {
  anthropic: "Claude: el modelo evaluado (v3 cita la fuente en el 100 % de las respuestas) y el único con visión para la foto.",
  ollama: "Modelo local en CPU: gratis y privado, pero más lento y menos preciso con las tools; no entiende fotos.",
  deepseek: "Alternativa en la nube, económica; no entiende fotos.",
};

function Insignia({ ok, si, no, icono }: { ok: boolean; si: string; no: string; icono: string }) {
  return (
    <span className={`insignia ${ok ? "estado-ok" : "estado-curso"}`}>
      <Icono nombre={icono} /> {ok ? si : no}
    </span>
  );
}

/** Configuración (panel del equipo): proveedor, modo de contexto, versión del prompt y estado del sistema. */
export default function Configuracion({ ajustes, onCambiar, salud, onReintentar }: Props) {
  const datos = useDatos(sistema).datos;
  const modo = MODOS.find((m) => m.id === ajustes.modo) ?? MODOS[0];
  return (
    <div className="pila">
      <p className="leyenda">Ajustes técnicos de esta sesión. El área de atención al cliente los usa sin mostrarlos.</p>
      <section className="tarjeta">
        <h2>
          <Icono nombre="psychology" /> Modelo y contexto
        </h2>
        <p className="etiqueta-campo">Proveedor del modelo</p>
        <div className="segmentado" role="radiogroup" aria-label="Proveedor del modelo">
          {PROVEEDORES.map((p) => (
            <button
              key={p.id}
              type="button"
              role="radio"
              aria-checked={ajustes.proveedor === p.id}
              className={ajustes.proveedor === p.id ? "activo" : undefined}
              onClick={() => onCambiar({ proveedor: p.id })}
            >
              {p.nombre}
            </button>
          ))}
        </div>
        <p className="leyenda">{AYUDA[ajustes.proveedor] ?? ""}</p>
        <label>
          <span className="etiqueta-campo" title={AYUDA_MODOS}>
            Modo de contexto <Icono nombre="help" />
          </span>
          <select value={modo.id} onChange={(e) => onCambiar({ modo: e.target.value })} aria-label="Modo de contexto">
            {MODOS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.nombre}
              </option>
            ))}
          </select>
        </label>
        <p className="etiqueta-campo">Versión del prompt</p>
        <div className="segmentado" role="radiogroup" aria-label="Versión del prompt">
          {VERSIONES.map((v) => (
            <button
              key={v}
              type="button"
              role="radio"
              aria-checked={ajustes.version === v}
              disabled={modo.agente}
              className={ajustes.version === v ? "activo" : undefined}
              onClick={() => onCambiar({ version: v })}
            >
              {v}
            </button>
          ))}
        </div>
        <p className="leyenda">
          {modo.agente
            ? "Los agentes usan su propio prompt (con reglas de citación, memoria y blindaje)."
            : "v1: ingenuo · v2: grounding simple · v3: zero-shot estructurado · v4: few-shot"}
        </p>
        {ajustes.proveedor === "ollama" && ajustes.modo === "completo" && (
          <p className="aviso-foto">Con Ollama en CPU, «Toda la base» puede tardar minutos; use «Reducido» o «RAG».</p>
        )}
      </section>
      <section className="tarjeta">
        <h2>
          <Icono nombre="monitor_heart" /> Estado del sistema
        </h2>
        {datos && (
          <>
            <div className="insignias">
              <Insignia ok={datos.base_lista} si="Base de conocimiento lista" no="Falta la base: make data" icono="database" />
              <Insignia ok={datos.vision_instalada} si="Visión (YOLO) instalada" no="Visión sin instalar: make vision" icono="photo_camera" />
              <Insignia ok={datos.clave_anthropic} si="Clave de Anthropic configurada" no="Sin clave de Anthropic en .env" icono="key" />
            </div>
            {datos.paginas !== null && (
              <div className="fila-metricas">
                <Metrica titulo="Páginas en la base" valor={(datos.paginas ?? 0).toLocaleString("es-CO")} icono="article" />
                <Metrica titulo="Fragmentos" valor={(datos.fragmentos ?? 0).toLocaleString("es-CO")} icono="segment" />
                <Metrica titulo="Tokens de contexto (aprox.)" valor={(datos.tokens_contexto ?? 0).toLocaleString("es-CO")} icono="token" />
              </div>
            )}
          </>
        )}
        <h3>Componentes del backend</h3>
        <Estado estado={salud} onReintentar={onReintentar} />
      </section>
    </div>
  );
}
