# 3 · Seguridad y cadena de suministro

## S1 · SECURITY.md
Copiar `assets/plantillas/SECURITY.md`. Indica cómo reportar una vulnerabilidad sin abrir un issue público.
En GitHub se activa *Settings → Security → Private vulnerability reporting*.

## S2 · Secretos fuera del repo
- `.gitignore`: `.env`, `.env.*`, `!.env.example`, `*.pem` y `*.key`.
- `.env.example` lista **todas** las variables con valores ficticios y un comentario.
- La configuración se lee con `pydantic-settings`, con tipos y validación al arrancar.

## S3 · Escaneo de secretos (gitleaks)
Fusionar `assets/plantillas/pre-commit-extra.yaml`:
```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.24.0
  hooks: [{id: gitleaks}]
```
Para revisar **todo el historial** una vez: `gitleaks detect --source . --log-opts="--all"`.
Si aparece un secreto real, se **rota primero** y después se limpia el historial.

## S4 · Dependabot
Usar `package-ecosystem: uv` (o `pip`), `github-actions` y `npm` si hay frontend.
Se agrupan los minor y patch y se apunta a la rama de integración (`develop`).

## S5 · Auditoría de vulnerabilidades
`assets/plantillas/workflows/seguridad.yml` corre `pip-audit` sobre las dependencias exportadas del lock:
```bash
uv export --frozen --no-hashes > /tmp/req.txt && uvx pip-audit -r /tmp/req.txt --strict
```
Corre en cada PR y cada semana (`schedule`), porque las CVE aparecen sin que cambie el código.

## S6 · Análisis estático
- CodeQL (Python + JavaScript) en `seguridad.yml`; gratis en repos públicos.
- Alternativa liviana: agregar `"S"` (flake8-bandit) al `select` de Ruff e ignorar `S101` en `tests/`.

## S7 · CODEOWNERS
Asigna revisores por ruta. Combinado con la protección de rama ("Require review from Code
Owners"), ningún cambio en `src/`, `.github/` o `.claude/` entra sin aprobación de un dueño.

## S8 · Permisos mínimos en workflows
Al inicio de cada workflow:
```yaml
permissions:
  contents: read
```
Se amplían solo en el job que lo necesite (`pull-requests: write`, `security-events: write`).
Las acciones de terceros se fijan por SHA cuando el repo maneja secretos.

## S9 · SBOM
En el release: `uvx cyclonedx-py environment -o sbom.json`, adjunto al GitHub Release.
Permite responder a la pregunta "¿usamos la librería X en la versión Y?" sin abrir el código.

## Protección de ramas (manual, la hace el humano)
Para `main` y `develop`:
- PR obligatorio con 1 aprobación y aprobación de Code Owners.
- Checks requeridos: `quality`, `seguridad` y `evals`.
- Commits firmados opcionales.
- Sin force-push.
