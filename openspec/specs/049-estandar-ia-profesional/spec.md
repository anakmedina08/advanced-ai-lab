# SPEC-049 · Skill de estándar profesional y auditor de madurez

> Curso: Gestión M4 (CI/CD) y Técnicas M3 (gobernanza) · Story points: **5** · Responsable: Daniel ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
La skill del curso (`jan-project-standard`) deja la base del repo, pero no mide la madurez ni cubre seguridad, CI/CD en GitHub, IA/ML responsable ni gobernanza de agentes. Sin una medida, no sabemos qué mejorar primero ni si el proyecto retrocede.

## Historia
**Como** equipo, **quiero** una skill que audite el repositorio en 8 dimensiones con puntaje y un auditor propio en la CI, **para** priorizar mejoras y evitar que la calidad baje.

## Requisitos
- **R049.1** `.claude/skills/estandar-ia-profesional/` DEBE contener solo instrucciones, rúbrica y plantillas (sin scripts propios que ejecute la skill).
- **R049.2** `.claude/skills/seguimiento-anuncios-curso/` DEBE describir la lectura de anuncios del curso en solo lectura y sin copiar datos sensibles.
- **R049.3** `scripts/auditar_madurez.py` DEBE implementar las 70 verificaciones (66 de la rúbrica + K1-K4) leyendo solo archivos, sin red ni ejecución del proyecto.
- **R049.4** `make madurez [MINIMO=N]` DEBE imprimir el informe y salir con código 1 si el puntaje global es menor que N.
- **R049.5** La CI DEBE ejecutar el auditor con un mínimo que impida retroceder.
- **R049.6** `docs/madurez.md` DEBE versionar el informe de la fecha.

## Criterios de aceptación
- **AC1** · **Dado** el repositorio, **cuando** se ejecuta `make madurez`, **entonces** se imprime el puntaje global, el nivel por dimensión y las brechas ordenadas por peso.
- **AC2** · **Dado** un puntaje menor que el mínimo, **cuando** corre la CI, **entonces** el job falla.
- **AC3** · **Dado** `make skills`, **cuando** se listan las skills, **entonces** las dos nuevas aparecen como válidas.

## Fuera de alcance
Cerrar las brechas que reporta el auditor (cada una tiene su propia spec).

## Métricas de éxito
Auditor en la CI con mínimo 60 % (sube con cada oleada); 7 skills válidas.
