# Análisis estadístico de investigacionv5

- ID del análisis: `1a10a10a-37b7-407b-b919-51fd2b8299c2`
- Base analizada: `investigacionv5`
- Fecha UTC: `2026-11-06T05:51:32.997180+00:00`
- Filas sumadas de las 11 tablas base: **62,340**
- Las vistas analíticas no se cuentan como tablas base.

## Auditoría de integridad

| Tabla | Filas |
|---|---:|
| `benchmark_corrida` | 22,737 |
| `complejidad_funcion` | 3,985 |
| `ejecucion_experimental` | 1,775 |
| `ejecucion_herramienta` | 0 |
| `medicion_metrica` | 10,609 |
| `plantilla_prompt` | 4 |
| `problema` | 150 |
| `protocolo_experimental` | 1 |
| `registro_evento` | 1,775 |
| `resultado_prueba` | 21,300 |
| `tecnica_prompt` | 4 |

- Combinaciones planificadas: 1,800; ejecuciones registradas: 1,775; combinaciones ausentes: 25 en 6 problemas.
- Duplicados de combinación ejecución/problema/técnica/repetición: 0; identificadores de prueba duplicados: 0.
- Estados: `{"completada": 1756, "fallida": 19}`.
- Las 19 ejecuciones fallidas carecen de respuesta/código persistido y se tratan como ejecuciones incompletas; sus mediciones ya persistidas solo se usan para la variable correspondiente.
- Observaciones válidas por indicador: `{"porcentaje_pruebas_aprobadas": 1775, "maintainability_index": 1775, "complejidad_ciclomatica_max": 1775, "sloc": 1772, "tiempo_promedio_ms": 1118, "memoria_mediana_bytes": 1118}`.
- Nulos / no finitos por indicador: `{"memoria_mediana_bytes": 638, "tiempo_promedio_ms": 638}` / `{}`.
- Unidades observadas: `{"porcentaje_pruebas_aprobadas": {"%": 1775}, "maintainability_index": {"puntos": 1775}, "complejidad_ciclomatica_max": {"rutas": 1775}, "sloc": {"lineas": 1772}, "tiempo_promedio_ms": {"ms": 1756}, "memoria_mediana_bytes": {"bytes": 1756}}`.
- Bloques completos por indicador (al menos una repetición válida por cada técnica): `{"porcentaje_pruebas_aprobadas": 145, "maintainability_index": 145, "complejidad_ciclomatica_max": 145, "sloc": 145, "tiempo_promedio_ms": 82, "memoria_mediana_bytes": 82}`.
- Sensibilidad estricta (3 repeticiones válidas para las cuatro técnicas): `{"porcentaje_pruebas_aprobadas": 144, "maintainability_index": 144, "complejidad_ciclomatica_max": 144, "sloc": 143, "tiempo_promedio_ms": 67, "memoria_mediana_bytes": 67}`.
- Corridas de benchmark con salida no cero en al menos una medición: 631; completadas sin filas de benchmark: 7.

Los valores atípicos potenciales se marcan usando la regla exploratoria de 1,5×IQR en observaciones válidas de ejecución. No se eliminan ni winsorizan; Friedman es una prueba basada en rangos. El detalle de cercas y conteos está en `auditoria.csv`.

## Decisiones estadísticas

- Las repeticiones pertenecen a la misma combinación problema-técnica; se resumen con la mediana para reducir sensibilidad a observaciones extremas y no inflar el tamaño muestral.
- Cada problema es un bloque y cada técnica un tratamiento: prueba global de Friedman por indicador, con Kendall W como tamaño de efecto.
- Se aplicó Holm a los seis contrastes globales (exactitud, MI, CC, SLOC, tiempo, memoria; α=.05).
- Solo los indicadores con Friedman significativo tras Holm tienen post hoc Wilcoxon pareado; Holm se aplica a los seis pares de técnicas dentro de cada indicador. Se informa rango biserial pareado y bootstrap percentil del 95% para la diferencia mediana A−B.
- Sensibilidad: se repite Friedman restringiendo a bloques que tienen las tres repeticiones válidas en las cuatro técnicas; Holm se aplica separadamente a los seis contrastes de sensibilidad.
- SLOC se trata como resultado descriptivo de tamaño, sin presuponer que menos líneas signifiquen mejor calidad.
- No se construye un índice compuesto ni se interpreta un resultado no significativo como equivalencia.

## Estadística descriptiva

La tabla principal usa medianas por problema-técnica y solo los bloques completos del indicador, para comparar las técnicas sobre los mismos problemas. `estadistica_descriptiva.csv` también contiene el conjunto de todas las celdas problema-técnica observadas.

| Indicador | Técnica | n problemas | Media | DE | Mediana | Q1–Q3 | Mín–Máx | CV (%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Exactitud funcional (% pruebas aprobadas) | Zero-shot | 145 | 64.138 | 37.760 | 75.000 | 33.330–100.000 | 0.000–100.000 | — |
| Exactitud funcional (% pruebas aprobadas) | Few-shot | 145 | 69.483 | 36.114 | 91.670 | 41.670–100.000 | 0.000–100.000 | — |
| Exactitud funcional (% pruebas aprobadas) | Chain-of-Thought | 145 | 63.046 | 38.750 | 75.000 | 25.000–100.000 | 0.000–100.000 | — |
| Exactitud funcional (% pruebas aprobadas) | Role prompting | 145 | 63.563 | 38.074 | 75.000 | 25.000–100.000 | 0.000–100.000 | — |
| Maintainability Index | Zero-shot | 145 | 71.598 | 15.100 | 70.790 | 59.450–82.970 | 37.620–100.000 | — |
| Maintainability Index | Few-shot | 145 | 67.018 | 14.419 | 62.730 | 56.880–75.300 | 38.940–100.000 | — |
| Maintainability Index | Chain-of-Thought | 145 | 66.561 | 15.558 | 61.770 | 54.710–78.270 | 37.110–100.000 | — |
| Maintainability Index | Role prompting | 145 | 71.577 | 15.685 | 68.960 | 59.030–83.830 | 42.340–100.000 | — |
| Complejidad ciclomática máxima | Zero-shot | 145 | 6.138 | 3.449 | 5.000 | 4.000–7.000 | 2.000–22.000 | — |
| Complejidad ciclomática máxima | Few-shot | 145 | 5.593 | 2.554 | 5.000 | 4.000–7.000 | 2.000–17.000 | — |
| Complejidad ciclomática máxima | Chain-of-Thought | 145 | 6.103 | 3.488 | 5.000 | 4.000–8.000 | 2.000–22.000 | — |
| Complejidad ciclomática máxima | Role prompting | 145 | 5.855 | 3.089 | 5.000 | 4.000–7.000 | 2.000–17.000 | — |
| Líneas de código fuente (SLOC) | Zero-shot | 145 | 19.317 | 9.755 | 18.000 | 12.000–26.000 | 5.000–60.000 | 50.50 |
| Líneas de código fuente (SLOC) | Few-shot | 145 | 18.676 | 10.139 | 17.000 | 12.000–24.000 | 5.000–62.000 | 54.29 |
| Líneas de código fuente (SLOC) | Chain-of-Thought | 145 | 19.276 | 9.517 | 18.000 | 12.000–25.000 | 5.000–64.000 | 49.37 |
| Líneas de código fuente (SLOC) | Role prompting | 145 | 19.359 | 9.539 | 17.000 | 12.000–25.000 | 5.000–51.000 | 49.28 |
| Tiempo promedio de ejecución | Zero-shot | 82 | 6.357 | 54.300 | 0.184 | 0.167–0.243 | 0.122–491.907 | 854.14 |
| Tiempo promedio de ejecución | Few-shot | 82 | 4.374 | 36.242 | 0.184 | 0.162–0.245 | 0.123–328.279 | 828.66 |
| Tiempo promedio de ejecución | Chain-of-Thought | 82 | 2.942 | 24.747 | 0.185 | 0.161–0.236 | 0.120–224.300 | 841.30 |
| Tiempo promedio de ejecución | Role prompting | 82 | 2.992 | 23.385 | 0.182 | 0.163–0.234 | 0.121–211.488 | 781.64 |
| Memoria mediana máxima | Zero-shot | 82 | 51652.232 | 144254.556 | 29300.000 | 29175.250–39763.250 | 27978.000–1328592.000 | 279.28 |
| Memoria mediana máxima | Few-shot | 82 | 48874.671 | 118692.988 | 29307.000 | 29175.250–39763.250 | 27978.000–1092944.000 | 242.85 |
| Memoria mediana máxima | Chain-of-Thought | 82 | 45725.451 | 108610.767 | 29300.000 | 29175.250–39739.000 | 27978.000–1015185.000 | 237.53 |
| Memoria mediana máxima | Role prompting | 82 | 48050.049 | 110494.633 | 29300.000 | 29175.250–39763.250 | 27978.000–1015561.000 | 229.96 |

## Pruebas globales

| Indicador | n bloques | χ² de Friedman | gl | p | p Holm (6 indicadores) | W Kendall | Resultado |
|---|---:|---:|---:|---:|---:|---:|---|
| Exactitud funcional (% pruebas aprobadas) | 145 | 3.9982 | 3 | 0.261661 | 0.939465 | 0.0092 | no significativo |
| Maintainability Index | 145 | 16.1889 | 3 | 0.0010372 | 0.00622322 | 0.0372 | significativo |
| Complejidad ciclomática máxima | 145 | 4.0944 | 3 | 0.251447 | 0.939465 | 0.0094 | no significativo |
| Líneas de código fuente (SLOC) | 145 | 10.5647 | 3 | 0.0143282 | 0.0716412 | 0.0243 | no significativo |
| Tiempo promedio de ejecución | 82 | 4.2585 | 3 | 0.234866 | 0.939465 | 0.0173 | no significativo |
| Memoria mediana máxima | 82 | 1.1408 | 3 | 0.767224 | 0.939465 | 0.0046 | no significativo |

## Sensibilidad: solo bloques con 12 repeticiones válidas

| Indicador | n bloques | χ² de Friedman | p | p Holm | W Kendall | Resultado |
|---|---:|---:|---:|---:|---:|---|
| Exactitud funcional (% pruebas aprobadas) | 144 | 3.9982 | 0.261661 | 0.879779 | 0.0093 | no significativo |
| Maintainability Index | 144 | 15.7183 | 0.00129521 | 0.00777123 | 0.0364 | significativo |
| Complejidad ciclomática máxima | 144 | 4.4156 | 0.219945 | 0.879779 | 0.0102 | no significativo |
| Líneas de código fuente (SLOC) | 143 | 10.9864 | 0.0117994 | 0.0589969 | 0.0256 | no significativo |
| Tiempo promedio de ejecución | 67 | 2.3373 | 0.50541 | 1 | 0.0116 | no significativo |
| Memoria mediana máxima | 67 | 0.6667 | 0.881015 | 1 | 0.0033 | no significativo |

## Comparaciones post hoc

Las diferencias se expresan como técnica A menos técnica B. El rango biserial pareado incluye IC bootstrap percentil; también se presenta el IC de la diferencia mediana pareada.

| Indicador | A | B | n | p | p Holm (pares) | Rango biserial [IC 95%] | Dif. mediana A−B [IC 95%] |
|---|---|---|---:|---:|---:|---:|---:|
| Maintainability Index | ZERO_SHOT | FEW_SHOT | 145 | 0.00350297 | 0.0105089 | 0.301 [0.104, 0.486] | 0.000 [0.000, 1.050] puntos (0-100) |
| Maintainability Index | ZERO_SHOT | CHAIN_OF_THOUGHT | 145 | 0.000175611 | 0.000878055 | 0.416 [0.213, 0.596] | 0.000 [0.000, 0.570] puntos (0-100) |
| Maintainability Index | ZERO_SHOT | ROLE_PROMPTING | 145 | 0.188127 | 0.188127 | -0.158 [-0.391, 0.077] | 0.000 [0.000, 0.000] puntos (0-100) |
| Maintainability Index | FEW_SHOT | CHAIN_OF_THOUGHT | 145 | 0.0731795 | 0.146359 | 0.185 [-0.018, 0.384] | 0.250 [0.000, 1.140] puntos (0-100) |
| Maintainability Index | FEW_SHOT | ROLE_PROMPTING | 145 | 0.00122621 | 0.00490483 | -0.331 [-0.511, -0.142] | 0.000 [-1.050, 0.000] puntos (0-100) |
| Maintainability Index | CHAIN_OF_THOUGHT | ROLE_PROMPTING | 145 | 2.86242e-07 | 1.71745e-06 | -0.583 [-0.735, -0.399] | 0.000 [-0.570, 0.000] puntos (0-100) |

Nota: por el redondeo y empates del MI, la mediana de la diferencia pareada puede ser cero y su IC bootstrap incluir cero aunque Wilcoxon detecte asimetría en los rangos. Para el tamaño y dirección del efecto de rangos, consulte el rango biserial y su IC bootstrap; un p significativo no implica una diferencia grande.

## Hipótesis

| Hipótesis | Decisión | Indicadores que aportan evidencia |
|---|---|---|
| HE1 | sin respaldo estadístico | Ninguno |
| HE2 | respaldo estadístico | maintainability_index |
| HE3 | sin respaldo estadístico | Ninguno |
| HG | respaldo estadístico parcial | maintainability_index |

## Figuras

- [Exactitud funcional (% pruebas aprobadas)](figuras/porcentaje_pruebas_aprobadas.png)
- [Maintainability Index](figuras/maintainability_index.png)
- [Complejidad ciclomática máxima](figuras/complejidad_ciclomatica_max.png)
- [Líneas de código fuente (SLOC)](figuras/sloc.png)
- [Tiempo promedio de ejecución](figuras/tiempo_promedio_ms.png)
- [Memoria mediana máxima](figuras/memoria_mediana_bytes.png)

## Interpretación y límites

Los resultados de exactitud y mantenibilidad se basan en los indicadores persistidos, incluyendo mediciones parciales de ejecuciones cuyo registro final quedó fallido; esas 19 ejecuciones no tienen código ni respuesta archivados, por lo que su procedencia no puede auditarse íntegramente. Se cuantifica este hecho y se excluyen del análisis las variables que no tienen un valor válido.

La disponibilidad de tiempo y memoria depende de que el código complete la primera aserción usada por el benchmark. En los datos, 631 grupos de benchmark tienen salida no cero durante mediciones y 7 ejecuciones completadas no tienen filas de benchmark. Por ello, las pruebas de eficiencia describen solo ejecuciones con medición válida; pueden sufrir sesgo de selección y no deben generalizarse a todas las generaciones.

El sistema guarda tiempo en milisegundos como **promedio** de corridas correctas y memoria en bytes como **mediana**. Se verificó que ambas métricas guardadas coinciden con las corridas originales válidas. Aunque el manual menciona tiempo mediano, este análisis respeta y documenta el cálculo realmente almacenado.

La falta de diferencias significativas no prueba equivalencia. W de Kendall mide magnitud de concordancia de rangos entre tratamientos; dirección y pares deben interpretarse junto con la mediana, intervalos y corrección múltiple. El análisis compara el comportamiento de estas técnicas en estos problemas y bajo este protocolo, sin afirmar una superioridad universal.

## Reproducción

Desde la raíz del proyecto: ` .venv/bin/python analisis_estadistico_investigacionv5/analizar.py --database investigacionv5 --user postgres`.
El código y datos tabulares de esta corrida se guardaron en `1a10a10a37b7407bb91951fd2b8299c2/`; las tablas persistentes están en el esquema PostgreSQL `analisis_estadistico`.
