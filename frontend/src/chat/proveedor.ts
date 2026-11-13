import { useState } from "react";

/** Proveedores que acepta la API (`config.PROVIDERS`). Claude es el evaluado (v3 cita la fuente 100 %). */
export const PROVEEDORES = [
  { id: "anthropic", nombre: "Claude" },
  { id: "ollama", nombre: "Ollama (local)" },
  { id: "deepseek", nombre: "DeepSeek" },
] as const;

const CLAVE = "sb.proveedor";
const POR_DEFECTO = (import.meta.env.VITE_LLM_PROVIDER as string | undefined) ?? "anthropic";

/** Proveedor elegido en el encabezado, recordado en el navegador. */
export function useProveedor(): [string, (id: string) => void] {
  const [proveedor, setProveedor] = useState<string>(() => {
    try {
      return localStorage.getItem(CLAVE) ?? POR_DEFECTO;
    } catch {
      return POR_DEFECTO;
    }
  });
  const elegir = (id: string) => {
    setProveedor(id);
    try {
      localStorage.setItem(CLAVE, id);
    } catch {
      // sin almacenamiento: solo dura la sesión
    }
  };
  return [proveedor, elegir];
}
