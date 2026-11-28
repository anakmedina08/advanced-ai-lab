# SPEC-083 · Auditoría de QA con Playwright sobre la app desplegada

> Curso: Técnicas Avanzadas de IA (551462) · Story points: **3** · Responsable: Katherine Medina ·
> Anuncio: [551462 · 008](../../../docs/anuncios/README.md) (sección 7, «QA con Playwright»).
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El anuncio 008 exige «Playwright instalado y una corrida de QA en verde sobre la app desplegada»
antes de la sustentación, con las pruebas en `tests/e2e/`. Hoy las más de 2.000 pruebas de `pytest`
revisan el código por dentro, pero nada revisa el sitio publicado como lo ve un usuario: errores de
consola, respuestas 404/500 o fallas en pantalla de teléfono.

## Historia
**Como** equipo que sustenta en vivo, **quiero** un robot que recorra la app desplegada en el
navegador **para** encontrar los errores antes de que los vean los invitados.

## Requisitos
- **R083.1** Playwright DEBE instalarse con `uv` como dependencia de desarrollo (sin pip).
- **R083.2** Las pruebas DEBEN vivir en `tests/e2e/` y marcarse con `e2e`; `uv run pytest` (la suite
  normal y la CI) NO DEBE correrlas, porque dependen de la red.
- **R083.3** DEBEN recorrer el sitio público, el asistente y el panel del equipo en **teléfono
  (390 × 844)** y **escritorio (1440 × 900)**, sin errores de consola ni respuestas 4xx/5xx.
- **R083.4** DEBEN verificar que `GET /health` de la API responda `status: ok` con el modelo YOLO.
- **R083.5** DEBEN verificar que el chat con IA sin código de acceso responda un error controlado
  (no un 500) y que un archivo inválido en `/fotos` reciba 400.
- **R083.6** La URL base DEBE poder cambiarse por variables de entorno (`E2E_SITIO`, `E2E_APP`,
  `E2E_API`) para correr contra local o contra otro despliegue.

## Criterios de aceptación
- **AC1** · **Dado** el sitio desplegado, **cuando** se corre `uv run pytest tests/e2e -m e2e`,
  **entonces** todas las pruebas pasan.
- **AC2** · **Dado** `uv run pytest -q`, **cuando** corre la suite normal, **entonces** las pruebas
  `e2e` no se ejecutan y la suite sigue sin red.
- **AC3** · **Dado** una página que devuelve 404 o escribe un error en la consola, **cuando** corre la
  prueba de recorrido, **entonces** falla y nombra la URL o el mensaje.

## Fuera de alcance
- La conversación por WhatsApp: Playwright no entra a WhatsApp; se prueba desde el teléfono.
- Correr las pruebas e2e en la CI (dependen del despliegue y de la red).
