# ADR-032 · El asistente por WhatsApp con la Cloud API de Meta, con firma y códigos de acceso

- **Fecha:** 2026-11-19
- **Categoría:** producto · integración · seguridad · costos
- **What:** un número propio del equipo atiende por WhatsApp con el mismo agente de la página
  (todas las aseguradoras, identificar la aseguradora, canales). El webhook vive en la API
  (`/whatsapp/webhook`) y responde por la Graph API.
- **Why:**
  - **Cloud API oficial** y no automatizar WhatsApp Web ni bots de terceros: es lo permitido por
    Meta, no exige un celular encendido y no arriesga el bloqueo del número.
  - **Firma de Meta obligatoria:** el endpoint es público; sin `X-Hub-Signature-256` válida
    cualquiera podría hacer hablar al agente y gastar tokens.
  - **Códigos de acceso (ADR-031) también aquí:** el número es público; la persona envía su código
    una vez y queda vinculado a su número (en hash) hasta que venza o se agote.
  - **200 inmediato y respuesta en segundo plano:** Meta reintenta si tarda; además se recuerdan
    los ids ya atendidos para no responder dos veces.
  - **Sin el número en claro:** conversación, perfil y vínculo usan `wa-<hash>` (Ley 1581).
- **Alternativas descartadas:**
  - WhatsApp Web automatizado: contra los términos de WhatsApp y frágil.
  - Proveedor intermediario (Twilio, Infobip): más costo y otra dependencia para un proyecto académico.
- **Where:**
  - `src/sb_asistente/model/whatsapp.py`, `model/acceso.py` (vínculos) y `controller/whatsapp.py`
  - `view/api.py` (`GET`/`POST /whatsapp/webhook`), `view/dependencias.py` (`get_whatsapp`)
  - `make tunel`, `.env.example` y pruebas en `tests/test_whatsapp.py`
- **Learned:**
  - Mientras la app no esté publicada en Meta, el webhook solo recibe eventos de prueba del panel.
