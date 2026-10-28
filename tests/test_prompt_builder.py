"""
Pruebas unitarias para el constructor de prompts y segregación de ejemplos.
"""
import pytest
from backend.services.prompt_builder import build_prompt

@pytest.fixture
def sample_problem():
    return {
        "titulo": "Two Sum",
        "dificultad": "Fácil",
        "categoria_algoritmica": "Arreglos y Hash Table",
        "enunciado": "Dado un arreglo nums y un target, retorna los índices.",
        "restricciones": "2 <= nums.length <= 10^4",
        "ejemplos_enunciado": [
            {"entrada": "nums = [2,7,11,15], target = 9", "salida": "[0,1]", "explicacion": "nums[0]+nums[1]==9"}
        ],
        "ejemplos_few_shot": [
            {
                "id": 1,
                "descripcion": "Demostración Hash Map",
                "entrada": "nums = [3,2,4], target = 6",
                "salida": "[1,2]",
                "explicacion": "Búsqueda en O(1)",
                "codigo_ilustrativo": "def twoSum(nums, target): return [1, 2]"
            }
        ],
        "solucion_referencia": "class Solution:\n    def twoSum(self, nums, target):\n        return []",
        "pruebas_funcionales": []
    }

def test_prompt_builder_zero_shot(sample_problem):
    res = build_prompt(sample_problem, "ZERO_SHOT")
    prompt = res["prompt"]
    assert res["version"] == "2"
    assert "Two Sum" in prompt
    assert "Fácil" in prompt
    # Debe tener ejemplos de enunciado
    assert "nums = [2,7,11,15]" in prompt
    assert "twoSum(nums, target)" in prompt
    # NO DEBE incluir las demostraciones de few-shot (Regla de Integridad)
    assert "Demostración Hash Map" not in prompt
    assert "Búsqueda en O(1)" not in prompt

def test_prompt_builder_few_shot(sample_problem):
    res = build_prompt(sample_problem, "FEW_SHOT")
    prompt = res["prompt"]
    assert "Two Sum" in prompt
    # DEBE incluir la sección de demostraciones Few-Shot
    assert "Demostración Hash Map" in prompt
    assert "Búsqueda en O(1)" in prompt
    assert "nums = [3,2,4]" in prompt
    # También debe incluir los ejemplos del enunciado del problema a resolver
    assert "nums = [2,7,11,15]" in prompt

def test_prompt_builder_chain_of_thought(sample_problem):
    res = build_prompt(sample_problem, "CHAIN_OF_THOUGHT")
    prompt = res["prompt"]
    assert "analiza paso a paso" in prompt.lower()
    assert "fuera de la respuesta final" in prompt.lower()
    assert "únicamente código" in prompt.lower()
    # NO DEBE incluir demostraciones de few-shot
    assert "Demostración Hash Map" not in prompt

def test_prompt_builder_role_prompting(sample_problem):
    res = build_prompt(sample_problem, "ROLE_PROMPTING")
    prompt = res["prompt"]
    assert "rol de una persona ingeniera de software" in prompt.lower()
    # NO DEBE incluir demostraciones de few-shot
    assert "Demostración Hash Map" not in prompt


def test_prompt_builder_uses_same_problem_specification(sample_problem):
    prompts = [
        build_prompt(sample_problem, technique)["prompt"]
        for technique in ("ZERO_SHOT", "FEW_SHOT", "CHAIN_OF_THOUGHT", "ROLE_PROMPTING")
    ]
    common_sections = [prompt[prompt.index("Resuelve el siguiente problema"): ] for prompt in prompts]
    assert len(set(common_sections)) == 1


def test_prompt_builder_rejects_missing_few_shot_demo(sample_problem):
    sample_problem["ejemplos_few_shot"] = []
    with pytest.raises(ValueError, match="al menos una demostración real"):
        build_prompt(sample_problem, "FEW_SHOT")
