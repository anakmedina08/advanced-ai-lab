# Plan · SPEC-027 · Foto «¿qué hago?» en el frontend con confianza y estados

## Diseño
`src/pages/Foto.tsx` y `CajasDeteccion` (SVG sobre la imagen); backend: campo opcional `imagen_jpeg_b64` en `FotoOut`.

## Decisiones
- Cajas en SVG escalable sobre la imagen: se ven bien en cualquier tamaño.

## Contrato
`POST /fotos?interpretar&responder&devolver_imagen` → `FotoOut.imagen_jpeg_b64`.

## Riesgos
- Imágenes grandes en base64 (+33 %): se reduce a 1280 px antes de codificar.

## Alternativas descartadas
- Difuminar en el navegador: la foto original saldría del equipo hacia la API igual.

## Estrategia de pruebas
Pytest del nuevo campo y Vitest de la validación. Pruebas AAA sin red ni API de pago.
