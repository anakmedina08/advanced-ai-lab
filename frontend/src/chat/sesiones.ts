/**
 * Sesiones del navegador: lista de hilos y un `usuario_id` anónimo, en `localStorage`.
 *
 * Si el almacenamiento no está disponible (modo privado, bloqueado), todo sigue funcionando en
 * memoria: solo se pierde la lista al recargar.
 */

import { useCallback, useState } from "react";

export interface Hilo {
  id: string;
  titulo: string;
  creado: string;
}

const CLAVE_HILOS = "sb.hilos";
const CLAVE_USUARIO = "sb.usuario";
const CLAVE_ACTIVO = "sb.hilo-activo";

function leer<T>(clave: string, defecto: T): T {
  try {
    const valor = localStorage.getItem(clave);
    return valor ? (JSON.parse(valor) as T) : defecto;
  } catch {
    return defecto;
  }
}

function escribir(clave: string, valor: unknown): void {
  try {
    localStorage.setItem(clave, JSON.stringify(valor));
  } catch {
    // almacenamiento no disponible: se sigue en memoria
  }
}

export const nuevoId = (prefijo: string) => `${prefijo}-${crypto.randomUUID().replace(/-/g, "").slice(0, 12)}`;

/** Hilos del usuario, hilo activo y `usuario_id` estable entre visitas. */
export function useSesiones() {
  const [usuarioId] = useState<string>(() => {
    const guardado = leer<string | null>(CLAVE_USUARIO, null);
    if (guardado) return guardado;
    const id = nuevoId("usuario");
    escribir(CLAVE_USUARIO, id);
    return id;
  });
  const [hilos, setHilos] = useState<Hilo[]>(() => leer<Hilo[]>(CLAVE_HILOS, []));
  const [activo, setActivo] = useState<string>(() => leer<string | null>(CLAVE_ACTIVO, null) ?? nuevoId("hilo"));

  const guardarHilos = useCallback((siguiente: Hilo[]) => {
    setHilos(siguiente);
    escribir(CLAVE_HILOS, siguiente);
  }, []);

  const elegir = useCallback((id: string) => {
    setActivo(id);
    escribir(CLAVE_ACTIVO, id);
  }, []);

  const nuevo = useCallback(() => elegir(nuevoId("hilo")), [elegir]);

  /** Registra el hilo activo en la lista al enviar su primer mensaje. */
  const titular = useCallback(
    (texto: string) => {
      if (hilos.some((h) => h.id === activo)) return;
      const titulo = texto.length > 48 ? `${texto.slice(0, 47)}…` : texto;
      guardarHilos([{ id: activo, titulo, creado: new Date().toISOString() }, ...hilos]);
      escribir(CLAVE_ACTIVO, activo);
    },
    [activo, hilos, guardarHilos],
  );

  const quitar = useCallback(
    (id: string) => {
      guardarHilos(hilos.filter((h) => h.id !== id));
      if (id === activo) nuevo();
    },
    [hilos, activo, guardarHilos, nuevo],
  );

  return { usuarioId, hilos, activo, elegir, nuevo, titular, quitar };
}
