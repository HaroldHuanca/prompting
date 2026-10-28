# PromptLab Research | ChatGPT-4o Empirical Benchmarking Platform

Plataforma experimental automatizada para la tesis de investigación:
> **"Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o"**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.14-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%20%7C%2018-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-ChatGPT--4o%20(T%3D0.0)-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 🚀 Inicio Rápido (Quick Start)

Para una guía paso a paso completa, consulte el [MANUAL_INICIO.md](MANUAL_INICIO.md).

```bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd prompting

# 2. Configurar entorno virtual e instalar dependencias
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Inicializar Base de Datos en PostgreSQL
createdb -U postgres investigacionv2
psql -U postgres -d investigacionv2 -f database/schema.sql
psql -U postgres -d investigacionv2 -f database/seed_problems.sql

# 4. Configurar variables de entorno
cp .env.example .env

# 5. Iniciar la plataforma
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Abra su navegador en **[http://localhost:8000](http://localhost:8000)**.

---

## 📋 Características Principales

1. **Ingesta y Segregación de Problemas (LeetCode):**
   - Importación directa vía interfaz con el botón **"📂 Cargar desde JSON"**.
   - Segregación estricta entre `ejemplos_enunciado`, `ejemplos_few_shot` y `pruebas_funcionales`.
   - Plantilla de importación disponible en [plantilla_problema_leetcode.json](plantilla_problema_leetcode.json).
2. **Evaluación de las 4 Técnicas Canónicas:**
   - **Zero-Shot** (Instrucción directa).
   - **Few-Shot** (Demostraciones estructuradas).
   - **Chain-of-Thought [CoT]** (Razonamiento paso a paso).
   - **Role Prompting** (Ingeniero de Software Principal).
3. **Pipeline de Evaluación Multi-Dimensional:**
   - **Exactitud Funcional:** Ejecución automatizada con **Pytest**.
   - **Mantenibilidad:** Maintainability Index (MI), Complejidad Ciclomática (CC) y SLOC con **Radon**.
   - **Eficiencia:** Perfilamiento de tiempo con **timeit** (3 warmup + 10 runs) y memoria pico con **tracemalloc**.
4. **Determinismo Científico:**
   - Parámetro mandatorio `temperature=0.0` (Greedy Decoding).
   - Auditoría criptográfica por hash **SHA-256**.
5. **Exportación de Datos:**
   - Descarga de datasets científicos consolidados en **CSV** y **JSON** para análisis en R, Python/Pandas y SPSS.

---

## 📚 Documentación Técnica (Metodología de Cascada Adaptada)

Los documentos formales de la investigación se encuentran en la carpeta [`/docs`](docs/):
- [Docs 01: Análisis de Requerimientos Funcionales y No Funcionales](docs/01_analisis_requerimientos.md)
- [Docs 02: Diseño de Arquitectura, Diagramas y Modelo E-R](docs/02_diseno_arquitectura.md)
- [Docs 03: Guía de Implementación y Catálogo de API Endpoints](docs/03_implementacion_guia.md)
- [Docs 04: Pruebas, Validación y Determinismo T=0.0](docs/04_pruebas_y_validacion.md)

---

## 🧪 Pruebas Automatizadas

Ejecute la suite completa con 24 pruebas:
```bash
pytest tests/ -v
```
