# Plan · SPEC-052 · Retirar Streamlit del proyecto

## Diseño
Borrado directo de la vista Streamlit; el modelo y el controlador no cambian porque la vista solo hablaba con ellos (MVC).

## Decisiones
- Se retira por completo (no queda como herramienta interna): la regla dice «en ninguna parte».
- Las specs y ADR históricos se conservan tal como se escribieron; ADR-024 deja constancia del cambio.

## Contrato
Sin cambios de API.

## Riesgos
- Alguna tarea interna solo existía en Streamlit: se verificó la paridad página por página con SPEC-046.

## Alternativas descartadas
- Mantenerla fuera del producto como herramienta interna: los dos anuncios la excluyen.

## Estrategia de pruebas
`make check` (sin las pruebas de AppTest), `npm test` del frontend y `make madurez` con K4.
