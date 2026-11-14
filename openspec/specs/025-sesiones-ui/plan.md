# Plan · SPEC-025 · Sesiones en el frontend: hilos, usuario y memoria visible

## Diseño
Hook `useSesiones` (localStorage con try/catch) y componente `BarraHilos`; ids con `crypto.randomUUID`.

## Decisiones
- Los ids viven en el navegador: no hay datos personales en el servidor más allá del perfil que el usuario dicta y puede borrar.

## Contrato
Usa los endpoints de la historia 020.

## Riesgos
- `localStorage` bloqueado (modo privado): la app sigue funcionando sin lista persistente.

## Alternativas descartadas
- Guardar la lista de hilos en el servidor: requiere autenticación.

## Estrategia de pruebas
Pruebas del hook con `localStorage` simulado. Pruebas AAA sin red ni API de pago.
