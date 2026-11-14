# Plan · SPEC-010 · CORS configurable para el frontend desacoplado

## Diseño
`config.FRONTEND_ORIGINS` y `CORSMiddleware` en `api.py`.

## Decisiones
- Lista blanca explícita, nunca `*`.

## Contrato
Variable `FRONTEND_ORIGINS`.

## Riesgos
- Olvidar el origen del despliegue: queda documentado en `.env.example`.

## Alternativas descartadas
- Proxy de Vite: oculta la frontera frontend/backend que la rúbrica quiere ver en Network.

## Estrategia de pruebas
`tests/test_cors.py` con *preflight* simulado. Pruebas AAA sin red ni API de pago.
