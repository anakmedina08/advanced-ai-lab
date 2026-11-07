---
name: respuesta-cliente
description: Da a la respuesta del asistente el formato de atención al cliente de una aseguradora - respuesta directa, pasos numerados para trámites y cierre con el canal oficial y la fuente. Úsala en preguntas sobre cómo hacer un trámite, reclamar o contactar.
license: MIT
metadata:
  uso: asistente
  autor: equipo-sb-asistente
---

## Qué hace
- Empieza con la respuesta en una frase, sin saludo largo.
- Si la pregunta es un trámite (reclamar, pagar, descargar, actualizar), lista los pasos numerados (máximo 5) tal como aparecen en el conocimiento.
- Cierra con una línea «Canal sugerido:» con el canal oficial más directo que aparezca en el conocimiento (WhatsApp, línea o #322).
- Mantiene la línea final «Fuente:» con la URL.

## Reglas
- No inventa pasos, plazos ni números: si el conocimiento no los trae, lo dice.
- No reemplaza las reglas del asistente.
