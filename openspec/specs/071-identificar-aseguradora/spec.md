# SPEC-071 · Identificar la aseguradora de la persona y agente con todas las aseguradoras

> Curso: Técnicas Avanzadas de IA (551462) y Gestión de Proyectos en IA y CD (551475) ·
> Story points: **5** · Responsable: Daniel Silva · Depende de SPEC-069 y SPEC-070 · Plan en
> [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md). Decisión:
> [ADR-030](../../../docs/decisiones/ADR-030-identificar-aseguradora.md).

## Problema
El agente responde solo con el corpus de Seguros Bolívar y cierra con «consulte los canales de
Seguros Bolívar» aunque la persona esté asegurada en otra compañía. Además, muchas personas no
saben con qué aseguradora tienen su seguro (lo compraron en el banco, se lo dio la empresa, lo
paga un débito automático) y no hay una fuente pública que lo diga: no existe una API de pólizas
ni un MCP de las aseguradoras, y el asistente no pide cédula ni número de póliza.

## Historia
**Como** persona con un seguro de cualquier tipo (no solo SOAT), **quiero** que el asistente
averigüe con qué aseguradora estoy a partir de lo que tengo a mano (el recibo de pago, la
carátula, el débito del extracto, el correo que me llega) **para** que me diga cómo proceder con
esa aseguradora y me lleve a su canal oficial.

## Requisitos
- **R071.1** `mercado.identificar(pistas)` DEBE cruzar lo que escribió la persona con el registro
  (nombre, alias y dominio del sitio oficial) y devolver la aseguradora, la confianza (alta,
  media, baja o ninguna), el servicio que sugiere el texto y las candidatas con la señal que
  coincidió. Con dos candidatas empatadas, o ninguna, NO DEBE elegir.
- **R071.2** `POST /aseguradoras/identificar` DEBE leer un recibo, carátula, extracto o
  certificado (JPG, PNG o PDF, máx. 8 MB) en memoria, con OCR local (Tesseract) o el texto del
  PDF, sin LLM ni tokens, y devolver lo mismo que R071.1 más `leido`.
- **R071.3** El texto leído o escrito NUNCA DEBE salir del módulo: ni en la respuesta, ni en disco,
  ni en logs. Solo salen datos del registro (Ley 1581).
- **R071.4** En un documento, un alias de una palabra que también es un lugar («Bolívar»: avenida,
  departamento, localidad) NO DEBE contar; sí la frase completa («Seguros Bolívar»).
- **R071.5** El agente DEBE tener las tools `comparar_aseguradoras`, `identificar_aseguradora` y
  `canales_aseguradora` en la ruta `rag`; el prompt deja de ser solo de Seguros Bolívar, pregunta
  la aseguradora cuando el caso depende de la póliza, nunca la adivina y remite a los canales de
  SU aseguradora. Las URLs de esas tools cuentan como fuentes válidas y los pasajes de otras
  aseguradoras pasan por el mismo blindaje (datos pasivos, con su aseguradora).
- **R071.6** La salida del agente DEBE incluir `aseguradora` (id del registro) cuando la sabe.
- **R071.7** La skill `identificar-aseguradora` DEBE guiar las preguntas (dónde paga, qué dice el
  recibo o el débito, de qué dominio llegan los correos, qué app usa, dónde lo compró) y ofrecer
  subir el documento cuando la persona no sepa.
- **R071.8** Sin Tesseract el servicio DEBE responder 503 con un mensaje claro (pedir las pistas).

## Criterios de aceptación
- **AC1** · **Dado** un recibo con «MAPFRE SEGUROS GENERALES» y `www.mapfre.com.co`, **cuando** se
  sube, **entonces** la respuesta es `mapfre` con confianza alta y no trae la cédula ni la póliza.
- **AC2** · **Dado** un recibo con «Av. Simón Bolívar», **cuando** se lee, **entonces** Seguros
  Bolívar no es candidata.
- **AC3** · **Dado** «no sé si es SURA o MAPFRE», **cuando** se identifica, **entonces** la confianza
  es baja y no hay aseguradora elegida.
- **AC4** · **Dado** «tuve una fuga en la tubería y tengo el hogar con MAPFRE», **cuando** responde el
  agente, **entonces** usa `canales_aseguradora` de MAPFRE y no remite a Seguros Bolívar.
- **AC5** · **Dado** un `.txt`, **cuando** se sube, **entonces** la API responde 422.

## Fuera de alcance
- Verificar la póliza con la aseguradora o con el RUNT (requieren datos personales y captcha).
- Guardar el documento o mostrarlo a un administrador.
- La interfaz de yellowdata (va en su repositorio).

## Métricas de éxito
- 100 % de los casos del banco de pruebas sin datos personales en la respuesta.
- La aseguradora correcta en los recibos de prueba con nombre o dominio legibles.
