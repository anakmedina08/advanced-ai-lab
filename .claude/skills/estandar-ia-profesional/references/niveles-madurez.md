# Modelo de madurez — rúbrica

Cada dimensión tiene verificaciones con un **peso**:

- **3 = control crítico**: sin él hay riesgo real.
- **2 = práctica profesional esperada.**
- **1 = excelencia.**

El porcentaje de una dimensión es la suma de pesos cumplidos sobre la suma de pesos posibles. El
global pondera todas las verificaciones juntas.

| Nivel | Rango | Significado |
|---|---|---|
| **N1 Inicial** | < 40 % | Funciona en la máquina de alguien. Los controles dependen de la memoria de las personas. |
| **N2 Gestionado** | 40-69 % | Hay herramientas, pero no todas son obligatorias ni corren en CI. |
| **N3 Definido** | 70-89 % | Los controles están automatizados y documentados; un tercero puede operar el proyecto. |
| **N4 Optimizado** | ≥ 90 % | Hay puertas que impiden retroceder (madurez, evals, cobertura) y se mide la mejora en el tiempo. |

## Cómo leer el informe

- **Una dimensión en N1 bloquea el nivel global.** Aunque el promedio sea alto, se atiende primero.
- **Brechas de peso 3:** van en la oleada 1, sin discusión.
- **Un ✅ no significa "bien hecho", sino "existe y se puede verificar".** La revisión humana del PR
  juzga la calidad del contenido.

## Objetivos sugeridos

| Contexto | Objetivo |
|---|---|
| Proyecto de curso o prototipo | N2 en todas las dimensiones, N3 global |
| Proyecto para sustentación de maestría o portafolio | N3 en todas las dimensiones |
| Producto en producción con datos de clientes | N4 en seguridad, IA/ML y gobernanza; N3 en el resto |

## Extender la rúbrica

Para agregar una verificación, se añade una fila en `rubrica.md` con:
- ID libre (por ejemplo `S10`);
- peso;
- qué se verifica;
- **dónde mirar y qué cuenta como ✅**, comprobable solo leyendo archivos.

Después se explica la verificación en la guía de su dimensión. Si el proyecto tiene su propio
auditor (`make madurez`), se actualiza también ahí, en un PR del proyecto.
