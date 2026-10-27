"""
Servicio de construcción e interpolación de prompts experimentales.
Soporta las 4 técnicas canónicas de la tesis:
1. ZERO_SHOT
2. FEW_SHOT
3. CHAIN_OF_THOUGHT
4. ROLE_PROMPTING
"""
import json
from typing import Dict, Any, List

def format_ejemplos_enunciado(ejemplos: List[Dict[str, Any]]) -> str:
    """Formatea los ejemplos oficiales del enunciado del problema."""
    if not ejemplos:
        return "No se especifican ejemplos adicionales en el enunciado."
    
    formatted = []
    for i, ej in enumerate(ejemplos, 1):
        line = f"Ejemplo {i}:\n  Entrada: {ej.get('entrada', '')}\n  Salida: {ej.get('salida', '')}"
        if ej.get('explicacion'):
            line += f"\n  Explicación: {ej['explicacion']}"
        formatted.append(line)
    return "\n\n".join(formatted)

def format_ejemplos_few_shot(ejemplos: List[Dict[str, Any]]) -> str:
    """
    Formatea las demostraciones resueltas para inyección exclusiva en la técnica Few-Shot.
    Diferenciado estrictamente de los ejemplos del enunciado.
    """
    if not ejemplos:
        return "Demostración de referencia genérica:\nEntrada: Caso de prueba elemental\nSalida: Resultado esperado"
    
    formatted = []
    for i, ej in enumerate(ejemplos, 1):
        desc = ej.get('descripcion', f'Demostración {i}')
        line = [f"--- Demostración {i}: {desc} ---"]
        line.append(f"Entrada: {ej.get('entrada', '')}")
        line.append(f"Salida: {ej.get('salida', '')}")
        if ej.get('explicacion'):
            line.append(f"Razonamiento: {ej['explicacion']}")
        if ej.get('codigo_ilustrativo'):
            line.append(f"Implementación ilustrativa:\n```python\n{ej['codigo_ilustrativo']}\n```")
        formatted.append("\n".join(line))
    return "\n\n".join(formatted)

def build_prompt(problema: Dict[str, Any], tecnica_codigo: str) -> Dict[str, Any]:
    """
    Construye el prompt formal según el problema y la técnica seleccionada.
    """
    codigo_tec = tecnica_codigo.upper().strip()
    titulo = problema.get("titulo", "Problema Algorítmico")
    dificultad = problema.get("dificultad", "Media")
    categoria = problema.get("categoria_algoritmica", "General")
    enunciado = problema.get("enunciado", "")
    restricciones = problema.get("restricciones", "Restricciones estándar de LeetCode.")
    
    ejemplos_enunciado_str = format_ejemplos_enunciado(problema.get("ejemplos_enunciado", []))
    ejemplos_few_shot_str = format_ejemplos_few_shot(problema.get("ejemplos_few_shot", []))

    if codigo_tec == "ZERO_SHOT":
        prompt_text = f"""Escribe una solución en Python 3 para el siguiente problema algorítmico:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales del enunciado:
{ejemplos_enunciado_str}

Instrucciones de formato:
1. Proporciona una solución limpia, correcta y eficiente en Python 3.
2. Encapsula la solución dentro de la clase Solution y el método correspondiente.
3. Responde únicamente con el bloque de código Python entre comillas triples ```python ... ``` sin texto explicativo adicional."""

    elif codigo_tec == "FEW_SHOT":
        prompt_text = f"""A continuación se presentan ejemplos de demostración resueltos para ilustrar el estilo y la calidad de implementación esperada:

{ejemplos_few_shot_str}

Ahora, resuelve el siguiente problema algorítmico en Python 3 siguiendo el mismo estándar de rigor:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales del enunciado:
{ejemplos_enunciado_str}

Instrucciones de formato:
1. Proporciona una solución limpia, modular y eficiente en Python 3 dentro de la clase Solution.
2. Responde únicamente con el bloque de código Python entre comillas triples ```python ... ``` sin texto adicional posterior."""

    elif codigo_tec == "CHAIN_OF_THOUGHT":
        prompt_text = f"""Analiza y resuelve paso a paso el siguiente problema algorítmico en Python 3:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales:
{ejemplos_enunciado_str}

Estructura de razonamiento requerida:
Paso 1: Comprensión del problema y análisis de casos borde (edge cases).
Paso 2: Análisis de complejidad temporal y espacial teórica requerida.
Paso 3: Diseño algorítmico y selección de estructuras de datos adecuadas.
Paso 4: Implementación del código final optimizado dentro de la clase Solution.

Al final, entrega la implementación definitiva encerrada en un bloque de código Markdown ```python ... ```."""

    elif codigo_tec == "ROLE_PROMPTING":
        prompt_text = f"""Eres un Ingeniero de Software Principal y especialista en algoritmos avanzados de estructuras de datos y optimización de código en Python. Tu código se caracteriza por:
- Máxima claridad y legibilidad (alta mantenibilidad y bajo acoplamiento).
- Baja complejidad ciclomática por función.
- Eficiencia óptima en tiempo de ejecución O(n) o subcuadrático y uso disciplinado de memoria.
- Riguroso manejo de precondiciones y restricciones.

Resuelve el siguiente problema con los más altos estándares de calidad de la industria:

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales:
{ejemplos_enunciado_str}

Entrega el código Python definitivo encapsulado en un bloque ```python ... ``` dentro de la clase Solution."""

    else:
        raise ValueError(f"Técnica de prompt desconocida: {tecnica_codigo}")

    return {
        "tecnica_codigo": codigo_tec,
        "prompt": prompt_text.strip(),
        "variables": {
            "titulo": titulo,
            "dificultad": dificultad,
            "categoria": categoria,
            "cantidad_ejemplos_few_shot": len(problema.get("ejemplos_few_shot", []))
        }
    }
