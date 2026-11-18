---
name: seguimiento-anuncios-curso
description: Lee en Gmail los anuncios del profesor de Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) de la UAO, extrae requisitos, rúbricas, fechas y herramientas exigidas o prohibidas, y los contrasta con el repositorio. Úsala cuando llegue un anuncio nuevo, antes de planear la semana o una sustentación, o para saber si el proyecto usa algo que el curso ya no permite.
license: MIT
compatibility: Requiere el conector de Gmail del agente con la cuenta institucional @uao.edu.co. Si no está, el usuario pega el anuncio.
metadata:
  uso: desarrollo
  autor: Daniel Silva y Katherine Medina
  version: "1.0"
---

# Seguimiento de anuncios del curso

Skill **propia del equipo**, separada de `estandar-ia-profesional`, por tres motivos:
- **lee un correo personal;**
- depende de códigos de curso concretos;
- sirve solo mientras dure el semestre.

La skill de buenas prácticas se puede compartir sin ella.

```
seguimiento-anuncios-curso        estandar-ia-profesional
(qué pide el profesor)      ──▶   (qué tan profesional es el repo)
docs/anuncios/ + requisitos.md     lee esos archivos si existen
```

## Reglas

1. **Solo lectura del correo.** Nunca se responde, reenvía, etiqueta, archiva ni borra nada.
2. **Nada sensible al repo**, porque es público:
   - sin contraseñas de grabaciones ni enlaces de Webex;
   - sin enlaces de WhatsApp ni de hojas de cálculo del curso;
   - sin nombres de otros estudiantes ni el orden de otros grupos.
   Se resume con palabras propias.
3. **No se adivina.** Un término ambiguo queda ❓ con la frase original y se pregunta.
4. **El humano aprueba y sube.** El agente propone los archivos y la rama; el equipo hace push y abre el PR.

## Materias

| Código | Campus | Materia |
|---|---|---|
| 551462 | curso 16861 | Técnicas Avanzadas de IA aplicadas en Modelos de Lenguaje |
| 551475 | curso 16864 | Gestión de Proyectos en IA y CD |

Para otro semestre o materia, se agrega la fila aquí y en `docs/anuncios/README.md`.

## Flujo

1. **Buscar** con el conector de Gmail:
   `from:noreply@uaovirtual.edu.co ("551462" OR "551475") newer_than:120d`.
   Para los vencimientos de tareas del campus, ver [`references/anuncios.md`](references/anuncios.md).
2. **Filtrar** lo que no esté en `docs/anuncios/README.md`, en orden ascendente. Si no hay nada nuevo, se dice en una línea.
3. **Leer** cada hilo completo en texto plano; la búsqueda solo trae vistas previas.
4. **Clasificar:** clase, entrega, lineamientos, logística o vencimiento.
5. **Extraer:**
   - requisitos verificables;
   - rúbrica con pesos;
   - fechas;
   - herramientas ✅ exigidas, ⚠️ deseables y ⛔ no permitidas, con su paquete exacto si lo tienen;
   - si el anuncio dice que prevalece sobre los anteriores.
6. **Contrastar** con el repo, empezando por las herramientas ⛔. Cada requisito se marca ✅ (con evidencia), 🟡, ❌, ❓ o ⛔.
7. **Proponer:**
   - el resumen `docs/anuncios/<código>-anuncio-<NNN>.md`;
   - la fila del índice;
   - las filas del catálogo `docs/anuncios/herramientas.md`;
   - las filas nuevas de `docs/requisitos.md`;
   - una historia del Kanban por cada ❌.

   Todo va en la rama `docs/anuncio-<código>-<NNN>` y el commit `docs(anuncios): incorporar anuncio <NNN> de <materia>`.
8. **Cerrar** con una tabla de lo nuevo ordenada por fecha límite. Si el usuario quiere, sigue con
   `estandar-ia-profesional`, que ya verá esos requisitos como brechas.

Procedimiento detallado, lecciones de la primera ejecución y verificaciones: [`references/anuncios.md`](references/anuncios.md).

## Verificaciones (para el auditor del proyecto)

| ID | Peso | Verificación |
|---|---|---|
| K1 | 3 | `docs/anuncios/README.md` con al menos un anuncio registrado |
| K2 | 3 | Cada anuncio del índice tiene su resumen |
| K3 | 3 | `docs/requisitos.md` sin filas ❌ ni ❓ |
| K4 | 3 | Existe el catálogo y ningún paquete ⛔ es dependencia ni se importa en `src/` (sin catálogo, ❌) |

## Plantillas

| Plantilla | Destino |
|---|---|
| `assets/plantillas/anuncios/README.md` | `docs/anuncios/README.md` (índice) |
| `assets/plantillas/anuncios/anuncio.md` | `docs/anuncios/<código>-anuncio-<NNN>.md` |
| `assets/plantillas/anuncios/herramientas.md` | `docs/anuncios/herramientas.md` (catálogo) |
