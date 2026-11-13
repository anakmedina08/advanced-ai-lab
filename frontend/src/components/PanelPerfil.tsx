import { useCallback, useEffect, useState } from "react";

import { ApiError, borrarPerfil, perfil } from "../api/client";

interface Props {
  usuarioId: string;
  /** Cambia cuando termina un turno, para volver a consultar el perfil. */
  version: number;
}

/** «Lo que recuerdo de ti»: la memoria de largo plazo (Store) del usuario, con opción de borrarla. */
export default function PanelPerfil({ usuarioId, version }: Props) {
  const [hechos, setHechos] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    try {
      setHechos((await perfil(usuarioId)).hechos);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.detalle : String(e));
    }
  }, [usuarioId]);

  useEffect(() => {
    void cargar();
  }, [cargar, version]);

  const olvidar = async () => {
    try {
      await borrarPerfil(usuarioId);
      setHechos({});
    } catch (e) {
      setError(e instanceof ApiError ? e.detalle : String(e));
    }
  };

  const entradas = Object.entries(hechos);
  return (
    <section className="perfil" aria-label="Memoria de largo plazo">
      <h2>Lo que recuerdo de ti</h2>
      {error && <p className="suave">{error}</p>}
      {!error && entradas.length === 0 && <p className="suave">Nada todavía. Cuénteme, por ejemplo, su nombre o si tiene carro.</p>}
      {entradas.length > 0 && (
        <>
          <dl>
            {entradas.map(([clave, valor]) => (
              <div key={clave}>
                <dt>{clave.replace(/_/g, " ")}</dt>
                <dd>{valor}</dd>
              </div>
            ))}
          </dl>
          <button type="button" onClick={() => void olvidar()}>
            Olvidar mis datos
          </button>
        </>
      )}
      <p className="suave mini">Se guarda en el Store del agente (namespace por usuario) y vale para todos sus hilos.</p>
    </section>
  );
}
