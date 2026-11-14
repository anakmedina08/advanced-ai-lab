# SPEC-046 · Paridad con la versión Streamlit: modos de contexto, reprocesar y foto con Claude

> Curso: Técnicas M2 · Gestión M3 · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
En el frontend React faltaban funciones de la versión Streamlit (modo de contexto y versión del prompt, estado con métricas del corpus, reprocesar y descubrir en el pipeline) y la foto fallaba porque no enviaba el proveedor: la API usaba el de `.env` (Ollama, sin visión).

## Historia
**Como** integrante del equipo, **quiero** tener en el frontend lo mismo que tenía en Streamlit y que la foto use Claude, **para** no perder funciones al dejar Streamlit.

## Requisitos
- **R046.1** La foto DEBE enviar el proveedor elegido en Configuración (Claude por defecto).
- **R046.2** Configuración DEBE permitir elegir el modo de contexto (Agente con router M2, Toda la base, Reducido, RAG, Agente Deep Agents) y la versión del prompt (v1–v4); el chat DEBE usar `POST /preguntas` con esos ajustes cuando el modo no sea el agente M2.
- **R046.3** `POST /preguntas` DEBE aceptar los cuatro modos de `controller.assistant.MODES`.
- **R046.4** El estado del sistema DEBE mostrar las insignias (base lista, visión instalada, clave de Anthropic) y las métricas del corpus (páginas, fragmentos, tokens) con `GET /sistema`.
- **R046.5** El pipeline DEBE tener «Reprocesar sin volver a la web» (`POST /pipeline/procesar`) y «Descubrir en vivo» (`POST /pipeline/descubrir`).
- **R046.6** Los enlaces Markdown de `docs/requisitos.md` DEBEN verse como enlaces en Entregables por curso.

## Criterios de aceptación
- **AC1** · **Dado** Claude elegido en Configuración, **cuando** se sube una foto, **entonces** la petición lleva `proveedor=anthropic` y no falla.
- **AC2** · **Dado** el modo «Reducido» y la versión v1, **cuando** se pregunta en el chat, **entonces** se llama a `/preguntas` con `modo=reducido` y `version=v1`.

## Fuera de alcance
Reprocesar con scraping en vivo (va por `make data`).

## Métricas de éxito
Mismas funciones que la página Streamlit.
