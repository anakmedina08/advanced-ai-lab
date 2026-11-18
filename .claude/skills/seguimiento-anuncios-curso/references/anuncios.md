# Procedimiento detallado · anuncios del curso → requisitos del proyecto

El objetivo es que **ningún requisito del profesor se pierda** y que cada uno quede trazado hasta
una evidencia en el repositorio.

## 1. Buscar en el correo

Se usa el conector de correo del agente (Gmail). Los anuncios del campus llegan con este asunto:

```
551462-B-1-(2026-2S): Anuncio 006: Sustentación del Módulo 2
└─┬──┘ └┬┘  └──┬───┘          └┬┘  └──────────┬───────────┘
código  grupo  periodo        número          título
```

| Búsqueda | Uso |
|---|---|
| `from:noreply@uaovirtual.edu.co ("551462" OR "551475") newer_than:120d` | **todo** lo publicado en los foros de las dos materias, incluidos los avisos sin número |
| `from:noreply@uaovirtual.edu.co ("GESTION DE PROYECTO" OR "TÉCNICAS AVANZADAS") (vence OR "contenido nuevo")` | vencimientos de tareas y material nuevo del campus |
| `subject:"Anuncio 007"` | un anuncio concreto |

Lecciones de la primera ejecución real (noviembre de 2026):
- **No todos los avisos llevan número.** Hay publicaciones sin número ("Reposición agendada", "Grupos conformados", "Mensaje de bienvenida"). Por eso se busca por código de curso y no por la palabra "Anuncio".
- **El separador del número varía:** `Anuncio 006: …` y `Anuncio 001 · …`. El número se extrae con `Anuncio (\d{3})\s*[:·]`.
- **Hay duplicados.** El 003 de Técnicas llegó dos veces con títulos distintos. Se conserva el más reciente.
- **Los avisos "(registro histórico)" o "borrado"** se registran como logística y no generan requisitos.
- **La búsqueda solo devuelve vistas previas.** El cuerpo completo se lee con la lectura del hilo en texto plano.
- **Otras materias usan el mismo remitente** (por ejemplo 551469). Se filtra por los códigos del índice.

- Cada código de curso es una materia. La tabla de `docs/anuncios/README.md` dice qué código corresponde a cuál; en este proyecto:

  | Código | Materia | Ejemplo de asunto |
  |---|---|---|
  | 551462 | Técnicas Avanzadas de IA | `551462-B-1-(2026-2S): Anuncio 006: Sustentación del Módulo 2` |
  | 551475 | Gestión de Proyectos en IA y CD | `551475-B-1-(2026-2S): Anuncio 005: Grabación de la Clase 3 — Consolas Agénticas (OpenCode)` |

- Se clasifica cada anuncio por **tipo**, porque cada tipo aporta algo distinto:

  | Tipo | Señal en el título | Qué se extrae |
  |---|---|---|
  | Grabación o clase | "Grabación de la Clase N — <tema>" | tema, herramientas mostradas, buenas prácticas, tareas |
  | Entrega o sustentación | "Sustentación", "Entrega", "Módulo N" | requisitos, entregables, rúbrica, fecha |
  | Herramientas o lineamientos | "Herramientas", "Lineamientos", "Actualización" | herramientas permitidas, **no permitidas** y reemplazos |
  | Logística | horarios, aulas, enlaces, reposiciones | solo la fecha, si afecta una entrega |
  | Vencimiento | "Vence el …", "Tarea … es nuevo" (avisos automáticos del campus) | nombre de la tarea y fecha y hora límite |
- Se leen **el cuerpo y los adjuntos** (PDF, enlaces al campus). Si un adjunto no se puede abrir, se marca ❓ y se pide al usuario.
- **Solo lectura:** el agente nunca responde, reenvía, etiqueta ni borra correos.

## 2. Filtrar lo nuevo

Un anuncio es nuevo si su `<código>` + `<número>` no aparece en el índice `docs/anuncios/README.md`.
Se procesan en orden ascendente, porque un anuncio posterior puede corregir a uno anterior.

## 3. Extraer

Por cada anuncio se llena `docs/anuncios/<código>-anuncio-<NNN>.md` (plantilla en
`assets/plantillas/anuncios/anuncio.md` de esta skill):

- **Metadatos:** materia, número, fecha de recepción, módulo y fecha límite.
- **Requisitos:** uno por fila, redactados como algo verificable ("API con JSON-RPC 2.0", no "usar RPC").
- **Componentes y herramientas** que menciona, con su nombre oficial y un enlace si lo trae.
  Si el nombre es ambiguo, se deja como ❓ con la frase original; **no se adivina**.
- **Entregables y formato:** repositorio, informe, video, sustentación, rúbrica de calificación.
- **Herramientas por estado**, porque la clase evoluciona y algunas dejan de aceptarse:
  - ✅ **recomendadas o exigidas:** se deben usar o demostrar;
  - ⚠️ **permitidas:** opcionales;
  - ⛔ **no permitidas o reemplazadas:** con el motivo y la que la reemplaza.

  Cada herramienta se consolida en `docs/anuncios/herramientas.md`, el catálogo vivo por materia
  (plantilla en `assets/plantillas/anuncios/herramientas.md`). Cuando la herramienta es un paquete,
  se llena la columna **Paquete** con su nombre exacto en PyPI o npm (`streamlit`, `gradio`).
  Es lo que verifica K4; las prácticas sin paquete (pip, notebooks) las revisa el agente. Si un anuncio posterior cambia el
  estado de una herramienta, se actualiza la fila y se anota el número del anuncio que la cambió.

- **Rúbrica:** cada criterio con su peso, porque dice dónde vale la pena invertir esfuerzo.
- **Precedencia:** si el anuncio dice que "prevalece sobre cualquier mención anterior", se marca así y se actualizan las filas afectadas.

**Nunca se copia** a `docs/` (el repo es público):
- contraseñas de grabaciones ni enlaces de Webex;
- enlaces de grupos de WhatsApp ni hojas de cálculo del curso;
- nombres de otros estudiantes ni el orden de sustentación de otros grupos;
- correos personales.

Se resume con palabras propias.

## 4. Contrastar con el proyecto

Cada requisito se busca en:
1. `docs/requisitos.md`, la matriz existente;
2. el código y la configuración (rutas, endpoints, dependencias en `pyproject.toml`);
3. los ADR y las specs (`openspec/specs/`).

| Estado | Criterio | Acción propuesta |
|---|---|---|
| ✅ | Hay evidencia verificable (ruta, endpoint, comando) | Agregar la evidencia a la fila |
| 🟡 | Existe, pero incompleto o sin documentar | Historia de ajuste |
| ❌ | No existe | Historia nueva + spec |
| ❓ | Requisito ambiguo | Pregunta al usuario, con la frase original |
| ⛔ | El equipo decide no hacerlo | Se registra con el motivo (*not planned*) |

## 5. Proponer y registrar

Se entrega al usuario una tabla con requisito, estado, evidencia o acción, esfuerzo estimado
(S/M/L) y fecha límite. Ordena primero lo ❌ con la fecha más cercana.

Con su aprobación:
- Rama `docs/anuncio-<código>-<NNN>`.
- Se crean:
  - `docs/anuncios/<código>-anuncio-<NNN>.md`;
  - la fila en el índice `docs/anuncios/README.md`;
  - las filas o la evidencia nuevas en `docs/requisitos.md`.
- Por cada ❌ o 🟡 se propone el issue con la plantilla `historia.yml`. El humano lo crea, o autoriza al agente a crearlo.
- Commit `docs(anuncios): incorporar anuncio <NNN> de <materia>`. El humano hace push y abre el PR.

### Herramientas no permitidas (crítico)

Si una herramienta ⛔ aparece en el proyecto, se reporta **primero**, antes que cualquier otra
brecha. Se busca su nombre en `pyproject.toml`, `uv.lock`, `frontend/package.json`, `src/`,
`Makefile`, los workflows y los ADR. La propuesta incluye la migración a la herramienta que la
reemplaza y un ADR que lo registre.

## 6. Verificaciones del seguimiento (dimensión K)

| ID | Peso | Verificación | Dónde mirar · qué cuenta como ✅ |
|---|---|---|---|
| K1 | 3 | Índice de anuncios | existe `docs/anuncios/README.md` con al menos un anuncio registrado |
| K2 | 3 | Cada anuncio registrado tiene su resumen | por cada fila del índice existe su `docs/anuncios/*-anuncio-*.md` |
| K3 | 3 | Sin requisitos pendientes sin plan | en `docs/requisitos.md` no hay filas ❌ ni ❓ (las ⛔ llevan motivo) |
| K4 | 3 | Sin herramientas no permitidas | existe el catálogo y ningún paquete ⛔ (columna Paquete) es dependencia en `pyproject.toml` o `frontend/package.json` ni se importa en `src/` (sin catálogo, ❌); las prácticas ⛔ sin paquete las revisa el agente |

Si el proyecto no es de un curso, la dimensión 9 aplica igual a los requisitos del cliente: actas,
correos de alcance o tickets.
