# Problemas seleccionados 3

## Criterios de selección

- Fuente: `leetcodedataset/data_hf/problems_after_reference_estimated.json`, con fechas estimadas del 2024-08-11 al 2025-03-30 (posteriores al 2024-08-06).
- Cada problema incluido tiene solución de referencia y 12 pruebas funcionales únicas interpretables como aserciones Python.
- Cada problema tiene un ejemplo few-shot propio, basado en un problema distinto y algorítmicamente relacionado. Incluye una entrada/salida del problema de referencia y su solución completa.
- Las relaciones se seleccionaron por conceptos algorítmicos, estructura de los problemas, etiquetas y similitud de enunciados; las relaciones menos obvias fueron especificadas individualmente. No se reutiliza el ejemplo genérico LC-121 como demostración común.

## Conteo

- Problemas que ya estaban en `problemas_seleccionados2`: 30.
- Problemas nuevos convertidos: 186.
- Total en cada una de las carpetas seleccionadas: 216.
- Problemas de la fuente no convertidos: 9.

## No convertidos

| Código | Problema | Motivo |
|---|---|---|
| LC-3266 | Final Array State After K Multiplication Operations II | Solo 2 pruebas únicas con entradas y salidas interpretables; mínimo 10. |
| LC-3376 | Minimum Time to Break Locks I | No tiene solución de referencia en la fuente. |
| LC-3380 | Maximum Area Rectangle With Point Constraints I | No tiene solución de referencia en la fuente. |
| LC-3382 | Maximum Area Rectangle With Point Constraints II | No tiene solución de referencia en la fuente. |
| LC-3387 | Maximize Amount After Two Days of Conversions | Solo 9 pruebas únicas con entradas y salidas interpretables; mínimo 10. |
| LC-3405 | Count the Number of Arrays with K Matching Adjacent Elements | Solo 1 prueba única con entradas y salidas interpretables; mínimo 10. |
| LC-3410 | Maximize Subarray Sum After Removing All Occurrences of One Element | No tiene solución de referencia en la fuente. |
| LC-3437 | Permutations III | Solo 8 pruebas únicas con entradas y salidas interpretables; mínimo 10. |
| LC-3454 | Separate Squares II | No tiene solución de referencia en la fuente. |

## Orden lógico para `problemas_seleccionados3`

Primero se incorporan los 30 JSON preexistentes de `problemas_seleccionados2`; después, los 186 JSON nuevos. El sistema de archivos no garantiza orden de listado, por lo que este README documenta el orden de incorporación.
