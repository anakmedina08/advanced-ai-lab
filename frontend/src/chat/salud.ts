import { useCallback, useEffect, useState } from "react";

import { ApiError, salud } from "../api/client";
import type { HealthOut } from "../api/types";

export type EstadoSalud =
  | { fase: "cargando" }
  | { fase: "ok"; datos: HealthOut }
  | { fase: "caida"; detalle: string };

/** Consulta `GET /health` al montar y cuando se pide reintentar (sin sondeo periódico). */
export function useSalud() {
  const [estado, setEstado] = useState<EstadoSalud>({ fase: "cargando" });

  const consultar = useCallback(async () => {
    setEstado({ fase: "cargando" });
    try {
      setEstado({ fase: "ok", datos: await salud() });
    } catch (e) {
      setEstado({ fase: "caida", detalle: e instanceof ApiError ? e.detalle : String(e) });
    }
  }, []);

  useEffect(() => {
    void consultar();
  }, [consultar]);

  return { estado, reintentar: consultar };
}
