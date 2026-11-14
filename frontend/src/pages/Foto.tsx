import { useRef, useState } from "react";
import Markdown from "react-markdown";

import { ApiError, analizarFoto } from "../api/client";
import type { FotoOut } from "../api/types";
import CajasDeteccion from "../components/CajasDeteccion";
import { porcentaje, validarFoto } from "../foto/validar";

type Fase = "idle" | "cargando" | "listo" | "error";

const PLANES: Record<FotoOut["plan"]["tipo"], string> = {
  siniestro: "Siniestro: qué hacer ahora",
  asegurar: "Un bien que puede asegurar",
  documento: "Documento: no se procesa",
  ninguno: "Sin una situación de seguros clara",
};

/** Foto → «¿qué hago?»: YOLO detecta y difumina personas en el backend; Claude entiende la escena. */
export default function Foto({ proveedor }: { proveedor?: string }) {
  const [fase, setFase] = useState<Fase>("idle");
  const [error, setError] = useState<{ detalle: string; requestId: string | null } | null>(null);
  const [resultado, setResultado] = useState<FotoOut | null>(null);
  const [nombre, setNombre] = useState<string | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const control = useRef<AbortController | null>(null);

  const procesar = async (archivo: File) => {
    const invalida = validarFoto(archivo);
    setResultado(null);
    setNombre(archivo.name);
    if (invalida) {
      setFase("error");
      setError({ detalle: invalida, requestId: null });
      return;
    }
    setFase("cargando");
    setError(null);
    control.current = new AbortController();
    try {
      setResultado(await analizarFoto(archivo, control.current.signal, proveedor));
      setFase("listo");
    } catch (e) {
      const err = e instanceof ApiError ? e : new ApiError(0, "desconocido", String(e));
      setError({ detalle: err.detalle, requestId: err.requestId });
      setFase("error");
    }
  };

  return (
    <section className="foto">
      <p className="suave">
        Suba la foto de un choque, un daño en casa o un bien que quiera asegurar. Las personas se difuminan en el
        servidor antes de cualquier análisis y la foto no se guarda. No envíe fotos de documentos.
      </p>
      <label
        className={`zona-carga ${arrastrando ? "arrastrando" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastrando(false);
          const archivo = e.dataTransfer.files[0];
          if (archivo) void procesar(archivo);
        }}
      >
        <input
          type="file"
          accept="image/jpeg,image/png"
          onChange={(e) => {
            const archivo = e.target.files?.[0];
            if (archivo) void procesar(archivo);
            e.target.value = "";
          }}
          disabled={fase === "cargando"}
        />
        <span>{fase === "cargando" ? "Analizando…" : "Arrastre una foto aquí o haga clic para elegirla (JPG o PNG, máx. 8 MB)"}</span>
      </label>

      <p className="estado-foto" role="status" aria-live="polite">
        {fase === "idle" && "Esperando una foto."}
        {fase === "cargando" && `Analizando «${nombre}»: detección local con YOLO, difuminado y lectura de la escena…`}
        {fase === "listo" && resultado && `Listo: ${resultado.detecciones.length} objetos en ${Math.round(resultado.tiempo_inferencia_ms)} ms de inferencia.`}
      </p>
      {fase === "cargando" && (
        <button type="button" onClick={() => control.current?.abort()}>
          Cancelar
        </button>
      )}

      {fase === "error" && error && (
        <div className="error" role="alert">
          <p>{error.detalle}</p>
          {error.requestId && <small>request id: {error.requestId}</small>}
        </div>
      )}

      {resultado && (
        <div className="resultado-foto">
          <div>
            {resultado.imagen_jpeg_b64 && (
              <CajasDeteccion
                src={`data:image/jpeg;base64,${resultado.imagen_jpeg_b64}`}
                ancho={resultado.ancho}
                alto={resultado.alto}
                detecciones={resultado.detecciones}
              />
            )}
            <p className="suave mini">
              Inferencia YOLO: {Math.round(resultado.tiempo_inferencia_ms)} ms · personas difuminadas:{" "}
              {resultado.personas_difuminadas}
            </p>
          </div>
          <div className="tarjeta">
            <h2>{PLANES[resultado.plan.tipo]}</h2>
            <p>{resultado.plan.nombre}</p>
            {resultado.escena && (
              <p className="suave">
                Escena: {resultado.escena.descripcion} (confianza {resultado.escena.confianza})
              </p>
            )}
            {resultado.aviso && <p className="aviso-foto">{resultado.aviso}</p>}
            <h3>Detecciones</h3>
            {resultado.detecciones.length === 0 ? (
              <p className="suave">Ningún objeto relevante sobre el umbral de confianza.</p>
            ) : (
              <table className="tabla">
                <thead>
                  <tr>
                    <th>Objeto</th>
                    <th>Confianza</th>
                  </tr>
                </thead>
                <tbody>
                  {resultado.detecciones.map((d, i) => (
                    <tr key={`${d.clase}-${i}`}>
                      <td>{d.etiqueta}</td>
                      <td>
                        <meter min={0} max={1} value={d.confianza} /> {porcentaje(d.confianza)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {resultado.respuesta && (
              <>
                <h3>¿Qué hago?</h3>
                <Markdown>{resultado.respuesta.texto}</Markdown>
                <ul className="fuentes">
                  {resultado.respuesta.fuentes.map((u) => (
                    <li key={u}>
                      <a href={u} target="_blank" rel="noreferrer">
                        {u.replace(/^https?:\/\/(www\.)?/, "")}
                      </a>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {resultado.recomendaciones.length > 0 && (
              <>
                <h3>Perfiles similares también contratan</h3>
                <ul>
                  {resultado.recomendaciones.map((r) => (
                    <li key={r.product_id}>
                      <strong>{r.nombre}</strong> — {r.razon}
                    </li>
                  ))}
                </ul>
                <p className="suave mini">Sugerencia con datos sintéticos de práctica.</p>
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
