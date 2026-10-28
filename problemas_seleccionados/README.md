# Problemas seleccionados de LeetCode

Esta carpeta contiene 30 archivos JSON basados en `plantilla_problema_leetcode.json`: 10 problemas fáciles, 10 medios y 10 difíciles. Cada archivo incluye el enunciado, los ejemplos oficiales disponibles, una solución de referencia, pruebas funcionales y un ejemplo few-shot.

## Criterio de selección

La selección se obtuvo el 28 de octubre de 2026 consultando el endpoint público de problemas de LeetCode (`https://leetcode.com/api/problems/all/`). Se excluyeron los problemas ocultos y los que requieren una suscripción; luego se eligieron, por dificultad, los diez identificadores `frontend_question_id` más altos disponibles.

El endpoint no incluye una fecha de publicación. Por ello, el identificador ascendente se utilizó como aproximación reproducible a la recencia; no representa una verificación independiente de la fecha exacta de publicación. Los enunciados se conservan en inglés para mantener el texto original de LeetCode.

## Uso

Importa los archivos JSON desde la plataforma con **“Cargar desde JSON”**. Las pruebas funcionales llaman al método de LeetCode correspondiente en `Solution` (o a la clase indicada para el problema de diseño). Los ejemplos few-shot son demostraciones ilustrativas redactadas para acompañar cada problema.
