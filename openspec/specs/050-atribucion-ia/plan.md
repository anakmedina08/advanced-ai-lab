# Plan · SPEC-050 · Commits y PRs a nombre de las personas, sin coautor de IA

## Diseño
Dos capas: configuración del agente (`attribution`) y red de seguridad local (hook `commit-msg`) que no depende de la versión del agente.

## Decisiones
- Borrar en el hook, no rechazar: el commit no se interrumpe y el resultado es el mismo.
- El uso de IA se declara en la política de uso de IA (SPEC-056) y en el README, no en cada commit.

## Contrato
Hook `limpiar-trailers-ia` (stage `commit-msg`) → `scripts/limpiar_trailers_ia.py <archivo>`.

## Riesgos
- Los commits hechos desde la web de GitHub no pasan por el hook: se revisan en el PR.

## Alternativas descartadas
- Rechazar el commit con error: obliga a reescribir el mensaje a mano sin aportar nada.
- Reescribir ya el historial: rompe clones y firmas; se deja como decisión aparte.

## Estrategia de pruebas
Pruebas AAA del filtro: quita coautor y sesión, respeta coautores humanos, es idempotente.
