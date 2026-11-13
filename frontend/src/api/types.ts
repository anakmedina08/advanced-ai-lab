/** Contratos de la API (espejo de `src/sb_asistente/view/schemas.py`). */

export type Ruta = "directo" | "datos" | "rag" | "mixto" | "fuera_de_alcance";

export interface ErrorOut {
  error: string;
  detalle: string | { campo: string; mensaje: string }[] | Record<string, unknown> | null;
  ruta: string;
  request_id: string;
}

export interface DecisionOut {
  ruta: Ruta;
  confianza: number;
  senales: string[];
  tools: string[];
  cautela: boolean;
}

export interface PasoAgenteOut {
  tool: string;
  argumentos: Record<string, unknown>;
  resultado: string;
}

export interface TiempoTool {
  tool: string;
  ms: number;
  error?: string;
}

export interface SalidaAgenteOut {
  respuesta: string;
  fuentes: string[];
  intencion: string;
  confianza: "alta" | "media" | "baja";
  productos_recomendados: string[];
  requiere_asesor: boolean;
}

export interface AgenteOut {
  conversacion_id: string;
  usuario_id: string | null;
  salida: SalidaAgenteOut;
  decision: DecisionOut;
  pasos: PasoAgenteOut[];
  fuentes_descartadas: string[];
  mensajes_en_memoria: number;
  tiempos_tools: TiempoTool[];
  ms_total: number;
}

export interface AgenteIn {
  mensaje: string;
  conversacion_id: string;
  usuario_id?: string | null;
  proveedor?: string | null;
}

/** Eventos del flujo SSE de `POST /agente/stream`. */
export type EventoAgente =
  | ({ tipo: "router" } & DecisionOut)
  | { tipo: "tool_inicio"; tool: string; argumentos: Record<string, unknown> }
  | { tipo: "tool_fin"; tool: string; resumen: string }
  | { tipo: "texto"; delta: string }
  | { tipo: "final"; turno: AgenteOut }
  | { tipo: "error"; detalle: string };

export interface MensajeHistorial {
  rol: "usuario" | "asistente";
  texto: string;
}

export interface ConversacionOut {
  conversacion_id: string;
  mensajes: MensajeHistorial[];
}

export interface CheckpointOut {
  checkpoint_id: string;
  paso: number;
  fecha: string;
  mensajes: number;
  siguiente: string[];
}

export interface PerfilOut {
  usuario_id: string;
  hechos: Record<string, string>;
}

export interface HealthOut {
  status: "ok" | "degradado";
  version: string;
  llm: string;
  componentes: Record<string, boolean>;
}

export interface CajaOut {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface DeteccionOut {
  clase: string;
  etiqueta: string;
  confianza: number;
  caja: CajaOut;
}

export interface RespuestaOut {
  texto: string;
  tarea: string;
  version_prompt: string;
  latencia_s: number;
  tokens_contexto: number;
  cita_fuente: boolean;
  fuentes: string[];
}

export interface FotoOut {
  tiempo_inferencia_ms: number;
  ancho: number;
  alto: number;
  personas_difuminadas: number;
  detecciones: DeteccionOut[];
  sugerencias: { tema: string; nombre: string; objetos: string[]; confianza: number; pregunta: string; paginas: string[] }[];
  escena: { situacion: string; descripcion: string; confianza: string; contiene_documento: boolean } | null;
  plan: { tipo: "siniestro" | "asegurar" | "documento" | "ninguno"; nombre: string; pregunta: string | null; paginas: string[] };
  aviso: string | null;
  respuesta: RespuestaOut | null;
  recomendaciones: { product_id: string; nombre: string; linea: string; razon: string }[];
  imagen_jpeg_b64?: string | null;
}

export interface EtapaOut {
  etapa: string;
  capa: string;
  hecha: boolean;
  metricas: Record<string, number | string>;
}

export interface CorpusOut {
  url: string;
  titulo: string;
  seccion: string;
  fecha_captura: string;
  sha256: string;
  tokens: number;
}

export interface EvaluacionOut {
  modelo: string;
  version: string;
  preguntas: number;
  keyword_hit_promedio: number;
  tasa_cita_fuente: number;
  tasa_fallback_correcto: number;
  latencia_promedio_s: number;
}

export interface CorridaOut {
  nombre: string;
  fecha: number;
  commit: string;
  parametros: Record<string, string>;
  metricas: Record<string, number>;
}

export interface ExperimentosOut {
  activa: boolean;
  url_ui: string;
  nombres: Record<string, string>;
  experimentos: Record<string, CorridaOut[]>;
}

export interface RequisitoOut {
  requisito: string;
  estado: "cumplido" | "en curso" | "pendiente";
  evidencia: string;
}

export interface ProyectoOut {
  secciones: Record<string, RequisitoOut[]>;
  contadores: Record<string, number>;
  corridas_mlflow: number | null;
  enlaces: Record<string, string>;
}

export interface SistemaOut {
  base_lista: boolean;
  vision_instalada: boolean;
  clave_anthropic: boolean;
  paginas: number | null;
  fragmentos: number | null;
  tokens_contexto: number | null;
}

export interface ProcesoOut {
  documentos: number;
  chunks: number;
  duplicadas_descartadas: number;
}

export interface DescubrimientoOut {
  total_sitemap: number;
  seleccionadas: number;
  descartadas: number;
}
