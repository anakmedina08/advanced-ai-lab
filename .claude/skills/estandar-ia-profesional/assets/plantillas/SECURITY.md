# Política de seguridad

## Versiones soportadas
Solo la última versión publicada en `main` recibe correcciones de seguridad.

## Cómo reportar una vulnerabilidad
**No abras un issue público.** Usa *Security → Report a vulnerability* en GitHub
(reporte privado) o escribe a los mantenedores listados en `.github/CODEOWNERS`.

Incluye:
- qué componente está afectado;
- cómo reproducirlo;
- el impacto que estimas.

Respondemos en un máximo de 5 días hábiles.

## Alcance
- Código de este repositorio, sus workflows y su imagen Docker.
- **Fuera de alcance:** servicios de terceros (proveedores de LLM, hosting) y datos públicos indexados.

## Buenas prácticas del proyecto
- Los secretos solo viven en `.env` (ignorado) o en los secretos de GitHub.
- Hay escaneo de secretos (gitleaks), auditoría de dependencias (pip-audit) y CodeQL en cada PR.
- Si se filtra una llave, se rota primero y después se limpia el historial.
