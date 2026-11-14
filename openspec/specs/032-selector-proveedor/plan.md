# Plan · SPEC-032 · Elegir el proveedor del LLM desde el frontend

## Diseño
Hook `useProveedor` y `<select>` en el encabezado; se pasa al chat.

## Decisiones
- Por defecto Claude: es el modelo evaluado (v3 cita la fuente en el 100 %).

## Contrato
Campo `proveedor` de `AgenteIn`.

## Riesgos
- Sin clave de Anthropic, la API responde el error y se ve en la burbuja.

## Alternativas descartadas
- Cambiar el `.env`: afecta a todo el equipo y requiere reiniciar.

## Estrategia de pruebas
Prueba del cuerpo de la petición con `fetch` falso. Pruebas AAA sin red ni API de pago.
