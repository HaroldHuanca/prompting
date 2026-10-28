"""
Servicio de construcción e interpolación de prompts experimentales.
Las técnicas comparten la misma especificación; solo cambia el tratamiento asignado.
"""
import ast
from typing import Dict, Any, List

PROMPT_TEMPLATE_VERSION = "2"


def format_ejemplos_enunciado(ejemplos: List[Dict[str, Any]]) -> str:
    """Formatea los ejemplos oficiales del enunciado del problema."""
    if not ejemplos:
        return "No se especifican ejemplos adicionales en el enunciado."

    formatted = []
    for i, ej in enumerate(ejemplos, 1):
        line = f"Ejemplo {i}:\n  Entrada: {ej.get('entrada', '')}\n  Salida: {ej.get('salida', '')}"
        if ej.get("explicacion"):
            line += f"\n  Explicación: {ej['explicacion']}"
        formatted.append(line)
    return "\n\n".join(formatted)


def format_ejemplos_few_shot(ejemplos: List[Dict[str, Any]]) -> str:
    """Formatea demostraciones resueltas reservadas para Few-Shot."""
    formatted = []
    for i, ej in enumerate(ejemplos, 1):
        desc = ej.get("descripcion", f"Demostración {i}")
        line = [f"--- Demostración {i}: {desc} ---"]
        line.append(f"Entrada: {ej.get('entrada', '')}")
        line.append(f"Salida: {ej.get('salida', '')}")
        if ej.get("explicacion"):
            line.append(f"Explicación: {ej['explicacion']}")
        if ej.get("codigo_ilustrativo"):
            line.append(f"Implementación ilustrativa:\n```python\n{ej['codigo_ilustrativo']}\n```")
        formatted.append("\n".join(line))
    return "\n\n".join(formatted)


def _format_solution_interface(solution: str) -> str:
    """Obtiene nombres y parámetros públicos desde la solución de referencia."""
    if not solution:
        return "Implementa la clase y el método requeridos por el enunciado."

    try:
        tree = ast.parse(solution)
    except SyntaxError:
        return "Implementa la clase y el método requeridos por el enunciado."

    classes = [node for node in tree.body if isinstance(node, ast.ClassDef)]
    selected = next((node for node in classes if node.name == "Solution"), None)
    if selected is None and classes:
        selected = classes[0]
    if selected is None:
        return "Implementa la clase y el método requeridos por el enunciado."

    methods = []
    for node in selected.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        args = [arg.arg for arg in node.args.args]
        if args and args[0] in {"self", "cls"}:
            args = args[1:]
        methods.append(f"{node.name}({', '.join(args)})")

    class_label = f"class {selected.name}"
    if not methods:
        return class_label
    return f"{class_label} con los métodos: {', '.join(methods)}"


def build_prompt(problema: Dict[str, Any], tecnica_codigo: str) -> Dict[str, Any]:
    """Construye el prompt formal con contenido común y una sola variable de tratamiento."""
    codigo_tec = tecnica_codigo.upper().strip()
    titulo = problema.get("titulo", "Problema Algorítmico")
    dificultad = problema.get("dificultad", "Media")
    categoria = problema.get("categoria_algoritmica", "General")
    enunciado = problema.get("enunciado", "")
    restricciones = problema.get("restricciones", "No especificadas.")
    interfaz = _format_solution_interface(problema.get("solucion_referencia", ""))
    ejemplos_enunciado = format_ejemplos_enunciado(problema.get("ejemplos_enunciado", []))
    ejemplos_few_shot = problema.get("ejemplos_few_shot", [])

    treatments = {
        "ZERO_SHOT": "",
        "FEW_SHOT": "",
        "CHAIN_OF_THOUGHT": (
            "Tratamiento Chain-of-Thought: analiza paso a paso el algoritmo, los casos borde "
            "y su complejidad antes de responder. Mantén ese análisis fuera de la respuesta "
            "final, que debe contener únicamente el código solicitado."
        ),
        "ROLE_PROMPTING": (
            "Tratamiento Role Prompting: adopta el rol de una persona ingeniera de software "
            "experta en algoritmos y Python 3."
        ),
    }
    if codigo_tec not in treatments:
        raise ValueError(f"Técnica de prompt desconocida: {tecnica_codigo}")
    if codigo_tec == "FEW_SHOT" and not ejemplos_few_shot:
        raise ValueError("FEW_SHOT requiere al menos una demostración real.")

    treatment = treatments[codigo_tec]
    prompt_sections = []
    if codigo_tec == "FEW_SHOT":
        prompt_sections.append(
            "Tratamiento Few-Shot: usa las siguientes demostraciones como ejemplos "
            "de entrada, salida y estilo de solución. No copies su implementación "
            "si el problema actual requiere otro algoritmo."
        )
        prompt_sections.append(format_ejemplos_few_shot(ejemplos_few_shot))
    elif treatment:
        prompt_sections.append(treatment)

    prompt_sections.append(f"""Resuelve el siguiente problema en Python 3.

Título: {titulo}
Dificultad: {dificultad}
Categoría: {categoria}

Interfaz requerida:
{interfaz}

Especificación de entrada: {problema.get("especificacion_entrada") or "Según el enunciado."}
Especificación de salida: {problema.get("especificacion_salida") or "Según el enunciado."}

Enunciado:
{enunciado}

Restricciones:
{restricciones}

Ejemplos oficiales:
{ejemplos_enunciado}

Instrucciones comunes:
1. Implementa exactamente la interfaz indicada y resuelve los casos borde.
2. Usa una solución correcta y eficiente conforme a las restricciones.
3. Devuelve únicamente código Python ejecutable en un bloque ```python ... ```.
4. No incluyas texto, comentarios ni explicaciones fuera del código.""")

    return {
        "tecnica_codigo": codigo_tec,
        "version": PROMPT_TEMPLATE_VERSION,
        "prompt": "\n\n".join(prompt_sections).strip(),
        "variables": {
            "titulo": titulo,
            "dificultad": dificultad,
            "categoria": categoria,
            "interfaz": interfaz,
            "cantidad_ejemplos_few_shot": len(ejemplos_few_shot) if codigo_tec == "FEW_SHOT" else 0,
        },
    }
