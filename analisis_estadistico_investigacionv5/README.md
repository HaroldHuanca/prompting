# Análisis de investigacionv5

Este análisis usa el problema como bloque, resume las repeticiones por
problema-técnica con la mediana y contrasta los seis indicadores mediante
Friedman. Aplica Holm a las pruebas globales y a los post hoc Wilcoxon
pareados; incluye una sensibilidad restringida a bloques con las tres
repeticiones válidas en las cuatro técnicas. No imputa ni elimina valores.

## Reproducir

Instala las dependencias en el entorno virtual del proyecto y ejecuta desde la
raíz:

```bash
.venv/bin/python -m pip install -r analisis_estadistico_investigacionv5/requirements.txt
.venv/bin/python analisis_estadistico_investigacionv5/analizar.py --database investigacionv5 --user postgres
```

Cada ejecución agrega un análisis independiente al esquema PostgreSQL
`analisis_estadistico` y genera una carpeta con auditoría, mediciones
numéricas, datos procesados, tablas, figuras y el informe en
`resultados/<analysis_id>/`. No se conecta a OpenAI ni modifica los datos
experimentales originales.
