# Plan · SPEC-054 · Auditoría de dependencias, CodeQL y SBOM

## Diseño
Workflow nuevo `dependencias.yml` con tres jobs (dependencias, codeql, sbom), independiente del de secretos. La lista de aceptadas es un archivo de texto revisable en PR.

## Decisiones
- opentelemetry-api 1.45.1 → 1.45.2 y soupsieve 3.0.4 → 4.0.0 (corrigen CVE-2026-126360 y CVE-2026-126190).
- Los 4 avisos de chromadb 1.5.9 no tienen versión corregida y afectan al **modo servidor** (API HTTP, autenticación y RBAC). El proyecto usa Chroma embebido (`PersistentClient`) sin servidor: se aceptan con fecha de revisión del 15/12/2026.

## Contrato
`make auditar-deps` · jobs `dependencias`, `codeql` y `sbom` en `.github/workflows/dependencias.yml` · `seguridad/vulnerabilidades-aceptadas.txt`.

## Riesgos
- Que una CVE nueva rompa la CI sin cambios propios: es el comportamiento buscado; se corrige o se acepta en un PR.

## Alternativas descartadas
- `safety`: requiere cuenta para la base completa.
- Ignorar los avisos sin documentarlos: no deja trazabilidad.

## Estrategia de pruebas
`make auditar-deps` local y suite completa después de actualizar el lock.
