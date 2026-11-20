# ADR-027 · Auditoría de dependencias, CodeQL y SBOM en la CI

- **Fecha:** 2026-11-18
- **What:** `.github/workflows/dependencias.yml` corre tres controles. **pip-audit** revisa `uv.lock` contra
  vulnerabilidades conocidas (`make auditar-deps`, también local). **CodeQL** hace análisis estático de Python
  y TypeScript. En cada push a `main` se genera un **SBOM CycloneDX** (`sbom.json`) como artefacto.
- **Why:** Dependabot actualiza versiones, pero no bloquea un PR que introduce una dependencia vulnerable ni
  revisa el código propio. El módulo 4 de Gestión pide CI/CD con credenciales y seguridad, y el SBOM deja
  constancia de qué se entregó.
- **Decisiones de diseño:**
  - **Vulnerabilidades aceptadas con fecha:** `seguridad/vulnerabilidades-aceptadas.txt` lista cada ID con su
    motivo y su fecha de revisión. Hoy son las de chromadb en modo servidor, que el proyecto no usa. Agregar
    una requiere PR revisado.
  - **Versiones fijas** de pip-audit y cyclonedx-bom: una herramienta de seguridad no se actualiza sola.
  - **Permisos mínimos:** `contents: read`; solo CodeQL pide `security-events: write` para publicar hallazgos.
  - Se corre cada lunes, aunque no cambie el código, porque las CVE nuevas aparecen sin commits.
- **Where:** `.github/workflows/dependencias.yml`, `Makefile` (`auditar-deps`), `seguridad/`, SPEC-054.
- **Learned:** pip-audit sobre `uv export` (sin hashes ni el propio proyecto) evita instalar el entorno para
  auditarlo. Se actualizaron opentelemetry-api y soupsieve porque sí tenían versión corregida.
