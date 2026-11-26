# USER.md — Quién opera a Yelo

> Contexto del dueño y del equipo. Le dice al agente para quién trabaja y bajo qué reglas.

## Equipo

| Campo | Valor |
|---|---|
| Producto | Asistente Seguros Bolívar (Yelo) |
| Autoría | Daniel Silva y Katherine Medina — UAO |
| Cursos | Técnicas Avanzadas de IA (551462, Grupo 10) y Gestión de Proyectos en IA y CD (551475, Grupo 5) |
| Repositorio | https://github.com/anakmedina08/advanced-ai-lab |
| Rama principal | `main` (estable); `develop` (integración); `feature/*` |

## Quién decide qué

- **Daniel Silva** es el revisor de código (Code Reviewer) y quien opera la infraestructura
  (Droplet, OpenClaw, CI/CD).
- **Katherine Medina** es dueña del repositorio de GitHub.
- Las decisiones técnicas se registran en **Engram** y se espejan en `docs/decisiones/` (ADR).

## Reglas que me aplican

- La autoría del repositorio es de las personas, no de la IA (ADR-023): ningún commit lleva
  coautor de IA.
- Ningún secreto (llaves, tokens, `.env`) entra al repositorio ni al chat.
- Todo cambio significativo actualiza `CONSTITUTION.md` y lleva su ADR en el mismo commit.
- La documentación de referencia vive en `AGENTS.md` (raíz) y `CONSTITUTION.md`.

## Estado operativo (noviembre 2026)

- **Canal en producción:** WhatsApp por **OpenClaw** (dispositivo vinculado por QR), en el Droplet.
- **Modelo:** DeepSeek como primario, con fallback.
- **Gateway:** contenedor `openclaw-gateway`, bind en loopback y token (`docs/openclaw.md`).
