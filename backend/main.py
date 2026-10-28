"""
Punto de Entrada Principal de la API Backend (FastAPI).
Plataforma de Investigación Experimental: Prompt Engineering Research Lab
Tesis: Técnicas de Estructuración de Prompts en la Calidad de Código Generado por ChatGPT-4o
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routers import problemas, ejecuciones, metricas, export
from backend.config import CODIGO_PROTOCOLO, TARGET_MODEL, TEMPERATURE

app = FastAPI(
    title="Prompt Engineering Research Lab API",
    description="Plataforma de experimentación automatizada sobre ChatGPT-4o (T=0.0) para evaluación de calidad de código.",
    version="1.0.0",
)

# Configuración CORS abierta para entorno de investigación
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Routers Modulares
app.include_router(problemas.router)
app.include_router(ejecuciones.router)
app.include_router(metricas.router)
app.include_router(export.router)

@app.get("/api/health")
async def health_check():
    """Endpoint de estado del backend y servicios."""
    return {
        "status": "online",
        "protocolo": CODIGO_PROTOCOLO,
        "modelo_objetivo": TARGET_MODEL,
        "temperatura": TEMPERATURE,
        "entorno": "Arch Linux x86_64 / Python 3.14"
    }

# Montaje de archivos estáticos del Frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
