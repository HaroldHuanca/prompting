"""
Pruebas unitarias para el servicio de extracción de código clean_code_block.
"""
import pytest
from backend.services.code_extractor import clean_code_block

def test_clean_code_block_python_markdown():
    raw = """
Aquí tienes la solución solicitada:

```python
class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, n in enumerate(nums):
            if target - n in seen:
                return [seen[target - n], i]
            seen[n] = i
        return []
```

Esta solución tiene una complejidad O(n).
"""
    code, is_parseable, sha256_hash = clean_code_block(raw)
    assert "class Solution:" in code
    assert "def twoSum" in code
    assert "Aquí tienes la solución" not in code
    assert "Esta solución tiene una complejidad" not in code
    assert is_parseable is True
    assert len(sha256_hash) == 64

def test_clean_code_block_generic_backticks():
    raw = """```
class Solution:
    def solve(self):
        return True
```"""
    code, is_parseable, sha256_hash = clean_code_block(raw)
    assert code == "class Solution:\n    def solve(self):\n        return True"
    assert is_parseable is True
    assert len(sha256_hash) == 64

def test_clean_code_block_syntax_error():
    raw = """```python
def invalid_syntax(
    return 123
```"""
    code, is_parseable, sha256_hash = clean_code_block(raw)
    assert is_parseable is False
    assert len(sha256_hash) == 64

def test_clean_code_block_empty():
    code, is_parseable, sha256_hash = clean_code_block("")
    assert code == ""
    assert is_parseable is False
    assert len(sha256_hash) == 64
