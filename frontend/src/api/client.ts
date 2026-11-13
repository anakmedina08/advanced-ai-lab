/**
 * Cliente tipado de la API FastAPI: timeout, reintentos en GET y errores como `ApiError`.
 *
 * Todas las llamadas del frontend pasan por aquí; ningún componente usa `fetch` directo ni
 * habla con un modelo: la frontera frontend/backend queda en este archivo.
 */

import { leerSSE } from "./sse";
import type {
  AgenteIn,
  AgenteOut,
  CheckpointOut,
  ConversacionOut,
  ErrorOut,
  EventoAgente,
  FotoOut,
  HealthOut,
  PerfilOut,
} from "./types";

export const API_URL: string = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";
const TIMEOUT_MS = 30_000;
const REINTENTOS_GET = 2;

/** Error de la API o de la red, con lo necesario para mostrarlo y depurarlo. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public codigo: string,
    public detalle: string,
    public requestId: string | null = null,
  ) {
    super(detalle);
    this.name = "ApiError";
  }
}

function detalleLegible(cuerpo: Partial<ErrorOut>): string {
  const d = cuerpo.detalle;
  if (Array.isArray(d)) return d.map((c) => `${c.campo}: ${c.mensaje}`).join(" · ");
  if (typeof d === "string") return d;
  return cuerpo.error ?? "Error desconocido";
}

async function aError(respuesta: Response): Promise<ApiError> {
  let cuerpo: Partial<ErrorOut> = {};
  try {
    cuerpo = (await respuesta.json()) as Partial<ErrorOut>;
  } catch {
    // respuesta sin JSON (p. ej., un proxy): se usa el status
  }
  const rid = cuerpo.request_id ?? respuesta.headers.get("X-Request-ID");
  return new ApiError(respuesta.status, cuerpo.error ?? "http", detalleLegible(cuerpo), rid);
}

/** `fetch` con timeout; los errores de red se traducen a `ApiError` (status 0). */
export async function pedir(
  ruta: string,
  init: RequestInit = {},
  { timeoutMs = TIMEOUT_MS, señal }: { timeoutMs?: number; señal?: AbortSignal } = {},
): Promise<Response> {
  const control = new AbortController();
  const reloj = setTimeout(() => control.abort(new DOMException("timeout", "TimeoutError")), timeoutMs);
  señal?.addEventListener("abort", () => control.abort(señal.reason), { once: true });
  try {
    const respuesta = await fetch(`${API_URL}${ruta}`, { ...init, signal: control.signal });
    if (!respuesta.ok) throw await aError(respuesta);
    return respuesta;
  } catch (e) {
    if (e instanceof ApiError) throw e;
    if (control.signal.aborted && !señal?.aborted) {
      throw new ApiError(0, "timeout", `La API no respondió en ${timeoutMs / 1000} s.`);
    }
    if (señal?.aborted) throw new ApiError(0, "cancelado", "Petición cancelada.");
    throw new ApiError(0, "red", "No hay conexión con la API. ¿Está corriendo `make api`?");
  } finally {
    clearTimeout(reloj);
  }
}

/** GET con reintentos ante errores de red o 5xx (los 4xx no se reintentan). */
export async function obtener<T>(ruta: string, reintentos = REINTENTOS_GET): Promise<T> {
  for (let intento = 0; ; intento++) {
    try {
      return (await (await pedir(ruta)).json()) as T;
    } catch (e) {
      const reintentable = e instanceof ApiError && (e.status === 0 || e.status >= 500);
      if (!reintentable || intento >= reintentos) throw e;
      await new Promise((r) => setTimeout(r, 300 * 2 ** intento));
    }
  }
}

const json = (cuerpo: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(cuerpo),
});

export const enviarMensaje = async (entrada: AgenteIn): Promise<AgenteOut> =>
  (await (await pedir("/agente/mensajes", json(entrada), { timeoutMs: 120_000 })).json()) as AgenteOut;

/** Turno del agente en streaming: entrega cada evento SSE tipado; se cancela con `señal`. */
export async function* streamAgente(entrada: AgenteIn, señal?: AbortSignal): AsyncGenerator<EventoAgente> {
  const respuesta = await pedir("/agente/stream", json(entrada), { timeoutMs: 180_000, señal });
  if (!respuesta.body) throw new ApiError(0, "red", "El navegador no entregó el cuerpo del streaming.");
  for await (const { datos } of leerSSE(respuesta.body)) {
    yield JSON.parse(datos) as EventoAgente;
  }
}

export const historial = (id: string) => obtener<ConversacionOut>(`/agente/conversaciones/${encodeURIComponent(id)}`);
export const checkpoints = (id: string) =>
  obtener<CheckpointOut[]>(`/agente/conversaciones/${encodeURIComponent(id)}/checkpoints`);
export const borrarConversacion = async (id: string) => {
  await pedir(`/agente/conversaciones/${encodeURIComponent(id)}`, { method: "DELETE" });
};
export const perfil = (usuario: string) => obtener<PerfilOut>(`/agente/usuarios/${encodeURIComponent(usuario)}/perfil`);
export const borrarPerfil = async (usuario: string) => {
  await pedir(`/agente/usuarios/${encodeURIComponent(usuario)}/perfil`, { method: "DELETE" });
};
export const salud = () => obtener<HealthOut>("/health", 0);

/** Foto → «¿qué hago?»: multipart con la imagen; la API difumina personas antes de usarla. */
export async function analizarFoto(archivo: File, señal?: AbortSignal): Promise<FotoOut> {
  const datos = new FormData();
  datos.append("archivo", archivo);
  const query = "interpretar=true&responder=true&devolver_imagen=true";
  const respuesta = await pedir(`/fotos?${query}`, { method: "POST", body: datos }, { timeoutMs: 120_000, señal });
  return (await respuesta.json()) as FotoOut;
}
