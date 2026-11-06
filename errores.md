# Resumen de errores del experimento 3

## Alcance

Resumen consultado directamente de la base `investigacionv3`, con corte al 4 de noviembre de 2026. Se encontraron 360 ejecuciones: 90 por cada técnica de prompting, para 30 problemas y 3 repeticiones por combinación de problema y técnica.

## Resultado general

| Indicador | Resultado |
|---|---:|
| Ejecuciones registradas como completadas, con código generado | 360 |
| Código parseable | 360 (100 %) |
| Ejecuciones con validación inválida | 214 (59,4 %) |
| Ejecuciones con validación válida | 146 (40,6 %) |
| Ejecuciones de generación registradas como fallidas | 0 |

Por tanto, los registros no indican que el modelo dejara de generar código o que este tuviera errores de sintaxis. Los fallos aparecen durante la ejecución de las pruebas o al comparar los resultados con lo esperado.

## Errores funcionales más frecuentes

Se registraron 4.320 resultados de prueba: 2.920 aprobados y 1.400 no aprobados.

| Tipo | Registros | Ejecuciones afectadas | Detalle |
|---|---:|---:|---|
| Aserciones fallidas | 1.224 | 199 | El resultado no coincidió con la aserción (`AssertionError`). |
| Límites de tiempo | 144 | 12 | El proceso aislado superó el límite de 5 segundos. |
| Excepciones en ejecución | 32 | 4 | Errores `TypeError`, `IndexError`, `KeyError` y `AttributeError`. |

Los conteos de ejecuciones afectadas pueden superponerse: una ejecución puede incluir tanto aserciones fallidas como excepciones.

### Excepciones y timeouts identificados

| Problema | Técnica y repetición | Error registrado |
|---|---|---|
| LC-3474 — Lexicographically Smallest Generated String | Role prompting, repetición 2 | `TypeError: ord() expected a character, but string of length 0 found` (5 pruebas) |
| LC-3485 — Longest Common Prefix of K Strings After Removal | Role prompting, repetición 1 | `IndexError: list index out of range` (5 pruebas) |
| LC-3486 — Longest Special Path II | Chain-of-Thought, repetición 2 | `KeyError: 0` (1), `KeyError: 1` (7) y `KeyError: 2` (2) |
| LC-3503 — Longest Palindrome After Substring Concatenation I | Role prompting, repetición 3 | `AttributeError`: el objeto `Solution` no tiene el atributo `_getPalindromeLengths` (12 pruebas) |
| LC-3490 — Count Beautiful Numbers | Zero-shot, Chain-of-Thought y Role prompting; 3 repeticiones cada una | Timeout en las 12 pruebas de cada ejecución (9 ejecuciones) |
| LC-3495 — Minimum Operations to Make Array Elements Zero | Few-shot, 3 repeticiones | Timeout en las 12 pruebas de cada ejecución (3 ejecuciones) |

## Problemas sin ejecuciones válidas

En estos 15 problemas, las 12 ejecuciones (4 técnicas × 3 repeticiones) quedaron marcadas como inválidas:

- LC-3473 — Sum of K Subarrays With Length at Least M
- LC-3474 — Lexicographically Smallest Generated String
- LC-3476 — Maximize Profit from Task Assignment
- LC-3485 — Longest Common Prefix of K Strings After Removal
- LC-3486 — Longest Special Path II
- LC-3487 — Maximum Unique Subarray Sum After Deletion
- LC-3489 — Zero Array Transformation IV
- LC-3494 — Find the Minimum Amount of Time to Brew Potions
- LC-3495 — Minimum Operations to Make Array Elements Zero
- LC-3499 — Maximize Active Section with Trade I
- LC-3500 — Minimum Cost to Divide Array Into Subarrays
- LC-3501 — Maximize Active Section with Trade II
- LC-3503 — Longest Palindrome After Substring Concatenation I
- LC-3504 — Longest Palindrome After Substring Concatenation II
- LC-3505 — Minimum Operations to Make Elements Within K Subarrays Equal

## Resultados por técnica

| Técnica | Ejecuciones inválidas | Porcentaje inválido |
|---|---:|---:|
| Role prompting | 56 de 90 | 62,2 % |
| Chain-of-Thought | 55 de 90 | 61,1 % |
| Zero-shot | 54 de 90 | 60,0 % |
| Few-shot | 49 de 90 | 54,4 % |

Estos porcentajes describen los registros de este experimento; por sí solos no demuestran que la técnica haya causado los errores.

## Limitación de los datos guardados

Para las pruebas fallidas, la base contiene el mensaje genérico `AssertionError:`, pero no guarda el traceback, la entrada utilizada ni las salidas esperada y obtenida. Por ello, no es posible determinar desde estos registros qué caso límite o diferencia concreta produjo cada aserción fallida. Las excepciones y los timeouts sí conservan un mensaje, pero tampoco incluyen traceback.

Como dato complementario, el benchmark registró 4.680 corridas; 1.404 marcaron el resultado como incorrecto, repartidas en 108 ejecuciones, y no hubo timeouts en esas corridas.
