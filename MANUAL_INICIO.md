# Manual de Inicio y Guía de Operación para el Equipo de Investigación
## Plataforma Experimental: Prompt Engineering Research Lab

**Tesis:** *Técnicas de Estructuración de Prompts en la Calidad de Código Generado por el Modelo de Lenguaje de Gran Escala ChatGPT-4o*  
**Versión:** 1.0.0  
**Audiencia:** Integrantes del equipo de investigación, evaluadores y tesistas  

---

## 1. Introducción y Objetivo

Este manual tiene como objetivo guiar a los miembros del equipo de investigación en la puesta en marcha, configuración, ejecución y retroalimentación de la plataforma experimental automatizada.

La plataforma permite evaluar de manera reproducible y determinista ($T=0.0$) el código generado por **ChatGPT-4o** (`gpt-4o`) bajo cuatro técnicas de estructuración de prompts:
1. **Zero-Shot:** Instrucción directa sin demostraciones.
2. **Few-Shot:** Inyección guiada de ejemplos demostrativos de entrada/salida y código.
3. **Chain-of-Thought (CoT):** Razonamiento estructurado paso a paso previo al código.
4. **Role Prompting:** Imposición de un perfil de Ingeniero de Software Principal.

Las soluciones generadas son evaluadas multifacéticamente en:
- **Exactitud Funcional:** Aserciones automatizadas con **Pytest**.
- **Mantenibilidad:** Maintainability Index (MI), Complejidad Ciclomática (CC) y SLOC con **Radon**.
- **Eficiencia de Desempeño:** Tiempo mediano de CPU/Wall-clock con **timeit** (3 corridas de calentamiento + 10 de medición) y memoria pico con **tracemalloc**.

---

## 2. Requisitos Previos del Sistema

Asegúrese de contar con las siguientes herramientas en su estación de trabajo:
- **Sistema Operativo:** Linux (Ubuntu, Debian, Arch Linux, Fedora) o Windows 10/11 con WSL2 (recomendado), o macOS.
- **Python:** Versión **3.10 o superior** (probado y validado en Python 3.14).
- **PostgreSQL:** Versión **14 o superior** (probado en PostgreSQL 18).
- **Git** instalado.
- **Navegador Web:** Chrome, Firefox, Edge o Brave.

---

## 3. Instalación Paso a Paso

### Paso 1: Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd prompting
```

### Paso 2: Crear y Activar el Entorno Virtual
```bash
# Crear entorno virtual .venv
python3 -m venv .venv

# Activar en Linux / macOS:
source .venv/bin/activate

# Activar en Windows PowerShell:
# .venv\Scripts\Activate.ps1
```

### Paso 3: Instalar las Dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Configuración de la Base de Datos (PostgreSQL)

### Paso 4.1: Crear la Base de Datos
Acceda a PostgreSQL y cree la base de datos `investigacion`:
```bash
# Opción directa desde terminal:
createdb -U postgres investigacion

# O mediante psql:
psql -U postgres -c "CREATE DATABASE investigacion;"
```

### Paso 4.2: Ejecutar el Esquema Relacional y Datos Iniciales
Ejecute la migración del esquema relacional y la semilla inicial de problemas:
```bash
# 1. Crear tablas, vistas e índices del esquema "experimento"
psql -U postgres -d investigacion -f database/schema.sql

# 2. Cargar problemas semilla canónicos de LeetCode (Two Sum, Valid Parentheses, etc.)
psql -U postgres -d investigacion -f database/seed_problems.sql
```

---

## 5. Configuración de Variables de Entorno (`.env`)

Copie la plantilla de variables de entorno y configure sus credenciales:
```bash
cp .env.example .env
```

Abra el archivo `.env` con su editor favorito (`nano .env` o VS Code) y ajuste:
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO

# Conexión a PostgreSQL (ajuste usuario y contraseña si aplica)
DATABASE_URL=postgresql+asyncpg://postgres@localhost:5432/investigacion
DATABASE_SYNC_URL=postgresql://postgres@localhost:5432/investigacion

# OpenAI API (Ingrese su clave de OpenAI)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TARGET_MODEL=gpt-4o
TEMPERATURE=0.0

# Parámetros del Protocolo Experimental
CODIGO_PROTOCOLO=EXP-2026-GPT4O-01
BENCHMARK_WARMUP_RUNS=3
BENCHMARK_MEASURE_RUNS=10
EXECUTION_TIMEOUT_SECONDS=5.0
```

> [!NOTE]
> **Modo de Simulación Local (Sin Cuota / Offline):**  
> Si aún no dispone de una clave activa de OpenAI o desea realizar pruebas sin costo, puede dejar `OPENAI_API_KEY=` vacía. La plataforma detectará automáticamente la ausencia de la clave y ejecutará un motor de inferencia local determinista de alta fidelidad, permitiéndole probar el 100% de los evaluadores (Pytest, Radon, timeit y tracemalloc) y las vistas analíticas.

---

## 6. Despliegue y Ejecución de la Plataforma

Para iniciar el servidor backend FastAPI y servir la interfaz web:
```bash
# Asegúrese de tener el entorno virtual activo
source .venv/bin/activate

# Iniciar servidor con recarga automática
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Una vez iniciado, acceda desde su navegador web:
- **Plataforma Web:** [http://localhost:8000](http://localhost:8000)
- **Documentación de la API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 7. Guía de Uso de las 3 Interfaces Web

### 📝 Interfaz 1: Ingesta y Gestión de Problemas (LeetCode)
1. **Visualizar problemas existentes:** En la barra lateral izquierda verá la lista de problemas disponibles. Haga clic en cualquiera (ej. `LC-001 Two Sum`) para ver sus detalles en el formulario.
2. **Cargar un problema desde archivo JSON (Recomendado):**
   - Haga clic en el botón superior **"📂 Cargar desde JSON"**.
   - Seleccione un archivo `.json` preparado (ej. `ejemplos_problemas/ejemplo_leetcode_015_3sum.json`).
   - El sistema cargará automáticamente todos los campos: enunciado, restricciones, ejemplos del enunciado, demostraciones Few-Shot y pruebas Pytest.
   - Revise la información y haga clic en **"💾 Guardar Problema"** para registrarlo en PostgreSQL.
3. **Sección Especial Few-Shot:**
   - Note el recuadro destacado con borde violeta (**"⭐ SECCIÓN ESPECIAL FEW-SHOT"**).
   - **Regla de oro de la tesis:** Estas demostraciones están rigurosamente segregadas y sólo se inyectarán cuando se elija la técnica *Few-Shot*. Nunca se mezclarán con el enunciado oficial ni con los casos de prueba Pytest.

### ⚡ Interfaz 2: Panel de Ejecución Experimental en Vivo
1. **Seleccionar el problema** en el menú desplegable.
2. **Elegir la técnica de Prompting:**
   - `Zero-Shot`
   - `Few-Shot`
   - `Chain-of-Thought`
   - `Role Prompting`
3. **Visor de Prompt en Tiempo Real:** Observe cómo el panel izquierdo (*"💬 Prompt Construido"*) se actualiza instantáneamente con las instrucciones exactas que viajarán al modelo.
4. **Ejecutar:** Presione el botón **"🚀 Ejecutar Experimento"**.
5. **Resultados inmediatos:**
   - Panel Central: Respuesta íntegra de ChatGPT-4o con indicador de latencia en milisegundos.
   - Panel Derecho: Código Python limpio extraído con su hash **SHA-256**.
   - Banner de Métricas: Exactitud (% Pruebas aprobadas), Maintainability Index (Radon), Complejidad Ciclomática Máxima, Tiempo Mediano (ms) y Memoria Pico (KB).
   - Pestañas inferiores: Aserciones Pytest individuales, desglose por función de Radon y tabla de las 13 corridas de benchmark (3 calentamiento + 10 medición).

### 📊 Interfaz 3: Matriz Comparativa y Resultados
1. **Tarjetas de Resumen Global:** Muestra el desempeño consolidado por técnica (Zero-Shot vs Few-Shot vs CoT vs Role Prompting).
2. **Verificación de Determinismo ($T=0.0$):** Panel que audita si las repeticiones con los mismos parámetros arrojan hashes SHA-256 idénticos (Greedy decoding).
3. **Tabla Interactiva:** Consulta en vivo las vistas SQL de PostgreSQL (`vw_resumen_pruebas` y `vw_resumen_benchmark`).
4. **Exportar Datos:**
   - **"📥 Exportar CSV":** Descarga un archivo listo para importar en R o Microsoft Excel.
   - **"📥 Exportar JSON":** Descarga el dataset estructurado para procesamiento con Python Pandas / Jupyter Notebooks.

---

## 8. Estructura de la Plantilla JSON para Nuevos Problemas

Para que otros miembros del equipo recopilen problemas de LeetCode y los carguen sin fricción, utilicen la plantilla:
📄 [plantilla_problema_leetcode.json](file:///home/HaroldUser/prompting/plantilla_problema_leetcode.json)

### Ejemplo de Estructura:
```json
{
  "codigo": "LC-015",
  "titulo": "3Sum",
  "plataforma_origen": "LeetCode",
  "url_referencia": "https://leetcode.com/problems/3sum/",
  "dificultad": "Media",
  "categoria_algoritmica": "Arreglos y Dos Punteros",
  "enunciado": "Dado un arreglo nums...",
  "restricciones": "3 <= nums.length <= 3000",
  "solucion_referencia": "class Solution:\n    def threeSum(self, nums): ...",
  "ejemplos_enunciado": [
    { "entrada": "nums = [-1,0,1,2,-1,-4]", "salida": "[[-1,-1,2],[-1,0,1]]", "explicacion": "..." }
  ],
  "ejemplos_few_shot": [
    {
      "id": 1,
      "descripcion": "Demostración Two Pointers con ordenamiento",
      "entrada": "nums = [-2, 0, 0, 2, 2]",
      "salida": "[[-2, 0, 2]]",
      "explicacion": "Razonamiento que se inyecta en el prompt Few-Shot...",
      "codigo_ilustrativo": "def findTriplets(arr): ..."
    }
  ],
  "pruebas_funcionales": [
    { "nombre": "test_caso_general", "codigo": "assert Solution().threeSum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]" }
  ],
  "etiquetas": ["array", "two-pointers", "leetcode-medium"]
}
```

En la carpeta [`ejemplos_problemas/`](file:///home/HaroldUser/prompting/ejemplos_problemas/) encontrará ejemplos completos listos para probar:
- `ejemplos_problemas/ejemplo_leetcode_015_3sum.json`
- `ejemplos_problemas/ejemplo_leetcode_121_best_time_stock.json`

---

## 9. Ejecución de la Suite de Pruebas Automatizadas

Antes de subir cambios a Git o validar la instalación local, ejecute la suite de pruebas:
```bash
pytest tests/ -v
```
Se deben ejecutar y aprobar **24 pruebas unitarias y de integración**, garantizando que el pipeline de evaluación, la base de datos, el constructor de prompts y la API funcionen al 100%.

---

## 10. Preguntas Frecuentes y Solución de Problemas

1. **Error: `connection to server on socket "/run/postgresql/.s.PGSQL.5432" failed`**
   - Asegúrese de que el servicio de PostgreSQL esté iniciado:
     ```bash
     sudo systemctl status postgresql
     # Si está detenido:
     sudo systemctl start postgresql
     ```
2. **Error: `role "HaroldUser" does not exist`**
   - Ejecute `psql` especificando el usuario administrador: `psql -U postgres -d investigacion`.
3. **¿Cómo agregar un nuevo problema masivamente vía terminal?**
   - Puede usar el endpoint de importación por API:
     ```bash
     curl -X POST http://localhost:8000/api/problemas/importar-json \
          -H "Content-Type: application/json" \
          -d @ejemplos_problemas/ejemplo_leetcode_015_3sum.json
     ```
4. **¿Dónde se guardan los archivos de documentación de la tesis?**
   - En la carpeta [`/docs`](file:///home/HaroldUser/prompting/docs/), donde se encuentran los 4 documentos de la metodología de Cascada Adaptada.
