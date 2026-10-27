"""
Configuración central de la plataforma experimental de investigación.
Carga variables de entorno y define parámetros del protocolo experimental.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# URLs de Base de Datos PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres@localhost:5432/investigacion"
)
DATABASE_SYNC_URL = os.getenv(
    "DATABASE_SYNC_URL", 
    "postgresql://postgres@localhost:5432/investigacion"
)

# Configuración de OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TARGET_MODEL = os.getenv("TARGET_MODEL", "gpt-4o")
# Mandatorio según el protocolo: T=0.0 para Greedy Decoding determinista
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))

# Parámetros del Protocolo Experimental
CODIGO_PROTOCOLO = os.getenv("CODIGO_PROTOCOLO", "EXP-2026-GPT4O-01")
BENCHMARK_WARMUP_RUNS = int(os.getenv("BENCHMARK_WARMUP_RUNS", "3"))
BENCHMARK_MEASURE_RUNS = int(os.getenv("BENCHMARK_MEASURE_RUNS", "10"))
EXECUTION_TIMEOUT_SECONDS = float(os.getenv("EXECUTION_TIMEOUT_SECONDS", "5.0"))
