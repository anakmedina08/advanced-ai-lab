# Runbook de operación

## 1. Levantar todo
```bash
make dev        # primera vez
make api        # API en :8000
make frontend   # interfaz en :5173
```

## 2. ¿Está sano?
| Señal | Cómo verla | Esperado |
|---|---|---|
| API | `curl -s localhost:8000/health` | todos los componentes `true` |
| Trazas | proyecto de observabilidad | sin errores en la última hora |
| CI | pestaña Actions | verde en `develop` y `main` |

## 3. Fallos frecuentes
| Síntoma | Causa probable | Solución |
|---|---|---|
| `Address already in use` | proceso anterior vivo | `kill $(lsof -ti :PUERTO)` |
| 401 del LLM | llave vencida o ausente | revisar `.env` y rotar la llave |
| Respuestas sin contexto | índice vectorial vacío | `make index` |
| Tests que llaman a la red | falta un fake o un marcador | marcar `@pytest.mark.llm` |
| | | |

## 4. Rotar una llave
1. Revocarla en el proveedor.
2. Crear una nueva.
3. Actualizar `.env` local y los secretos de GitHub.
4. Verificar con `/health`.

## 5. Volver a una versión anterior
`git checkout vX.Y.Z && make docker-build`. Para modelos: mover el alias `@produccion` a la versión anterior en MLflow.

## 6. Escalamiento
| Tema | Responsable | Contacto |
|---|---|---|
