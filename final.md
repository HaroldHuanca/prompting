# CAPÍTULO IV. PRESENTACIÓN DE RESULTADOS

## 4.1. Caracterización de la experimentación

La plataforma experimental se desarrolló para evaluar cuatro técnicas de estructuración de prompts aplicadas sobre el mismo conjunto de problemas algorítmicos, con el problema como bloque experimental y la técnica como tratamiento. El análisis se centró en tres dimensiones de calidad del software: exactitud funcional, mantenibilidad y eficiencia de desempeño.

La auditoría de la base experimental realizada sobre la base `investigacionv5` evidenció que la matriz real no fue completamente factorial. Se registraron 1.775 ejecuciones frente a las 1.800 esperadas; 1.756 fueron completadas y 19 quedaron fallidas o incompletas. Además, hubo 25 combinaciones ausentes distribuidas en seis problemas. Por esta razón, los análisis inferenciales se realizaron sobre bloques completos y no sobre las 1.800 generaciones como si fueran observaciones independientes.

Los datos reales respaldan la siguiente estructura experimental observada:

- 150 problemas algorítmicos.
- 4 técnicas de prompting: Zero-Shot, Few-Shot, Chain-of-Thought y Role Prompting.
- 3 repeticiones por problema-técnica.
- 1.775 ejecuciones con registros completos o parciales.
- 145 problemas con información completa para la comparación de exactitud y mantenibilidad.
- 82 problemas con benchmark válido para tiempos y memoria.

## 4.2. Obtención y validación de los datos experimentales

La validación de la información se realizó a partir de los registros de ejecución, resultados funcionales, métricas de mantenibilidad y benchmarks de rendimiento. La base contempló indicadores de exactitud funcional (% de pruebas aprobadas), Maintainability Index (MI), complejidad ciclomática máxima (CC), SLOC, tiempo de ejecución y memoria máxima.

No se detectaron valores no finitos ni duplicados por problema-técnica-repetición. Se conservaron observaciones atípicas y se evitó la eliminación silenciosa de registros, de acuerdo con el principio de no imputar ni recortar datos sin justificación metodológica.

En cuanto a la preparación estadística, la estrategia adoptada consistió en resumir las tres repeticiones de cada combinación problema-técnica mediante la mediana, de modo que el análisis se basó en bloques problema y no en generaciones individuales. Este criterio es consistente con el diseño experimental emparejado y evita la pseudorreplicación.

## 4.3. Resultados descriptivos de la calidad del código generado

### 4.3.1. Exactitud funcional

La exactitud funcional se midió como el porcentaje de pruebas aprobadas por generación, resumido por problema-técnica. Los resultados descriptivos por técnica muestran la siguiente tendencia:

- Zero-Shot: media = 64,138 %, mediana = 75,000 %, DE = 37,760.
- Few-Shot: media = 69,483 %, mediana = 91,670 %, DE = 36,114.
- Chain-of-Thought: media = 63,046 %, mediana = 75,000 %, DE = 38,750.
- Role Prompting: media = 63,563 %, mediana = 75,000 %, DE = 38,074.

La técnica Few-Shot presentó la mayor media descriptiva en exactitud funcional, seguida de cerca por Zero-Shot y Role Prompting. Sin embargo, la dispersión fue alta en todas las técnicas y la mediana refleja una variabilidad considerable entre problemas, lo que indica que la diferencia observada no es uniforme entre los casos evaluados.

### 4.3.2. Mantenibilidad

Para la mantenibilidad se consideraron el Maintainability Index (MI), la complejidad ciclomática máxima y el SLOC. Los resultados fueron los siguientes:

- MI: Zero-Shot = 71,598; Few-Shot = 67,018; Chain-of-Thought = 66,561; Role Prompting = 71,577.
- CC máxima: Zero-Shot = 6,138; Few-Shot = 5,593; Chain-of-Thought = 6,103; Role Prompting = 5,855.
- SLOC: Zero-Shot = 19,317; Few-Shot = 18,676; Chain-of-Thought = 19,276; Role Prompting = 19,359.

En términos de MI, Role Prompting y Zero-Shot muestran valores medios ligeramente más altos que Few-Shot y Chain-of-Thought, aunque la diferencia no es grande en magnitud. La complejidad ciclomática y el SLOC no muestran patrones claramente distintos entre técnicas. Este hallazgo es relevante porque la mantenibilidad no puede interpretarse únicamente como la cantidad de líneas del código, sino como la relación entre estructura, legibilidad y complejidad lógica.

### 4.3.3. Eficiencia de desempeño

La eficiencia de desempeño se evaluó en función del tiempo de ejecución y del consumo máximo de memoria. Los resultados descriptivos sobre los 82 bloques completos disponibles para estas métricas fueron:

- Tiempo promedio (ms):
  - Zero-Shot = 6,357
  - Few-Shot = 4,374
  - Chain-of-Thought = 2,942
  - Role Prompting = 2,992
- Memoria mediana máxima (bytes):
  - Zero-Shot = 51.652.232
  - Few-Shot = 48.874.671
  - Chain-of-Thought = 45.725.451
  - Role Prompting = 48.050.049

Las medianas de tiempo y memoria fueron muy homogéneas entre técnicas: 0,184 ms para tiempo y aproximadamente 29.300 bytes para memoria, mientras que las medias quedaron influenciadas por observaciones extremas. Este patrón sugiere que las diferencias observadas en la media no reflejan un efecto típico de la técnica, sino la presencia de ejecuciones con colas largas y valores atípicos de rendimiento.

## 4.4. Análisis estadístico comparativo

### 4.4.1. Evaluación de supuestos estadísticos

Se evaluó la distribución de los indicadores y la pertinencia del contraste inferencial. La estructura emparejada por problema, junto con la presencia de valores atípicos y distribuciones sesgadas en tiempo y memoria, hizo que la prueba de Friedman fuera la alternativa más apropiada frente a pruebas paramétricas. La decisión no se basó únicamente en la significación de una prueba de normalidad, sino en la naturaleza del diseño experimental y en la robustez del procedimiento.

### 4.4.2. Comparación global de las técnicas

La prueba de Friedman se aplicó sobre los bloques problema para cada indicador. Los resultados obtenidos fueron los siguientes:

| Indicador | n bloques | χ² | gl | p Holm | Decisión |
|---|---:|---:|---:|---:|---|
| Exactitud funcional | 145 | 3,9982 | 3 | 0,9395 | No significativo |
| MI | 145 | 16,1889 | 3 | 0,0062 | Significativo |
| CC máxima | 145 | 4,0944 | 3 | 0,9395 | No significativo |
| SLOC | 145 | 10,5647 | 3 | 0,0716 | No significativo tras Holm |
| Tiempo promedio | 82 | 4,2585 | 3 | 0,9395 | No significativo |
| Memoria mediana | 82 | 1,1408 | 3 | 0,9395 | No significativo |

La única diferencia global que resistió la corrección por multiplicidad fue la del MI. En el caso de la exactitud funcional, de tiempo y de memoria, no hubo evidencia suficiente para afirmar diferencias estadísticamente significativas entre las técnicas evaluadas.

### 4.4.3. Comparaciones pareadas y corrección por multiplicidad

Para MI, se realizaron comparaciones pareadas con Wilcoxon y corrección de Holm. Se observó un efecto global pequeño (W de Kendall = 0,0372), con diferencias significativas en varios pares, principalmente entre Zero-Shot y Few-Shot, Zero-Shot y Chain-of-Thought, Few-Shot y Role Prompting, y Chain-of-Thought y Role Prompting. Sin embargo, la magnitud del efecto global fue pequeña y la interpretación práctica debe hacerse con cautela, dado que el indicador se expresa en una escala limitada y presenta empates por redondeo.

### 4.4.4. Tamaños del efecto y magnitud de las diferencias

Los tamaños del efecto global en exactitud, CC y eficiencia fueron mínimos o muy pequeños, indicando que las diferencias observadas no son consistentes ni suficientemente grandes para sostener una inferencia fuerte. En cambio, el efecto global de MI fue estadísticamente detectable, pero de magnitud pequeña; por lo tanto, no puede asumirse una superioridad general de una técnica sobre otra en toda la calidad del código generado.

## 4.5. Contrastación de hipótesis

### 4.5.1. Hipótesis nula y alternativa (enfoque clásico)

En el enfoque clásico de la prueba de hipótesis, la hipótesis nula (H0) representa la ausencia de efecto o la igualdad entre condiciones, mientras que la hipótesis alternativa (H1) representa la existencia de una diferencia significativa entre los tratamientos comparados. Por esta razón, en el presente estudio las hipótesis formuladas como “las técnicas mejoran significativamente…” son hipótesis alternativas; la hipótesis nula corresponde a la negación lógica de esa mejora, es decir, que no existe diferencia significativa entre técnicas.

La formulación clásica aplicada al diseño experimental es la siguiente:

- Hipótesis general
  - H0_G: Las técnicas de estructuración de prompts no mejoran significativamente la calidad del código generado por ChatGPT-4o.
  - H1_G: Al menos una técnica de estructuración de prompts mejora significativamente la calidad del código generado por ChatGPT-4o.

- Hipótesis específica 1: exactitud funcional
  - H0_E1: La exactitud funcional media de las cuatro técnicas es igual.
  - H1_E1: Al menos una técnica presenta una exactitud funcional distinta.

- Hipótesis específica 2: mantenibilidad
  - H0_E2: La mantenibilidad media de las cuatro técnicas es igual.
  - H1_E2: Al menos una técnica presenta un nivel de mantenibilidad distinto.

- Hipótesis específica 3: eficiencia de desempeño
  - H0_E3: La eficiencia de desempeño de las cuatro técnicas es igual.
  - H1_E3: Al menos una técnica presenta una eficiencia de desempeño distinta.

### 4.5.2. Decisión basada en los resultados reales

La decisión inferencial fue la siguiente:

- HE1 (exactitud funcional): no se rechaza H0. Los resultados descriptivos favorecen a Few-Shot, pero la diferencia no fue estadísticamente significativa tras la corrección por multiplicidad.
- HE2 (mantenibilidad): existe evidencia parcial de diferencia; la prueba global por Friedman para MI fue significativa, pero la magnitud del efecto fue pequeña y no todas las comparaciones pareadas fueron concluyentes. En consecuencia, la hipótesis de mejora significativa no puede sostenerse de manera general.
- HE3 (eficiencia de desempeño): no se rechaza H0. El tiempo y la memoria no mostraron diferencias globales significativas entre técnicas.

En síntesis, la formulación de hipótesis alternativa del proyecto es compatible con el diseño y con la lógica inferencial, pero la evidencia empírica de la base `investigacionv5` solo respalda una diferencia parcial en mantenibilidad, no en exactitud ni en eficiencia.

# CAPÍTULO V. DISCUSIÓN DE RESULTADOS

## 5.1. Influencia de las técnicas de prompts en la exactitud funcional

La comparación de técnicas en exactitud funcional no mostró diferencias estadísticamente significativas. El indicador tuvo un comportamiento heterogéneo entre problemas, con dispersiones elevadas y un rango muy amplio de resultados. Aunque Few-Shot obtuvo la mayor media descriptiva (69,483 %), la prueba de Friedman no evidenció un efecto global significativo tras Holm (p = 0,9395). Esto implica que la ventaja descriptiva observada no es suficiente para concluir que una técnica de prompting supere de manera consistente a las demás en la resolución funcional de los problemas evaluados.

La interpretación científica adecuada es que la exactitud funcional depende, en gran medida, del tipo de problema, de la complejidad de la tarea y de la variabilidad intrínseca del modelo, más que de una superioridad sistemática de una técnica sobre otra. En otras palabras, el prompt puede influir en la calidad de la solución, pero no de forma uniforme ni determinista.

## 5.2. Influencia de las técnicas de prompts en la mantenibilidad del código

La mantenibilidad fue la dimensión que mostró evidencia estadística más sólida. El análisis de Friedman para MI resultó significativo tras la corrección por multiplicidad (p Holm = 0,0062), aunque el tamaño del efecto global fue pequeño (W de Kendall = 0,0372). Esto sugiere que, si bien existen diferencias entre técnicas, estas no son de magnitud grande ni generalizadas a todas las comparaciones.

La comparación descriptiva indicó que Role Prompting y Zero-Shot presentaron una media ligeramente mayor en MI, mientras que Few-Shot y Chain-of-Thought mostraron valores menores. Sin embargo, el patrón no es uniforme para todos los indicadores: la complejidad ciclomática máxima y el SLOC no mostraron diferencias significativas tras Holm. Este resultado es importante porque la mantenibilidad no debe reducirse a un único indicador aislado; la calidad estructural del código requiere interpretar los diversos elementos que la componen.

Por ello, la discusión debe ser cautelosa: existe evidencia de que la técnica puede afectar aspectos de mantenibilidad, pero no de un modo absoluto ni con una diferencia práctica claramente grande. El caso más sólido es la diferencia en MI, no una superioridad total de una técnica en todas las métricas de calidad estructural.

## 5.3. Influencia de las técnicas de prompts en la eficiencia de desempeño

La eficiencia de desempeño no mostró diferencias estadísticamente significativas entre técnicas. El tiempo de ejecución y la memoria máxima tuvieron distribuciones muy sesgadas y con colas largas; en ese contexto, la media resultó altamente sensible a valores atípicos, por lo que la mediana resultó más apropiada para resumir la tendencia central.

Los resultados de los 82 bloques completos disponibles no indicaron diferencias globales significativas ni entre tiempos ni entre consumos de memoria. En consecuencia, no se puede afirmar que una técnica de prompting haya generado código más eficiente en términos de tiempo o de recursos bajo el protocolo experimental analizado.

La ausencia de significancia no debe interpretarse como equivalencia absoluta, sino como ausencia de evidencia suficiente con los datos disponibles. El diseño experimental y la disponibilidad parcial del benchmark restringen la poder estadístico de esta comparación.

## 5.4. Implicancias metodológicas, teóricas y prácticas

El análisis demuestra que, bajo la base experimental examinada, la calidad del código generado por ChatGPT-4o no responde de manera uniforme a una sola técnica de prompting. La comparación más robusta sugiere que la mejora depende del criterio de evaluación: para exactitud funcional y eficiencia de desempeño no hubo soporte estadístico, mientras que para mantenibilidad sí hubo evidencia parcial y de magnitud pequeña.

Metodológicamente, la decisión de tratar los problemas como bloques emparejados y las repeticiones como observaciones anidadas es esencial para evitar conclusiones espurias. Teóricamente, el estudio confirma que la formulación del prompt influye sobre la calidad del código, pero el efecto no es universal ni homogéneo.

Desde el punto de vista práctico, la elección de la técnica debe basarse en la dimensión de calidad que se priorice: si el objetivo principal es maximizar la corrección funcional, la diferencia entre técnicas no fue estadísticamente concluyente; si el objetivo principal es mejorar la mantenibilidad, una estrategia concreta puede ofrecer pequeñas ventajas, pero sin evidencia total ni generalizable.

# CONCLUSIONES

1. La base experimental analizada mostró un diseño incompleto respecto a la matriz teóricamente esperada, con 25 combinaciones faltantes y un número menor de ejecuciones que el previsto. Esto limita la inferencia y exige un análisis basado en bloques emparejados y no en observaciones independientes.

2. La exactitud funcional no presentó diferencias estadísticamente significativas entre las cuatro técnicas de prompting evaluadas. Aunque Few-Shot mostró la mayor media descriptiva, esta diferencia no fue suficiente para rechazar la hipótesis nula.

3. La mantenibilidad presentó evidencia parcial de diferencias entre técnicas, especialmente en el indicador MI. Sin embargo, el efecto fue pequeño y no fue consistente para todos los indicadores de calidad estructural; por ello, no puede afirmarse una superioridad general de una técnica sobre otra.

4. La eficiencia de desempeño, evaluada mediante tiempo y memoria, no mostró diferencias globales significativas entre técnicas. La presencia de valores atípicos y la disponibilidad parcial de benchmark limitan la interpretación de estas comparaciones.

5. En términos de la formulación clásica de hipótesis, las hipótesis planteadas en el estudio corresponden a hipótesis alternativas, mientras que la hipótesis nula es la ausencia de efecto o de diferencia entre técnicas. Los datos reales solo permiten rechazar la hipótesis nula para el MI, pero no para exactitud funcional ni para eficiencia de desempeño.

6. El conjunto de resultados indica que la selección de la técnica de prompting debe hacerse con criterio orientado al objetivo de evaluación: la mejora no es uniforme en todas las dimensiones de calidad del software y requiere un análisis contextual, no una generalización automática de la mejor técnica para todos los casos.

7. El presente estudio evidencia la necesidad de continuar con análisis más específicos por tipo de problema, por nivel de dificultad y por dimensión de calidad, de modo que la elección de la estrategia de prompting pueda apoyarse en evidencia más fina y más útil para la práctica de ingeniería de software.
