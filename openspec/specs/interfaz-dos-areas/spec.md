# Spec · Interfaz en dos áreas: atención al cliente y panel del equipo

> Desglose de la tarea T-41 de [`fase2-producto-unico`](../fase2-producto-unico/). Plan en
> [`plan.md`](plan.md); trabajo en [`tasks.md`](tasks.md). Decisión: ADR-021.

## Contexto

La interfaz de Streamlit tenía 6 pestañas que mezclaban lo del cliente (preguntar, foto) con lo
técnico (versión del prompt, *chunks*, tokens, pipeline). Un producto empresarial separa esas
audiencias; el jurado sigue viendo lo técnico en su propia área.

## Requisitos

### R25 · Dos áreas separadas
- La navegación DEBE tener dos secciones: «Atención al cliente» (Asistente, Foto: ¿qué hago?, Guías
  de seguros) y «Panel del equipo» (Configuración, Pipeline de datos, Evaluación).
- El área del cliente NO DEBE mostrar proveedor, modo de contexto, versión del prompt, fragmentos ni
  tokens; esos ajustes se eligen en «Configuración» y se guardan en la sesión.
- La página por defecto DEBE ser «Asistente».
- **Escenario:** dada la página «Asistente», entonces ningún control menciona «prompt» ni «proveedor».

### R26 · Asistente en formato chat
- Las preguntas DEBEN responderse en un chat con historial; cada respuesta DEBE mostrar sus fuentes
  como enlaces cortos.
- Antes del primer mensaje DEBEN ofrecerse preguntas sugeridas; al elegir una, se responde y las
  sugerencias desaparecen.
- «Nueva conversación» DEBE aparecer en cuanto exista una respuesta y DEBE borrar el historial sin
  volver a enviar la última sugerencia.
- Un error del modelo DEBE mostrarse como mensaje del asistente sin romper la página.
- **Escenario:** dada una pregunta sugerida y luego «Nueva conversación», entonces el modelo recibió
  una sola pregunta.

### R27 · Estilo corporativo neutro
- El tema DEBE configurarse en `.streamlit/config.toml` (sin CSS), con íconos Material Symbols en
  lugar de emojis y sin las opciones de desarrollador.
- NO DEBE usar el logo, los colores ni el aspecto de Seguros Bolívar; el aviso «No es un canal
  oficial de la compañía» DEBE verse siempre.
- El límite de carga DEBE coincidir con el de la foto (8 MB).

### R28 · Configuración persistente entre páginas
- Un ajuste hecho en «Configuración» (p. ej., versión del prompt v4) DEBE aplicarse en el chat
  aunque se cambie de página.
- **Escenario:** dada la versión v4 elegida en «Configuración», cuando se pregunta en «Asistente»,
  entonces el asistente recibe `version = "v4"`.
