# SPEC-011 · Herramienta determinista sobre los CSV con @tool y Pydantic

> Curso: Técnicas M2 (2.1) · Story points: **5** · Responsable: Katherine ·
> Plan en [`plan.md`](plan.md); tareas en [`tasks.md`](tasks.md).

## Problema
El agente no tiene una herramienta para preguntas numéricas: si alguien pregunta cuántas pólizas se vendieron en un trimestre, el LLM inventaría la cifra.

## Historia
**Como** analista que consulta la cartera sintética, **quiero** preguntar cifras («¿cuántas pólizas se vendieron en el tercer trimestre de 2025?») y recibir el dato exacto, **para** confiar en que el número sale de los datos y no de la imaginación del modelo.

## Requisitos
- **R011.1** `model/datos.py` DEBE calcular métricas (`polizas_vendidas`, `primas_mensuales_cop`, `siniestros`, `monto_siniestros_cop`, `clientes`) sobre los CSV sintéticos con pandas, sin LLM.
- **R011.2** La consulta DEBE validarse con `ConsultaDatos` (Pydantic): métrica, año, trimestre (1–4), producto, línea, canal y `agrupar_por`.
- **R011.3** La tool `consultar_datos` DEBE exponerse con `@tool` y `args_schema=ConsultaDatos` y devolver JSON con el valor, la unidad, los filtros aplicados, las filas usadas y la fuente.
- **R011.4** Un filtro desconocido (producto que no existe) DEBE devolver un error explicativo con los valores válidos, no un cero.

## Criterios de aceptación
- **AC1** · **Dado** los datos sintéticos generados, **cuando** se consulta `polizas_vendidas` de 2025 trimestre 3, **entonces** el valor es igual al conteo hecho a mano con pandas.
- **AC2** · **Dado** un trimestre 5, **cuando** se valida la consulta, **entonces** Pydantic la rechaza.
- **AC3** · **Dado** el producto «Seguro lunar», **cuando** se consulta, **entonces** la tool responde con los productos válidos.

## Fuera de alcance
Consultas SQL libres generadas por el LLM (riesgo de inyección).

## Métricas de éxito
Exactitud 100 % frente al cálculo con pandas en las pruebas.
