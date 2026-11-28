# Plan · SPEC-083

1. **Dependencia.** `uv add --dev pytest-playwright` (trae `playwright` y los *fixtures* `page` y
   `playwright` de pytest) y `uv run playwright install chromium`. Solo Chromium: es el navegador del
   proyector y basta para la auditoría.
2. **Aislamiento.** Marca `e2e` registrada en `[tool.pytest.ini_options]` y `-m 'not e2e'` en
   `addopts`: la suite normal y la CI no tocan la red (R083.2). Para la auditoría, `-m e2e` en la línea
   de comandos reemplaza al de `addopts`.
3. **Pruebas** en `tests/e2e/test_auditoria.py`:
   - Recorrido de páginas parametrizado por tamaño (teléfono y escritorio): escucha `console` (tipo
     `error`) y `response` (estado ≥ 400) y falla con la lista de lo encontrado (AC3).
   - `GET /health` de la API con `status: ok` y `modelo_yolo: true`.
   - Chat sin código: respuesta controlada con `codigo` en el cuerpo y estado < 500.
   - `POST /fotos` con un texto en lugar de imagen: 400.
4. **URL base.** Constantes leídas de `E2E_SITIO`, `E2E_APP` y `E2E_API`, con el Droplet por defecto.

## Decisiones
- **pytest-playwright y no `npm init playwright`:** el proyecto ya usa pytest y uv; un solo
  ejecutor y un solo lenguaje para toda la QA.
- **Fuera de la CI:** depende de que el despliegue esté arriba; meterla en la CI haría fallar PRs por
  causas ajenas al cambio.

## Riesgos
- Un recurso de terceros (fuente o analítica) que falle haría fallar el recorrido aunque la app esté
  bien: el mensaje de la prueba nombra la URL para decidir si se ignora.
