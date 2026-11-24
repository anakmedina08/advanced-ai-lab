# SPEC-073 · El asistente en un número propio de WhatsApp (Cloud API de Meta)

> Curso: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **5** · Responsable: Daniel Silva · Depende de SPEC-071 y SPEC-072 · Plan en
> [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-032](../../../docs/decisiones/ADR-032-whatsapp-cloud-api.md).

## Problema
El asistente solo vive en la página. Mucha gente resuelve sus trámites por WhatsApp, y el equipo
ya tiene un número propio (SIM nueva) registrado en la WhatsApp Cloud API de Meta.

## Historia
**Como** persona con un seguro, **quiero** escribirle al asistente por WhatsApp **para** saber qué
cubre mi seguro, con qué aseguradora estoy y a qué canal oficial llamar, sin entrar a la página.

## Requisitos
- **R073.1** `GET /whatsapp/webhook` DEBE devolver `hub.challenge` solo si `hub.mode=subscribe` y
  `hub.verify_token` coincide con `WHATSAPP_VERIFY_TOKEN` (comparación en tiempo constante).
- **R073.2** `POST /whatsapp/webhook` DEBE rechazar (403) todo evento sin `X-Hub-Signature-256`
  válida (HMAC-SHA256 con `WHATSAPP_APP_SECRET`) y responder 200 de inmediato; la respuesta del
  agente sale en segundo plano por la Graph API.
- **R073.3** Con `WHATSAPP_EXIGE_CODIGO=1` (por defecto), el LLM solo responde si el número activó
  un código de acceso (SPEC-072) enviándolo en un mensaje; cada respuesta gasta un mensaje del cupo
  ANTES de llamar al modelo.
- **R073.4** El número de la persona NO DEBE guardarse en claro: conversación, perfil y vínculo
  con el código usan su hash (`canal_de`). No se registra el texto ni el número en logs.
- **R073.5** Un mismo mensaje (Meta reintenta) NO DEBE responderse dos veces.
- **R073.6** «olvidar» DEBE borrar la conversación y el vínculo con el código del número.
- **R073.7** Credenciales solo en `.env`; sin ellas el webhook responde 503.
- **R073.8** A un número sin código vigente (texto, audio o un código inválido) se le explica cómo
  pedirlo UNA vez cada `WHATSAPP_AVISO_HORAS` (24 por defecto); los demás mensajes no se responden,
  porque Meta cobra cada mensaje de servicio desde octubre de 2026.

## Criterios de aceptación
- **AC1** · **Dado** el token correcto, **cuando** Meta verifica, **entonces** recibe el reto.
- **AC2** · **Dado** un número sin código, **cuando** escribe, **entonces** recibe cómo pedirlo y el
  LLM no se llama.
- **AC3** · **Dado** un código de 2 mensajes activado, **cuando** escribe 3 preguntas, **entonces**
  la tercera recibe «ya usó todos sus mensajes».
- **AC4** · **Dado** un evento sin firma, **cuando** llega, **entonces** 403 y no se responde.

## Fuera de alcance
- Plantillas para iniciar conversaciones (requieren método de pago en Meta).
- Imágenes y audios por WhatsApp (se responde que por ahora solo texto).
- Publicar la app y verificar el negocio en Meta (lo hace el equipo en el panel).
