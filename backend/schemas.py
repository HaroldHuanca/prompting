"""
Esquemas Pydantic para validación y serialización de datos de la API.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EjemploEnunciado(BaseModel):
    entrada: str
    salida: str
    explicacion: Optional[str] = None

class EjemploFewShot(BaseModel):
    id: Optional[int] = None
    descripcion: Optional[str] = None
    entrada: str
    salida: str
    explicacion: Optional[str] = None
    codigo_ilustrativo: Optional[str] = None

class PruebaFuncional(BaseModel):
    nombre: str
    codigo: str

class ProblemaBase(BaseModel):
    codigo: str = Field(..., json_schema_extra={"example": "LC-001"})
    titulo: str = Field(..., json_schema_extra={"example": "Two Sum"})
    plataforma_origen: str = Field(default="LeetCode")
    url_referencia: Optional[str] = None
    dificultad: str = Field(..., json_schema_extra={"example": "Fácil"})
    categoria_algoritmica: Optional[str] = Field(None, json_schema_extra={"example": "Arreglos y Hash Table"})
    enunciado: str
    especificacion_entrada: Optional[str] = None
    especificacion_salida: Optional[str] = None
    restricciones: Optional[str] = None
    ejemplos_enunciado: List[Dict[str, Any]] = Field(default_factory=list)
    ejemplos_few_shot: List[Dict[str, Any]] = Field(default_factory=list)
    solucion_referencia: Optional[str] = None
    pruebas_funcionales: List[Dict[str, Any]] = Field(default_factory=list)
    etiquetas: List[str] = Field(default_factory=list)

class ProblemaCreate(ProblemaBase):
    pass

class ProblemaUpdate(BaseModel):
    titulo: Optional[str] = None
    dificultad: Optional[str] = None
    categoria_algoritmica: Optional[str] = None
    enunciado: Optional[str] = None
    especificacion_entrada: Optional[str] = None
    especificacion_salida: Optional[str] = None
    restricciones: Optional[str] = None
    ejemplos_enunciado: Optional[List[Dict[str, Any]]] = None
    ejemplos_few_shot: Optional[List[Dict[str, Any]]] = None
    solucion_referencia: Optional[str] = None
    pruebas_funcionales: Optional[List[Dict[str, Any]]] = None
    etiquetas: Optional[List[str]] = None
    activo: Optional[bool] = None

class ProblemaResponse(ProblemaBase):
    problema_id: int
    cantidad_ejemplos_few_shot: int
    version_problema: int
    activo: bool

class TecnicaResponse(BaseModel):
    tecnica_id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    requiere_ejemplos: bool

class PromptPreviewRequest(BaseModel):
    problema_id: int
    tecnica_codigo: str

class PromptPreviewResponse(BaseModel):
    problema_id: int
    problema_titulo: str
    tecnica_codigo: str
    tecnica_nombre: str
    prompt: str
    variables: Dict[str, Any]

class ExecutionRequest(BaseModel):
    problema_id: int
    tecnica_codigo: str
    numero_repeticion: int = Field(default=1, ge=1)

class ResultadoPruebaItem(BaseModel):
    identificador_prueba: str
    tipo_prueba: str
    estado: str
    duracion_ms: Optional[float] = None
    mensaje_error: Optional[str] = None

class ComplejidadItem(BaseModel):
    nombre_funcion: str
    nombre_clase: Optional[str] = None
    linea_inicio: Optional[int] = None
    linea_fin: Optional[int] = None
    complejidad_ciclomatica: Optional[int] = None

class BenchmarkItem(BaseModel):
    numero_corrida: int
    tipo_corrida: str
    conjunto_entrada: Optional[str] = None
    tiempo_ejecucion_ms: Optional[float] = None
    memoria_pico_bytes: Optional[int] = None
    timeout: bool

class ExecutionResponse(BaseModel):
    ejecucion_id: int
    problema_id: int
    problema_titulo: str
    tecnica_codigo: str
    tecnica_nombre: str
    numero_repeticion: int
    estado_ejecucion: str
    estado_validacion: str
    duracion_generacion_ms: Optional[float] = None
    hash_codigo_sha256: Optional[str] = None
    codigo_parseable: Optional[bool] = None
    generacion_exitosa: Optional[bool] = None
    prompt_enviado: Optional[str] = None
    respuesta_completa: Optional[str] = None
    codigo_generado: Optional[str] = None
    
    # Resumen de métricas
    porcentaje_pruebas_aprobadas: Optional[float] = None
    pruebas_totales: int = 0
    pruebas_aprobadas: int = 0
    maintainability_index: Optional[float] = None
    complejidad_ciclomatica_max: Optional[int] = None
    sloc: Optional[int] = None
    tiempo_promedio_ms: Optional[float] = None
    tiempo_mediano_ms: Optional[float] = None
    memoria_mediana_kb: Optional[float] = None
    
    pruebas_detalle: List[ResultadoPruebaItem] = []
    complejidad_detalle: List[ComplejidadItem] = []
    benchmark_detalle: List[BenchmarkItem] = []
