# Informe estadístico de la experimentación con ChatGPT-4o

## 1. Identificación del análisis

- **Base de datos:** `investigacionv5`.
- **Protocolo:** `EXP-2026-GPT4O-02`.
- **Modelo reportado por la API:** `gpt-4o-2024-08-06`.
- **ID de la corrida estadística final:** `1a10a10a-37b7-407b-b919-51fd2b8299c2`.
- **Fecha del análisis:** 6 de noviembre de 2026 (UTC).
- **Tablas experimentales:** 62.340 filas en 11 tablas base.
- **Tablas analíticas:** siete tablas bajo el esquema PostgreSQL `analisis_estadistico`.
- **Código reproducible:** [analizar.py](./analisis_estadistico_investigacionv5/analizar.py).
- **Archivos de esta corrida:** [carpeta de resultados](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/).

Este informe conserva el estado observado y analizado; no completa ni imputa las ejecuciones ausentes. Las pruebas estadísticas usan exclusivamente mediciones guardadas en `investigacionv5`. No se realizaron inferencias adicionales a la API de OpenAI como parte de este análisis.

## 2. Diseño y objetivo

El diseño previsto compara cuatro técnicas de prompting en los mismos problemas, con el problema como bloque:

1. Zero-Shot (`ZERO_SHOT`).
2. Few-Shot (`FEW_SHOT`).
3. Chain-of-Thought (`CHAIN_OF_THOUGHT`).
4. Role Prompting (`ROLE_PROMPTING`).

La matriz planeada tenía 150 problemas × 4 técnicas × 3 repeticiones = **1.800 generaciones**. Las dimensiones de calidad consideradas son exactitud funcional, mantenibilidad y eficiencia de desempeño. No se creó un índice compuesto de calidad.

## 3. Auditoría de la base experimental

### 3.1 Filas por tabla

El conteo suma filas de tablas base; las vistas no se cuentan.

| Tabla | Filas |
|---|---:|
| `protocolo_experimental` | 1 |
| `tecnica_prompt` | 4 |
| `problema` | 150 |
| `plantilla_prompt` | 4 |
| `ejecucion_experimental` | 1.775 |
| `resultado_prueba` | 21.300 |
| `ejecucion_herramienta` | 0 |
| `medicion_metrica` | 10.609 |
| `benchmark_corrida` | 22.737 |
| `complejidad_funcion` | 3.985 |
| `registro_evento` | 1.775 |
| **Total** | **62.340** |

Las 1.775 ejecuciones registradas se desglosan en **1.756 completadas** y **19 fallidas/incompletas**. No hay filas duplicadas por protocolo-problema-técnica-repetición ni identificadores de prueba duplicados. Hay 25 combinaciones ausentes, distribuidas en seis problemas; por ello, el diseño no constituye un factorial completo.

Las 19 ejecuciones fallidas tienen métricas parciales guardadas, pero no respuesta ni código generado persistidos. Sus métricas numéricas válidas se incluyen únicamente en los análisis del indicador correspondiente. La falta de la respuesta impide auditar plenamente la procedencia de esos valores.

### 3.2 Esquema de los datos examinados

Las relaciones principales son `ejecucion_experimental` → `problema` y `tecnica_prompt`; `resultado_prueba`, `medicion_metrica`, `benchmark_corrida`, `complejidad_funcion` y `registro_evento` se enlazan mediante `ejecucion_id`.

| Entidad | Campos usados o relevantes |
|---|---|
| Ejecución | `ejecucion_id`, `problema_id`, `tecnica_id`, `numero_repeticion`, `estado_ejecucion`, `estado_validacion`, `duracion_generacion_ms`, `modelo_reportado`, `identificador_modelo`, `respuesta_completa`, `codigo_generado`, `hash_codigo_sha256` |
| Medición | `ejecucion_id`, `dimension`, `indicador`, `metrica`, `valor_numerico`, `unidad`, `estado_medicion` |
| Prueba funcional | `ejecucion_id`, `identificador_prueba`, `estado`, `duracion_ms`, errores y salidas |
| Benchmark | `ejecucion_id`, `tipo_corrida`, `resultado_correcto`, `tiempo_ejecucion_ms`, `memoria_pico_bytes`, `timeout`, `codigo_salida` |
| Complejidad por función | `ejecucion_id`, `nombre_funcion`, `complejidad_ciclomatica`, `complejidad_cognitiva` |

La base registra el identificador de modelo `gpt-4o-2024-08-06` en las 1.756 ejecuciones completadas. De las 19 fallidas, ninguna tiene identificador de modelo registrado.

### 3.3 Integridad, faltantes y unidades

| Indicador | Valores válidos por ejecución | Nulos/error | Bloques completos, ≥1 repetición válida por técnica | Sensibilidad, 3 repeticiones válidas por las 4 técnicas |
|---|---:|---:|---:|---:|
| Exactitud (% pruebas aprobadas) | 1.775 | 0 | 145 | 144 |
| Maintainability Index (MI) | 1.775 | 0 | 145 | 144 |
| Complejidad ciclomática máxima (CC) | 1.775 | 0 | 145 | 144 |
| SLOC | 1.772 | 3 | 145 | 143 |
| Tiempo promedio | 1.118 | 638 | 82 | 67 |
| Memoria mediana máxima | 1.118 | 638 | 82 | 67 |

Las unidades son consistentes: exactitud en porcentaje, MI en puntos, CC en rutas, SLOC en líneas, tiempo en milisegundos y memoria en bytes. No se detectaron valores no finitos. Se comprobó que los 1.118 promedios de tiempo y las 1.118 medianas de memoria coinciden con las corridas válidas almacenadas.

El benchmark mide la primera aserción funcional. **631** ejecuciones tienen al menos una salida no cero en sus corridas de medición; además, siete ejecuciones completadas no tienen filas de benchmark. La falta de tiempo y memoria, por tanto, no es aleatoria ni puede considerarse un simple dato administrativo: está ligada a la posibilidad de completar ese caso evaluado. La inferencia sobre eficiencia se limita a las ejecuciones con benchmark válido y puede tener sesgo de selección.

### 3.4 Rango y observaciones atípicas

Se señalaron observaciones potencialmente atípicas mediante la regla exploratoria de 1,5 × IQR. Se conservaron todos los valores: no se eliminaron, recortaron ni reemplazaron.

| Indicador | Válidos | Mínimo | Máximo | Atípicos potenciales (1,5 × IQR) |
|---|---:|---:|---:|---:|
| Exactitud funcional | 1.775 | 0 % | 100 % | 0 |
| MI | 1.775 | 37,04 | 100 | 0 |
| CC máxima | 1.775 | 2 | 27 | 109 |
| SLOC | 1.772 | 5 | 66 | 35 |
| Tiempo promedio | 1.118 | 0,119926 ms | 492,518860 ms | 83 |
| Memoria mediana máxima | 1.118 | 27.978 bytes | 1.328.680 bytes | 37 |

Los valores extremos de tiempo y memoria explican por qué la media y el coeficiente de variación son muy sensibles a la cola. Las pruebas globales de Friedman se basan en rangos y no requieren eliminar esos valores.

## 4. Procedimiento estadístico

Las 1.800 generaciones no se tratan como observaciones independientes. Las tres repeticiones de un problema-técnica se resumieron mediante su **mediana**, una medida robusta a valores extremos. Luego se aplicó **Friedman**, con el problema como bloque y la técnica como tratamiento. El tamaño muestral de cada prueba es el número de problemas completos para ese indicador.

- Pruebas globales bilaterales, α = 0,05; 3 grados de libertad.
- Tamaño de efecto global: **W de Kendall**, con \(W=\chi^2/[n(k-1)]\).
- Se aplicó **Holm** a los seis contrastes globales (exactitud, MI, CC, SLOC, tiempo y memoria).
- Los post hoc solo se ejecutaron para MI, el único resultado global significativo tras Holm. Se usó Wilcoxon de rangos con signo, bilateral, con Holm sobre los seis pares.
- En post hoc se informa rango biserial pareado con IC bootstrap percentil del 95% y diferencia mediana pareada con su IC bootstrap del 95%.
- Como sensibilidad, se repitió Friedman en problemas con las tres repeticiones válidas de cada técnica; se corrigieron esos seis contrastes por Holm por separado.
- SLOC se interpreta como tamaño de código, no como calidad direccional: menos líneas no implica necesariamente mejor código.

## 5. Estadística descriptiva

Resumen de las medianas de repetición por problema-técnica, restringido a bloques completos para el indicador. DE es la desviación estándar entre problemas; Q1 y Q3 delimitan el rango intercuartílico.

| Indicador | Técnica | n | Media | DE | Mediana | Q1–Q3 | Mín–Máx | CV (%) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Exactitud (%) | Zero-Shot | 145 | 64,138 | 37,760 | 75,000 | 33,330–100,000 | 0–100 | — |
| Exactitud (%) | Few-Shot | 145 | 69,483 | 36,114 | 91,670 | 41,670–100,000 | 0–100 | — |
| Exactitud (%) | Chain-of-Thought | 145 | 63,046 | 38,750 | 75,000 | 25,000–100,000 | 0–100 | — |
| Exactitud (%) | Role Prompting | 145 | 63,563 | 38,074 | 75,000 | 25,000–100,000 | 0–100 | — |
| MI | Zero-Shot | 145 | 71,598 | 15,100 | 70,790 | 59,450–82,970 | 37,620–100 | — |
| MI | Few-Shot | 145 | 67,018 | 14,419 | 62,730 | 56,880–75,300 | 38,940–100 | — |
| MI | Chain-of-Thought | 145 | 66,561 | 15,558 | 61,770 | 54,710–78,270 | 37,110–100 | — |
| MI | Role Prompting | 145 | 71,577 | 15,685 | 68,960 | 59,030–83,830 | 42,340–100 | — |
| CC máxima | Zero-Shot | 145 | 6,138 | 3,449 | 5 | 4–7 | 2–22 | — |
| CC máxima | Few-Shot | 145 | 5,593 | 2,554 | 5 | 4–7 | 2–17 | — |
| CC máxima | Chain-of-Thought | 145 | 6,103 | 3,488 | 5 | 4–8 | 2–22 | — |
| CC máxima | Role Prompting | 145 | 5,855 | 3,089 | 5 | 4–7 | 2–17 | — |
| SLOC | Zero-Shot | 145 | 19,317 | 9,755 | 18 | 12–26 | 5–60 | 50,50 |
| SLOC | Few-Shot | 145 | 18,676 | 10,139 | 17 | 12–24 | 5–62 | 54,29 |
| SLOC | Chain-of-Thought | 145 | 19,276 | 9,517 | 18 | 12–25 | 5–64 | 49,37 |
| SLOC | Role Prompting | 145 | 19,359 | 9,539 | 17 | 12–25 | 5–51 | 49,28 |
| Tiempo (ms) | Zero-Shot | 82 | 6,357 | 54,300 | 0,184 | 0,167–0,243 | 0,122–491,907 | 854,14 |
| Tiempo (ms) | Few-Shot | 82 | 4,374 | 36,242 | 0,184 | 0,162–0,245 | 0,123–328,279 | 828,66 |
| Tiempo (ms) | Chain-of-Thought | 82 | 2,942 | 24,747 | 0,185 | 0,161–0,236 | 0,120–224,300 | 841,30 |
| Tiempo (ms) | Role Prompting | 82 | 2,992 | 23,385 | 0,182 | 0,163–0,234 | 0,121–211,488 | 781,64 |
| Memoria (bytes) | Zero-Shot | 82 | 51.652,232 | 144.254,556 | 29.300 | 29.175–39.763 | 27.978–1.328.592 | 279,28 |
| Memoria (bytes) | Few-Shot | 82 | 48.874,671 | 118.692,988 | 29.307 | 29.175–39.763 | 27.978–1.092.944 | 242,85 |
| Memoria (bytes) | Chain-of-Thought | 82 | 45.725,451 | 108.610,767 | 29.300 | 29.175–39.739 | 27.978–1.015.185 | 237,53 |
| Memoria (bytes) | Role Prompting | 82 | 48.050,049 | 110.494,633 | 29.300 | 29.175–39.763 | 27.978–1.015.561 | 229,96 |

Las medias de tiempo y memoria son altas frente a sus medianas por la presencia de observaciones extremas; sus CV elevados desaconsejan interpretar la media aislada como rendimiento típico.

## 6. Pruebas globales de hipótesis

Hipótesis nula por indicador: las distribuciones/rangos de las cuatro técnicas son iguales en los bloques problema. Alternativa: existe al menos una diferencia entre técnicas.

| Indicador | n bloques | χ² de Friedman | gl | p sin ajustar | p Holm (6) | W Kendall | Decisión |
|---|---:|---:|---:|---:|---:|---:|---|
| Exactitud funcional | 145 | 3,9982 | 3 | 0,261661 | 0,939465 | 0,0092 | No significativo |
| MI | 145 | 16,1889 | 3 | 0,001037 | **0,006223** | 0,0372 | **Significativo** |
| CC máxima | 145 | 4,0944 | 3 | 0,251447 | 0,939465 | 0,0094 | No significativo |
| SLOC | 145 | 10,5647 | 3 | 0,014328 | 0,071641 | 0,0243 | No significativo tras Holm |
| Tiempo promedio | 82 | 4,2585 | 3 | 0,234866 | 0,939465 | 0,0173 | No significativo |
| Memoria mediana | 82 | 1,1408 | 3 | 0,767224 | 0,939465 | 0,0046 | No significativo |

MI es el único indicador con diferencias globales después de ajustar por seis pruebas. Su W de Kendall de 0,0372 representa un efecto global pequeño. SLOC tiene p sin ajustar de 0,0143, pero no supera el umbral ajustado de 0,05.

### 6.1 Comparaciones post hoc para MI

Las diferencias se definen como técnica A menos técnica B. Para el rango biserial pareado, valores positivos favorecen valores mayores en A; un MI mayor suele interpretarse como mejor mantenibilidad. Los IC son bootstrap percentiles del 95%. El p ajustado aplica Holm a los seis pares.

| Técnica A | Técnica B | n | p sin ajustar | p Holm | Rango biserial [IC 95%] | Diferencia mediana A−B [IC 95%] |
|---|---|---:|---:|---:|---:|---:|
| Zero-Shot | Few-Shot | 145 | 0,003503 | 0,010509 | 0,301 [0,104; 0,486] | 0,000 [0,000; 1,050] |
| Zero-Shot | Chain-of-Thought | 145 | 0,000176 | 0,000878 | 0,416 [0,213; 0,596] | 0,000 [0,000; 0,570] |
| Zero-Shot | Role Prompting | 145 | 0,188127 | 0,188127 | −0,158 [−0,391; 0,077] | 0,000 [0,000; 0,000] |
| Few-Shot | Chain-of-Thought | 145 | 0,073180 | 0,146359 | 0,185 [−0,018; 0,384] | 0,250 [0,000; 1,140] |
| Few-Shot | Role Prompting | 145 | 0,001226 | 0,004905 | −0,331 [−0,511; −0,142] | 0,000 [−1,050; 0,000] |
| Chain-of-Thought | Role Prompting | 145 | 0,000000286 | 0,000001717 | −0,583 [−0,735; −0,399] | 0,000 [−0,570; 0,000] |

Por el redondeo del MI y los empates, la mediana de la diferencia pareada puede ser cero y su IC contener cero aunque Wilcoxon detecte una asimetría en los rangos. La interpretación debe considerar conjuntamente p ajustado, rango biserial, su IC y la escala del MI; no debe inferirse una gran diferencia práctica solo por significancia.

## 7. Sensibilidad: tres repeticiones completas

Se repitió Friedman solo para problemas con las **12 observaciones** (tres repeticiones de cada una de las cuatro técnicas) válidas para el indicador. El resultado de MI se mantiene; el de SLOC sigue sin superar Holm. La pérdida de bloques en eficiencia es importante (n=67).

| Indicador | n bloques | χ² de Friedman | p sin ajustar | p Holm | W Kendall | Decisión |
|---|---:|---:|---:|---:|---:|---|
| Exactitud funcional | 144 | 3,9982 | 0,261661 | 0,879779 | 0,0093 | No significativo |
| MI | 144 | 15,7183 | 0,001295 | **0,007771** | 0,0364 | **Significativo** |
| CC máxima | 144 | 4,4156 | 0,219945 | 0,879779 | 0,0102 | No significativo |
| SLOC | 143 | 10,9864 | 0,011799 | 0,058997 | 0,0256 | No significativo tras Holm |
| Tiempo promedio | 67 | 2,3373 | 0,505410 | 1,000000 | 0,0116 | No significativo |
| Memoria mediana | 67 | 0,6667 | 0,881015 | 1,000000 | 0,0033 | No significativo |

## 8. Conclusiones por hipótesis

| Hipótesis | Conclusión | Fundamento |
|---|---|---|
| **HE1 — Exactitud funcional** | Sin respaldo estadístico en este análisis. | Friedman: p Holm = 0,9395. La mediana descriptiva de Few-Shot fue mayor, pero esa diferencia no basta para concluir un efecto estadístico. |
| **HE2 — Mantenibilidad** | Respaldo parcial. | MI difiere globalmente (p Holm = 0,0062; W = 0,0372) y el resultado se conserva en sensibilidad. CC no difiere significativamente. SLOC no supera Holm (p ajustado = 0,0716). |
| **HE3 — Eficiencia de desempeño** | Sin respaldo estadístico en las mediciones válidas, con limitación importante. | Tiempo (p Holm = 0,9395) y memoria (p Holm = 0,9395) no muestran diferencias globales; solo se observan 82 bloques completos y 67 en sensibilidad estricta. |
| **HG — Diferencias en calidad del código** | Respaldo estadístico parcial, restringido al MI. | Solo uno de los indicadores presenta diferencia global tras Holm. No implica superioridad general de una técnica ni demuestra que el efecto sea grande o prácticamente importante. |

La ausencia de significancia no demuestra equivalencia entre técnicas. Estos resultados describen la muestra de problemas y el protocolo evaluado; no justifican una afirmación universal ni causal adicional.

## 9. Limitaciones y advertencias para uso posterior

1. **Matriz incompleta:** hay 1.775/1.800 registros; faltan 25 combinaciones en seis problemas. Los bloques completos cambian según la disponibilidad de cada indicador.
2. **Ejecuciones fallidas:** 19 filas están marcadas como fallidas y carecen de respuesta/código archivados. Las métricas parciales se conservaron y pueden entrar en algunas variables; esta procedencia debe señalarse al reutilizar los datos.
3. **Selección en benchmarks:** tiempo y memoria están disponibles solo cuando el benchmark produce mediciones válidas. Hay 638 valores de error/nulos; analizar solo los casos válidos puede sesgar la comparación.
4. **Indicador de tiempo:** el esquema persiste el promedio de ejecuciones correctas aunque el manual describa un tiempo mediano. Este informe analiza el campo realmente guardado (`tiempo_promedio_ms`).
5. **Atípicos:** la regla IQR es exploratoria. Los casos fueron conservados; tiempo y memoria muestran colas muy largas.
6. **Redondeo y empates:** las diferencias de MI están cuantizadas/redondeadas. Esto puede producir medianas pareadas iguales a cero a la vez que Wilcoxon detecta diferencias en rangos.
7. **Repeticiones resumidas:** resumir por mediana evita pseudorreplicación y reduce sensibilidad a extremos, pero no modela por separado la variabilidad entre repeticiones.
8. **Alcance de la interpretación:** no se definió una regla de importancia práctica mínima; el pequeño W global de MI aconseja cautela. No hay base para declarar equivalencia ni superioridad universal.

## 10. Archivos y persistencia

Resultados y datos de la corrida final:

- [Informe generado por el script](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/informe.md).
- [Auditoría de integridad (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/auditoria.csv).
- [Mediciones originales consultadas (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/mediciones_originales.csv).
- [Datos procesados por problema y técnica (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/datos_procesados_por_problema_tecnica.csv).
- [Estadística descriptiva (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/estadistica_descriptiva.csv).
- [Pruebas globales (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/pruebas_globales.csv).
- [Análisis de sensibilidad (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/sensibilidad_12_repeticiones.csv).
- [Comparaciones post hoc (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/comparaciones_posthoc.csv).
- [Decisiones de hipótesis (CSV)](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/decisiones_hipotesis.csv).

Se generaron seis gráficos comparativos:

- [Exactitud funcional](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/porcentaje_pruebas_aprobadas.png).
- [Maintainability Index](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/maintainability_index.png).
- [Complejidad ciclomática](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/complejidad_ciclomatica_max.png).
- [SLOC](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/sloc.png).
- [Tiempo](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/tiempo_promedio_ms.png).
- [Memoria](./analisis_estadistico_investigacionv5/resultados/1a10a10a37b7407bb91951fd2b8299c2/figuras/memoria_mediana_bytes.png).

La corrida final incorporó 28 elementos de auditoría, 3.178 medianas procesadas, 48 descriptivos, 12 pruebas globales (principal y sensibilidad), seis comparaciones post hoc y cuatro decisiones de hipótesis en `analisis_estadistico`. Hay dos corridas de análisis persistidas en ese esquema; este informe y los enlaces anteriores corresponden a la más reciente.

Para reproducir el análisis desde la raíz del proyecto:

```bash
.venv/bin/python -m pip install -r analisis_estadistico_investigacionv5/requirements.txt
.venv/bin/python analisis_estadistico_investigacionv5/analizar.py --database investigacionv5 --user postgres
```

La ejecución crea un nuevo ID de análisis y agrega resultados; no modifica ni sobrescribe las mediciones experimentales originales.
