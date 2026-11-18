# Plan · SPEC-053 · Escaneo de secretos con gitleaks en cada commit y en la CI

## Diseño
gitleaks en dos capas: hook local (rápido, solo staging) y workflow (historial completo, no se puede saltar con `--no-verify`).

## Decisiones
- Versión fijada (v8.24.0) en pre-commit para reproducibilidad.
- El workflow vive en `seguridad.yml`, que en SPEC-054 suma pip-audit, CodeQL y SBOM.

## Contrato
`make secretos` · job `secretos` en `.github/workflows/seguridad.yml`.

## Riesgos
- Falsos positivos en fixtures: se agregan a `.gitleaksignore` con el fingerprint, revisado en el PR.

## Alternativas descartadas
- detect-secrets: requiere mantener un baseline y es más lento.
- trufflehog: más pesado para un repo de este tamaño.

## Estrategia de pruebas
Verificación manual con un archivo de prueba con una llave falsa (no se versiona) y escaneo del historial completo.
