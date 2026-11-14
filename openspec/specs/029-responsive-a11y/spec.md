# SPEC-029 · Diseño responsive y accesible

> Curso: Técnicas M2 (3.1) · Story points: **2** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La rúbrica pide interfaz responsive; además el chat en streaming debe ser usable con teclado y lector de pantalla.

## Historia
**Como** usuaria en el celular, **quiero** usar el chat y la foto en una pantalla pequeña, **para** consultar desde cualquier dispositivo.

## Requisitos
- **R029.1** En pantallas < 768 px la barra de hilos DEBE plegarse tras un botón y el contenido DEBE ocupar el ancho sin scroll horizontal.
- **R029.2** La zona de mensajes DEBE tener `aria-live="polite"`; los botones DEBEN tener etiqueta y foco visible.
- **R029.3** DEBE respetar `prefers-color-scheme` (tema claro y oscuro).

## Criterios de aceptación
- **AC1** · **Dado** un ancho de 375 px, **cuando** se abre el chat, **entonces** no hay scroll horizontal y la barra está plegada.
- **AC2** · **Dado** solo teclado, **cuando** se navega, **entonces** todos los controles reciben foco visible.

## Fuera de alcance
Aplicación móvil nativa.

## Métricas de éxito
0 scroll horizontal a 375 px.
