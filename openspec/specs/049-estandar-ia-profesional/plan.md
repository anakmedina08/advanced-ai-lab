# Plan · SPEC-049 · Skill de estándar profesional y auditor de madurez

## Diseño
Skill de solo instrucciones (rúbrica en `references/rubrica.md`) y auditor como código del proyecto con pruebas propias. La skill nunca ejecuta el auditor por su cuenta: si el proyecto lo tiene, lo usa con `make madurez`.

## Decisiones
- Sin scripts dentro de la skill: el agente audita con sus propias herramientas y la CI depende del código del proyecto, no de la carpeta de la skill.
- La lectura de anuncios va en otra skill, porque lee un correo personal y es propia del curso; así la de buenas prácticas se puede compartir.
- Mínimo inicial de 60 % para no romper la CI (era 65; bajó al endurecer G4, M10 y K4 por la revisión de GGA); se sube al cerrar cada oleada.

## Contrato
`make madurez MINIMO=<0-100>` · `scripts/auditar_madurez.py --path . [--json] [--salida archivo] [--minimo N]`.

## Riesgos
- Falsos positivos o negativos de verificaciones basadas en texto: cada verificación tiene su prueba y la revisión humana juzga el contenido.

## Alternativas descartadas
- Copiar el patrón de `jan-project-standard` con un script dentro de la skill: el equipo lo descartó para mantener la skill limpia.

## Estrategia de pruebas
Pruebas AAA del auditor con repos temporales (vacío, secretos, cobertura, carpetas ignoradas, anuncios y herramientas prohibidas, ramas y entornos); `make skills` valida el frontmatter.
