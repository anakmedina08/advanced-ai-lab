# Política de seguridad

## Versiones soportadas

Solo la última versión de `main` recibe correcciones de seguridad. Es un proyecto académico de la
Maestría en IA y Ciencia de Datos (UAO), no un servicio oficial de Seguros Bolívar.

## Cómo reportar una vulnerabilidad

**No abras un issue público.** Usa *Security → Report a vulnerability* en GitHub, que crea un
reporte privado. Incluye:

- el componente afectado (API, frontend, agente, pipeline de datos, workflows);
- los pasos para reproducirlo;
- el impacto que estimas.

Respondemos en un máximo de 5 días hábiles.

## Alcance

- **Dentro:**
  - el código de este repositorio;
  - sus workflows de GitHub Actions;
  - la imagen Docker;
  - el manejo de datos (Ley 1581 de 2012).
- **Fuera:**
  - servicios de terceros (proveedores de LLM, hosting);
  - el sitio público de Seguros Bolívar, del que solo se leen páginas públicas respetando robots.txt.

## Controles del proyecto

| Control | Dónde |
|---|---|
| Secretos solo en `.env` (ignorado) o en los secretos de GitHub | `.gitignore`, `.env.example` |
| Escaneo de secretos en cada commit y en la CI | gitleaks (SPEC-053) |
| Vulnerabilidades en dependencias, análisis estático y SBOM | pip-audit, CodeQL y CycloneDX (SPEC-054) |
| Revisión obligatoria del otro integrante | [`.github/CODEOWNERS`](.github/CODEOWNERS) |
| El agente de desarrollo no lee `.env` ni `data/`; push y merge requieren aprobación | `.claude/settings.json` (ADR-023) |
| Blindaje del RAG contra inyección indirecta | `src/sb_asistente/model/rag/blindaje.py` |

Si se filtra una llave: se **rota primero** en el proveedor y después se limpia el historial.
