import { useState } from "react";
import Markdown from "react-markdown";

import { ApiError, guia, temas } from "../api/client";
import type { RespuestaOut } from "../api/types";
import Icono from "../components/Icono";
import { EstadoCarga, useDatos } from "../components/Panel";

type Tipo = "resumen" | "faq";

/** Guías de seguros: resumen o preguntas frecuentes de un tema, con la página de donde sale cada dato. */
export default function Guias({ proveedor }: { proveedor?: string }) {
  const lista = useDatos(temas);
  const [tipo, setTipo] = useState<Tipo>("resumen");
  const [tema, setTema] = useState<string>("");
  const [n, setN] = useState(5);
  const [fase, setFase] = useState<"idle" | "cargando" | "listo" | "error">("idle");
  const [resultado, setResultado] = useState<RespuestaOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const elegido = tema || lista.datos?.[0] || "";

  const generar = async () => {
    setFase("cargando");
    setError(null);
    try {
      setResultado(await guia(tipo, elegido, n, proveedor));
      setFase("listo");
    } catch (e) {
      setError(e instanceof ApiError ? e.detalle : String(e));
      setFase("error");
    }
  };

  return (
    <div className="pila">
      <p className="leyenda">Guías generadas a partir de la información pública, con la página de donde sale cada dato.</p>
      <EstadoCarga cargando={lista.cargando} error={lista.error} onReintentar={() => void lista.recargar()} />
      <section className="tarjeta">
        <div className="segmentado" role="radiogroup" aria-label="Tipo de guía">
          {(["resumen", "faq"] as Tipo[]).map((t) => (
            <button key={t} type="button" role="radio" aria-checked={tipo === t} className={tipo === t ? "activo" : undefined} onClick={() => setTipo(t)}>
              {t === "resumen" ? "Resumen" : "Preguntas frecuentes"}
            </button>
          ))}
        </div>
        <div className="fila-controles">
          <label>
            Tema
            <select value={elegido} onChange={(e) => setTema(e.target.value)}>
              {(lista.datos ?? []).map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </label>
          {tipo === "faq" && (
            <label>
              Número de preguntas: {n}
              <input type="range" min={3} max={10} value={n} onChange={(e) => setN(Number(e.target.value))} />
            </label>
          )}
          <button type="button" className="primario" disabled={!elegido || fase === "cargando"} onClick={() => void generar()}>
            <Icono nombre="auto_awesome" /> {fase === "cargando" ? "Preparando la guía…" : "Generar guía"}
          </button>
        </div>
      </section>
      {fase === "error" && error && (
        <div className="error" role="alert">
          <p>No se pudo generar la guía: {error}</p>
        </div>
      )}
      {resultado && fase === "listo" && (
        <section className="tarjeta">
          <h2>
            <Icono nombre="description" /> {tipo === "resumen" ? "Resumen" : "Preguntas frecuentes"}: {elegido}
          </h2>
          <Markdown>{resultado.texto}</Markdown>
          {resultado.fuentes.length > 0 && (
            <ul className="fuentes">
              {resultado.fuentes.map((u) => (
                <li key={u}>
                  <a href={u} target="_blank" rel="noreferrer">
                    {u.replace(/^https?:\/\/(www\.)?/, "")}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
