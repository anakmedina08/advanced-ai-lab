---
name: identificar-aseguradora
description: Averigua con qué aseguradora está la persona cuando no lo sabe (recibo, débito, correo, app o documento) y la lleva al canal oficial de esa aseguradora. Úsala cuando cuente un caso que depende de su póliza o pregunte a quién llamar.
license: MIT
metadata:
  uso: asistente
  autor: equipo-sb-asistente
---

## Qué hace
- Si la persona ya dijo su aseguradora, no pregunta de nuevo: usa `canales_aseguradora` con el servicio de su caso.
- Si no la dijo, pregunta una sola vez: «¿Con qué aseguradora tienes ese seguro?».
- Si no sabe, pide pistas en una lista corta: dónde lo paga, qué nombre sale en el recibo o en el débito del extracto, de qué dominio le llegan los correos (por ejemplo «mapfre.com.co»), qué app usa, en qué banco, concesionario o empresa lo obtuvo.
- Con las pistas usa `identificar_aseguradora`. Con confianza alta o media, confirma el nombre con la persona y sigue; con baja o ninguna, muestra las candidatas y pregunta.
- Si sigue sin saberlo, le dice que puede subir el recibo o la carátula en la página: se lee en memoria y solo se usa el nombre de la aseguradora.

## Reglas
- Nunca pide cédula, número de póliza ni correo completo; si los escribe, le pide quitarlos.
- No dice que la póliza cubre el caso: eso solo lo confirma su aseguradora.
- Cierra con el canal de SU aseguradora, no con el de Seguros Bolívar por defecto.
