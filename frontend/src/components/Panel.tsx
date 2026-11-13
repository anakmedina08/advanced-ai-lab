import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../api/client";
import Icono from "./Icono";

/** Carga datos de la API con estados cargando / listo / error y opción de reintentar. */
export function useDatos<T>(cargar: () => Promise<T>) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  const recargar = useCallback(async () => {
    setCargando(true);
    setError(null);
    try {
      setDatos(await cargar());
    } catch (e) {
      setError(e instanceof ApiError ? e.detalle : String(e));
    } finally {
      setCargando(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- la función de carga es estable por página
  }, []);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  return { datos, error, cargando, recargar };
}

/** Tarjeta de métrica como `st.metric(border=True)` de la versión Streamlit. */
export function Metrica({ titulo, valor, icono, nota }: { titulo: string; valor: string | number; icono: string; nota?: string }) {
  return (
    <div className="metrica">
      <p className="metrica-titulo">
        <Icono nombre={icono} /> {titulo}
      </p>
      <p className="metrica-valor">{valor}</p>
      {nota && <p className="metrica-nota">{nota}</p>}
    </div>
  );
}

/** Mensaje de carga o de error común a las páginas del panel. */
export function EstadoCarga({ cargando, error, onReintentar }: { cargando: boolean; error: string | null; onReintentar: () => void }) {
  if (cargando) return <p className="leyenda" role="status">Cargando…</p>;
  if (!error) return null;
  return (
    <div className="error" role="alert">
      <p>{error}</p>
      <button type="button" onClick={onReintentar}>
        Reintentar
      </button>
    </div>
  );
}

/** Barra horizontal de 0 a 1 con su valor (reemplaza las gráficas de barras de Streamlit). */
export function Barra({ etiqueta, valor, maximo = 1, formato }: { etiqueta: string; valor: number; maximo?: number; formato?: (v: number) => string }) {
  const ancho = Math.max(0, Math.min(100, (valor / maximo) * 100));
  return (
    <div className="barra">
      <span className="barra-etiqueta">{etiqueta}</span>
      <span className="barra-pista" aria-hidden="true">
        <span className="barra-relleno" style={{ width: `${ancho}%` }} />
      </span>
      <span className="barra-valor">{formato ? formato(valor) : valor}</span>
    </div>
  );
}

export const pct = (v: number) => `${Math.round(v * 100)} %`;
