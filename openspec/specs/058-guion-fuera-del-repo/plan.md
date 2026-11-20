# Plan · SPEC-058 · Guion de las sustentaciones fuera del repositorio público

## Diseño
`git rm --cached` + `.gitignore`.

## Decisiones
- El archivo sigue en commits anteriores; se documenta como limitación.

## Contrato
—

## Riesgos
- Quien clone de cero ya no tendrá el guion: se comparte por fuera del repo.

## Alternativas descartadas
- Mover el guion a otra carpeta del repo: seguiría siendo público.

## Estrategia de pruebas
`git ls-files` y revisión de enlaces.
