---
name: comparar-seguros
description: Compara dos o más seguros en una tabla breve (producto, para quién es, qué cubre y fuente) usando solo la base pública. Úsala cuando el usuario pida diferencias entre seguros o elegir entre opciones.
license: MIT
metadata:
  uso: asistente
  autor: equipo-sb-asistente
---

## Qué hace
- Responde con una tabla en Markdown con las columnas: Producto | Para quién es | Qué cubre | Fuente.
- Una fila por seguro mencionado en la pregunta o relevante para ella (máximo 4).
- Debajo de la tabla, una frase con la diferencia principal.

## Reglas
- Sin precios, primas ni porcentajes salvo que aparezcan literalmente en el conocimiento.
- Si un dato no está, escribe «no indicado en la página» en la celda.
- Cada fila cita su URL.
