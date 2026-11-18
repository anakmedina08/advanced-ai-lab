# CI/CD en GitHub e higiene de ramas

Complementa `entrega.md` (dimensión 4) y `proceso.md` (dimensión 6) con lo propio de GitHub:
qué ramas existen, qué corre en cada evento y cómo se publica.

## 1. Solo dos ramas permanentes (P9)

| Rama | Vida | Protección |
|---|---|---|
| `main` | permanente; solo releases | PR obligatorio, checks requeridos, sin force-push ni borrado |
| `develop` | permanente; integración | PR obligatorio, checks requeridos |
| `feature/*`, `fix/*`, `chore/*`, `docs/*`, `hotfix/*` | **efímeras**: se borran al fusionar | — |

Para que se mantenga solo y no dependa de la memoria de nadie:

1. **Ajuste del repo (lo hace el humano):** en *Settings → General → Pull Requests*, activar
   **Automatically delete head branches**.
2. **Red de seguridad en CI:** el workflow `ramas.yml` (plantilla en
   `assets/plantillas/workflows/ramas.yml`):
   - al cerrar un PR fusionado, borra su rama si no es `main` ni `develop`;
   - cada semana publica en el resumen del job las ramas viejas sin PR abierto;
   - **nunca borra una rama con PR abierto.**
3. **Limpieza inicial (una vez, el humano):** borrar las ramas remotas ya fusionadas:

   ```bash
   git fetch --prune
   # revisar primero la lista
   git branch -r --merged origin/develop | grep -vE 'origin/(main|develop|HEAD)'
   # borrar (después de revisar)
   git branch -r --merged origin/develop | grep -vE 'origin/(main|develop|HEAD)' \
     | sed 's#origin/##' | xargs -n1 git push origin --delete
   git fetch --prune && git branch -r   # debe quedar origin/main y origin/develop
   ```

   Las ramas locales se limpian con `git branch --merged develop | grep -vE '^\*|main|develop' | xargs git branch -d`.

**Verificación del agente:** `git ls-remote --heads origin` muestra solo `main`, `develop` y las
ramas con un PR abierto.

## 2. Qué corre en cada evento

| Evento | Workflow | Qué hace |
|---|---|---|
| PR a `develop`/`main` | `ci.yml` | lint, formato, tipos, pruebas con cobertura, build del frontend y Docker |
| PR / push / semanal | `seguridad.yml` | gitleaks, pip-audit, CodeQL |
| PR que toca prompts, RAG o agente | `evals.yml` | puerta de regresión del modelo (con aprobación, porque cuesta dinero) |
| PR cerrado / semanal | `ramas.yml` | higiene de ramas |
| push a `main` | `release.yml` | release-please: versión, CHANGELOG y tag |
| release publicado | `deploy.yml` | despliegue a producción con `environment: produccion` |

## 3. Entrega continua (R8)

- **Entornos de GitHub** (*Settings → Environments*):
  - `staging`: se despliega desde `develop` automáticamente;
  - `produccion`: se despliega desde un release y **requiere un revisor**.
- **Secretos por entorno**, nunca en el repo: llaves del LLM, tokens del canal (Telegram o WhatsApp) y del proveedor de hosting.
- **Despliegue reproducible:** la misma imagen Docker que pasó la CI se publica en GHCR (`ghcr.io/<owner>/<repo>:<versión>`) y se despliega por su etiqueta. No se reconstruye en el servidor.
- **Verificación después del despliegue:** `curl -f https://<host>/health` dentro del job; si falla, el job falla y no se anuncia.
- **Reversión:** volver a desplegar la etiqueta anterior. El Model Registry mueve el alias `@produccion` a la versión anterior.

```yaml
# extracto de deploy.yml
on:
  release: { types: [published] }
permissions: { contents: read, packages: write }
jobs:
  desplegar:
    runs-on: ubuntu-latest
    environment: produccion          # exige aprobación y aporta los secretos
    steps:
      - uses: actions/checkout@v4
      - run: echo "desplegar ghcr.io/${{ github.repository }}:${{ github.event.release.tag_name }}"
      - run: curl -fsS --retry 5 "${{ vars.URL_PRODUCCION }}/health"
```

## 4. Protección de ramas como checklist (la aplica el humano)

| Ajuste | `main` | `develop` |
|---|---|---|
| Require a pull request before merging | ✅ (1 aprobación) | ✅ (1 aprobación) |
| Require review from Code Owners | ✅ | ✅ |
| Require status checks: `quality`, `frontend`, `seguridad` | ✅ | ✅ |
| Require branches to be up to date | ✅ | — |
| Require conversation resolution | ✅ | ✅ |
| Block force pushes / deletions | ✅ | ✅ |

## 5. Anti-patrones

- Decenas de ramas fusionadas que nadie borra.
- Commits directos a `main` o `develop`.
- Checks que se pueden saltar ("Merge without waiting").
- Secretos como variables sin entorno.
- Despliegues que reconstruyen en el servidor una imagen distinta a la probada.
- Un `deploy` sin `/health` posterior.
