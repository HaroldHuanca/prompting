"""
Servicio de extracción, limpieza automatizada, verificación sintáctica (AST)
y hashing criptográfico SHA-256 para el código generado por LLM.
"""
import ast
import hashlib
import re
from typing import Tuple

def clean_code_block(raw_text: str) -> Tuple[str, bool, str]:
    """
    Limpia y extrae el bloque de código Python de la respuesta cruda de ChatGPT-4o.
    
    Retorna:
        Tuple[str, bool, str]:
        - codigo_limpio: Código Python aislado sin marcas de markdown ni preámbulos.
        - codigo_parseable: True si la sintaxis es válida según ast.parse().
        - hash_sha256: Hash criptográfico SHA-256 de 64 caracteres hexadecimales.
    """
    if not raw_text or not raw_text.strip():
        empty_hash = hashlib.sha256(b"").hexdigest()
        return "", False, empty_hash

    # Estrategia 1: Buscar bloques explícitos ```python ... ```
    match_python = re.search(r"```(?:python|py)\s*\n(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if match_python:
        code = match_python.group(1).strip()
    else:
        # Estrategia 2: Buscar bloques genéricos ``` ... ```
        match_generic = re.search(r"```\s*\n(.*?)```", raw_text, re.DOTALL)
        if match_generic:
            code = match_generic.group(1).strip()
        else:
            # Estrategia 3: Si no hay delimitadores, buscar inicio de clase o función
            lines = raw_text.splitlines()
            code_lines = []
            capturing = False
            for line in lines:
                if re.match(r"^\s*(?:class\s+|def\s+|import\s+|from\s+)", line):
                    capturing = True
                if capturing:
                    code_lines.append(line)
            
            code = "\n".join(code_lines).strip() if code_lines else raw_text.strip()

    # Remover cualquier remanente de backticks si quedaron en extremos
    code = re.sub(r"^```[a-zA-Z]*\n?", "", code).strip()
    code = re.sub(r"\n?```$", "", code).strip()

    # Si contiene saltos de línea literales escapados \\n sin saltos reales
    if "\n" not in code and "\\n" in code:
        code = code.replace("\\n", "\n").replace("\\t", "    ")

    # Validar parseabilidad sintáctica mediante ast.parse()
    is_parseable = False
    try:
        ast.parse(code)
        is_parseable = True
    except SyntaxError:
        is_parseable = False

    # Calcular SHA-256 sobre el código limpio normalizado
    sha256_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

    return code, is_parseable, sha256_hash
