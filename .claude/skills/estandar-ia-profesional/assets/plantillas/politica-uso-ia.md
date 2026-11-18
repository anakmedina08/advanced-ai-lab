# Política de uso de IA en el proyecto

## 1. Herramientas autorizadas
| Herramienta | Uso | Quién |
|---|---|---|
| Claude Code / OpenCode | desarrollo asistido, revisión, documentación | equipo |
| LLM del producto (API) | respuestas del asistente | aplicación |

## 2. Qué puede hacer un agente
- Leer el código, proponer cambios, crear ramas y commits locales.
- Correr pruebas, linters y el auditor de madurez.

## 3. Qué NO puede hacer un agente
- Leer `.env`, secretos o `data/`.
- Hacer `git push`, fusionar PRs o cambiar la configuración de GitHub.
- Enviar datos personales a servicios externos.
- Publicar contenido o desplegar sin aprobación humana.

## 4. Revisión
- Todo cambio generado con IA pasa por un PR revisado por **una persona del equipo**.
- La persona que aprueba responde por el cambio como si lo hubiera escrito.

## 5. Atribución
- **Decisión del equipo (ver ADR-NNN):** los commits van a nombre de la persona y sin coautor de IA
  (`attribution` vacío y filtro `commit-msg`). El uso de IA se declara en esta política y en el README.
- En entregas académicas se incluye una sección "Uso de IA" que describe las herramientas y en qué partes se usaron.

## 6. Datos y privacidad
- Solo datos públicos (Ley 1581 de 2012). Sin PII en prompts, trazas ni conjuntos de evaluación.

## 7. Revisión de esta política
Se revisa al inicio de cada módulo o ante un incidente.
