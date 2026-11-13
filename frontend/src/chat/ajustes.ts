import { useState } from "react";

/** Modos de contexto: el agente M2 (por defecto) y los modos de Q&A de las fases 1 y 2 (`controller.assistant.MODES`). */
export const MODOS = [
  { id: "agente-m2", nombre: "Agente con router, memoria y tools (Módulo 2)", agente: true },
  { id: "completo", nombre: "Toda la base (Fase 1)", agente: false },
  { id: "reducido", nombre: "Contexto reducido por palabras", agente: false },
  { id: "rag", nombre: "RAG con embeddings (Fase 2)", agente: false },
  { id: "agente", nombre: "Agente con subagentes · Deep Agents (Fase 2)", agente: true },
] as const;

export const VERSIONES = ["v1", "v2", "v3", "v4"] as const;

export const AYUDA_MODOS =
  "Agente M2: el router decide si buscar (Qdrant), consultar los datos o responder directo, con memoria y streaming. " +
  "Toda la base: todo el conocimiento en el prompt. Reducido: fragmentos por palabras, rápido en CPU. " +
  "RAG: fragmentos por embeddings locales (Ollama + Qdrant). Deep Agents: busca y delega el análisis a un subagente.";

export interface Ajustes {
  proveedor: string;
  modo: string;
  version: string;
}

const CLAVE = "sb.ajustes";
const POR_DEFECTO: Ajustes = {
  proveedor: (import.meta.env.VITE_LLM_PROVIDER as string | undefined) ?? "anthropic",
  modo: "agente-m2",
  version: "v3",
};

function leer(): Ajustes {
  try {
    const anterior = localStorage.getItem("sb.proveedor");
    const guardado = JSON.parse(localStorage.getItem(CLAVE) ?? "{}") as Partial<Ajustes>;
    return { ...POR_DEFECTO, ...(anterior ? { proveedor: anterior } : {}), ...guardado };
  } catch {
    return POR_DEFECTO;
  }
}

/** Ajustes de la sesión (como en la página Configuración de Streamlit), recordados en el navegador. */
export function useAjustes(): [Ajustes, (cambio: Partial<Ajustes>) => void] {
  const [ajustes, setAjustes] = useState<Ajustes>(leer);
  const cambiar = (cambio: Partial<Ajustes>) =>
    setAjustes((actual) => {
      const nuevo = { ...actual, ...cambio };
      try {
        localStorage.setItem(CLAVE, JSON.stringify(nuevo));
        if (cambio.proveedor) localStorage.setItem("sb.proveedor", cambio.proveedor);
      } catch {
        // sin almacenamiento: solo dura la sesión
      }
      return nuevo;
    });
  return [ajustes, cambiar];
}
