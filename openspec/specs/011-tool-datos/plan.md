# Plan · SPEC-011 · Herramienta determinista sobre los CSV con @tool y Pydantic

## Diseño
Función pura `consultar(tablas, consulta) → ResultadoDatos` + `crear_tool_datos(cargar)` con la carga inyectada (permite tablas pequeñas en las pruebas).

## Decisiones
- Métricas cerradas (Literal) en lugar de SQL libre: el modelo elige parámetros, el código calcula.
- Los datos son sintéticos (Ley 1581): la respuesta lo dice.

## Contrato
`ConsultaDatos{metrica, anio?, trimestre?, producto?, linea?, canal?, agrupar_por?}` → `ResultadoDatos{valor, unidad, filtros, filas, grupos?, fuente}`

## Riesgos
- Si faltan los CSV, la tool responde cómo generarlos (`uv run sb reco generar`).

## Alternativas descartadas
- Agente pandas de LangChain: ejecuta código generado, inseguro e indeterminista.

## Estrategia de pruebas
`tests/test_datos.py` con tablas de 6 filas: cada métrica, filtros, agrupación y errores. Pruebas AAA sin red ni API de pago.
