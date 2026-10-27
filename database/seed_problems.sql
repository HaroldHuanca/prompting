-- ============================================================================
-- SEED DE PROBLEMAS LEETCODE CON SEGREGACIÓN RIGUROSA:
-- 1. ejemplos_enunciado: Ejemplos oficiales del enunciado.
-- 2. ejemplos_few_shot: Demostraciones reservadas para técnica Few-Shot.
-- 3. pruebas_funcionales: Casos de prueba automatizados ejecutables en Pytest.
-- ============================================================================

BEGIN;

SET search_path TO experimento, public;

-- Problema 1: Two Sum
INSERT INTO problema (
    codigo, titulo, plataforma_origen, url_referencia, dificultad, categoria_algoritmica,
    enunciado, especificacion_entrada, especificacion_salida, restricciones,
    ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
    solucion_referencia, pruebas_funcionales, etiquetas
) VALUES (
    'LC-001',
    'Two Sum',
    'LeetCode',
    'https://leetcode.com/problems/two-sum/',
    'Fácil',
    'Arreglos y Hash Table',
    'Dado un arreglo de números enteros `nums` y un entero `target`, retorna los índices de los dos números tales que sumen `target`.\nPuedes asumir que cada entrada tendrá exactamente una solución, y no puedes usar el mismo elemento dos veces.\nPuedes retornar la respuesta en cualquier orden.',
    'nums: List[int], target: int',
    'List[int] con los dos índices',
    '2 <= nums.length <= 10^4\n-10^9 <= nums[i] <= 10^9\n-10^9 <= target <= 10^9\nExiste exactamente una solución válida.',
    '[
        {"entrada": "nums = [2,7,11,15], target = 9", "salida": "[0,1]", "explicacion": "nums[0] + nums[1] == 9, por tanto retornamos [0, 1]."},
        {"entrada": "nums = [3,3], target = 6", "salida": "[0,1]", "explicacion": "nums[0] + nums[1] == 6."}
    ]'::jsonb,
    '[
        {
            "id": 1,
            "descripcion": "Demostración con diccionario para búsqueda O(1)",
            "entrada": "nums = [3,2,4], target = 6",
            "salida": "[1,2]",
            "explicacion": "Calculamos el complemento diff = target - n y verificamos si existe en el hash map visto."
        }
    ]'::jsonb,
    1,
$SOL$class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        seen = {}
        for i, num in enumerate(nums):
            comp = target - num
            if comp in seen:
                return [seen[comp], i]
            seen[num] = i
        return []$SOL$,
    '[
        {"nombre": "test_caso_base", "codigo": "assert Solution().twoSum([2, 7, 11, 15], 9) in [[0, 1], [1, 0]]"},
        {"nombre": "test_caso_indices_consecutivos", "codigo": "assert Solution().twoSum([3, 2, 4], 6) in [[1, 2], [2, 1]]"},
        {"nombre": "test_caso_duplicados", "codigo": "assert Solution().twoSum([3, 3], 6) in [[0, 1], [1, 0]]"},
        {"nombre": "test_caso_negativos", "codigo": "assert Solution().twoSum([-1, -2, -3, -4, -5], -8) in [[2, 4], [4, 2]]"},
        {"nombre": "test_caso_cero", "codigo": "assert Solution().twoSum([0, 4, 3, 0], 0) in [[0, 3], [3, 0]]"}
    ]'::jsonb,
    ARRAY['array', 'hash-table', 'leetcode-easy']
)
ON CONFLICT (codigo) DO UPDATE SET
    titulo = EXCLUDED.titulo,
    enunciado = EXCLUDED.enunciado,
    ejemplos_enunciado = EXCLUDED.ejemplos_enunciado,
    ejemplos_few_shot = EXCLUDED.ejemplos_few_shot,
    cantidad_ejemplos_few_shot = EXCLUDED.cantidad_ejemplos_few_shot,
    solucion_referencia = EXCLUDED.solucion_referencia,
    pruebas_funcionales = EXCLUDED.pruebas_funcionales;

-- Problema 2: Valid Parentheses
INSERT INTO problema (
    codigo, titulo, plataforma_origen, url_referencia, dificultad, categoria_algoritmica,
    enunciado, especificacion_entrada, especificacion_salida, restricciones,
    ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
    solucion_referencia, pruebas_funcionales, etiquetas
) VALUES (
    'LC-020',
    'Valid Parentheses',
    'LeetCode',
    'https://leetcode.com/problems/valid-parentheses/',
    'Fácil',
    'Pilas y Cadenas',
    'Dada una cadena `s` que contiene solo los caracteres ''('', '')'', ''{'', ''}'', ''['' y '']'', determina si la cadena de entrada es válida.\nUna cadena de entrada es válida si:\n1. Los paréntesis abiertos se cierran con el mismo tipo de paréntesis.\n2. Los paréntesis abiertos se cierran en el orden correcto.\n3. Cada paréntesis cerrado tiene un paréntesis abierto correspondiente del mismo tipo.',
    's: str',
    'bool indicando validez',
    '1 <= s.length <= 10^4\ns consiste únicamente de ''()[]{}''.',
    '[
        {"entrada": "s = \"()\"", "salida": "true", "explicacion": "Paréntesis coincidente simple."},
        {"entrada": "s = \"()[]{}\"", "salida": "true", "explicacion": "Múltiples parejas consecutivas."},
        {"entrada": "s = \"(]\"", "salida": "false", "explicacion": "Cierre incorrecto."}
    ]'::jsonb,
    '[
        {
            "id": 1,
            "descripcion": "Demostración de estructura de Pila (LIFO)",
            "entrada": "s = \"{[]}\"",
            "salida": "true",
            "explicacion": "Apilamos los de apertura. Al encontrar un cierre, desapilamos y validamos correspondencia de tipos."
        }
    ]'::jsonb,
    1,
$SOL$class Solution:
    def isValid(self, s: str) -> bool:
        mapping = {")": "(", "}": "{", "]": "["}
        stack = []
        for char in s:
            if char in mapping:
                top = stack.pop() if stack else "#"
                if mapping[char] != top:
                    return False
            else:
                stack.append(char)
        return not stack$SOL$,
    '[
        {"nombre": "test_par_simple", "codigo": "assert Solution().isValid(\"()\") is True"},
        {"nombre": "test_multiples_tipos", "codigo": "assert Solution().isValid(\"()[]{}\") is True"},
        {"nombre": "test_cierre_incorrecto", "codigo": "assert Solution().isValid(\"(]\") is False"},
        {"nombre": "test_anidado_correcto", "codigo": "assert Solution().isValid(\"([{}])\") is True"},
        {"nombre": "test_cadena_impar", "codigo": "assert Solution().isValid(\"[\") is False"},
        {"nombre": "test_cierre_inicial", "codigo": "assert Solution().isValid(\"]\") is False"}
    ]'::jsonb,
    ARRAY['string', 'stack', 'leetcode-easy']
)
ON CONFLICT (codigo) DO UPDATE SET
    titulo = EXCLUDED.titulo,
    enunciado = EXCLUDED.enunciado,
    ejemplos_enunciado = EXCLUDED.ejemplos_enunciado,
    ejemplos_few_shot = EXCLUDED.ejemplos_few_shot,
    cantidad_ejemplos_few_shot = EXCLUDED.cantidad_ejemplos_few_shot,
    solucion_referencia = EXCLUDED.solucion_referencia,
    pruebas_funcionales = EXCLUDED.pruebas_funcionales;

-- Problema 3: Longest Substring Without Repeating Characters
INSERT INTO problema (
    codigo, titulo, plataforma_origen, url_referencia, dificultad, categoria_algoritmica,
    enunciado, especificacion_entrada, especificacion_salida, restricciones,
    ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
    solucion_referencia, pruebas_funcionales, etiquetas
) VALUES (
    'LC-003',
    'Longest Substring Without Repeating Characters',
    'LeetCode',
    'https://leetcode.com/problems/longest-substring-without-repeating-characters/',
    'Media',
    'Ventana Deslizante y Cadenas',
    'Dada una cadena `s`, encuentra la longitud de la subcadena más larga sin caracteres repetidos.',
    's: str',
    'int con la longitud máxima',
    '0 <= s.length <= 5 * 10^4\ns consiste de letras en inglés, dígitos, símbolos y espacios.',
    '[
        {"entrada": "s = \"abcabcbb\"", "salida": "3", "explicacion": "La respuesta es \"abc\", con longitud 3."},
        {"entrada": "s = \"bbbbb\"", "salida": "1", "explicacion": "La respuesta es \"b\", con longitud 1."}
    ]'::jsonb,
    '[
        {
            "id": 1,
            "descripcion": "Demostración de Ventana Deslizante con diccionario de últimas posiciones",
            "entrada": "s = \"pwwkew\"",
            "salida": "3",
            "explicacion": "La subcadena es \"wke\", con longitud 3. Nótese que \"pwke\" no es subcadena sino subsecuencia."
        }
    ]'::jsonb,
    1,
$SOL$class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        char_map = {}
        left = 0
        max_len = 0
        for right, char in enumerate(s):
            if char in char_map and char_map[char] >= left:
                left = char_map[char] + 1
            char_map[char] = right
            max_len = max(max_len, right - left + 1)
        return max_len$SOL$,
    '[
        {"nombre": "test_cadena_vacia", "codigo": "assert Solution().lengthOfLongestSubstring(\"\") == 0"},
        {"nombre": "test_un_solo_caracter", "codigo": "assert Solution().lengthOfLongestSubstring(\"a\") == 1"},
        {"nombre": "test_todos_repetidos", "codigo": "assert Solution().lengthOfLongestSubstring(\"bbbbb\") == 1"},
        {"nombre": "test_clasico_abc", "codigo": "assert Solution().lengthOfLongestSubstring(\"abcabcbb\") == 3"},
        {"nombre": "test_espacios_y_simbolos", "codigo": "assert Solution().lengthOfLongestSubstring(\"a b c a\") == 3"},
        {"nombre": "test_cadena_dvdf", "codigo": "assert Solution().lengthOfLongestSubstring(\"dvdf\") == 3"}
    ]'::jsonb,
    ARRAY['string', 'sliding-window', 'hash-table', 'leetcode-medium']
)
ON CONFLICT (codigo) DO UPDATE SET
    titulo = EXCLUDED.titulo,
    enunciado = EXCLUDED.enunciado,
    ejemplos_enunciado = EXCLUDED.ejemplos_enunciado,
    ejemplos_few_shot = EXCLUDED.ejemplos_few_shot,
    cantidad_ejemplos_few_shot = EXCLUDED.cantidad_ejemplos_few_shot,
    solucion_referencia = EXCLUDED.solucion_referencia,
    pruebas_funcionales = EXCLUDED.pruebas_funcionales;

-- Problema 4: Coin Change
INSERT INTO problema (
    codigo, titulo, plataforma_origen, url_referencia, dificultad, categoria_algoritmica,
    enunciado, especificacion_entrada, especificacion_salida, restricciones,
    ejemplos_enunciado, ejemplos_few_shot, cantidad_ejemplos_few_shot,
    solucion_referencia, pruebas_funcionales, etiquetas
) VALUES (
    'LC-322',
    'Coin Change',
    'LeetCode',
    'https://leetcode.com/problems/coin-change/',
    'Media',
    'Programación Dinámica',
    'Se te da un arreglo de enteros `coins` que representan monedas de diferentes denominaciones y un entero `amount` que representa una cantidad total de dinero.\nRetorna el menor número de monedas que necesitas para completar esa cantidad. Si esa cantidad de dinero no puede ser completada por ninguna combinación de las monedas, retorna `-1`.\nPuedes asumir que tienes un número infinito de cada tipo de moneda.',
    'coins: List[int], amount: int',
    'int con el número mínimo de monedas o -1',
    '1 <= coins.length <= 12\n1 <= coins[i] <= 2^31 - 1\n0 <= amount <= 10^4',
    '[
        {"entrada": "coins = [1,2,5], amount = 11", "salida": "3", "explicacion": "11 = 5 + 5 + 1"},
        {"entrada": "coins = [2], amount = 3", "salida": "-1", "explicacion": "No es posible formar 3 con monedas de 2."}
    ]'::jsonb,
    '[
        {
            "id": 1,
            "descripcion": "Demostración de Enfoque Bottom-Up (Tabulación DP)",
            "entrada": "coins = [1], amount = 0",
            "salida": "0",
            "explicacion": "Para una cantidad de 0, se requieren 0 monedas."
        }
    ]'::jsonb,
    1,
$SOL$class Solution:
    def coinChange(self, coins: list[int], amount: int) -> int:
        dp = [float("inf")] * (amount + 1)
        dp[0] = 0
        for c in coins:
            for i in range(c, amount + 1):
                dp[i] = min(dp[i], dp[i - c] + 1)
        return dp[amount] if dp[amount] != float("inf") else -1$SOL$,
    '[
        {"nombre": "test_monto_cero", "codigo": "assert Solution().coinChange([1, 2, 5], 0) == 0"},
        {"nombre": "test_caso_clasico_11", "codigo": "assert Solution().coinChange([1, 2, 5], 11) == 3"},
        {"nombre": "test_imposible", "codigo": "assert Solution().coinChange([2], 3) == -1"},
        {"nombre": "test_moneda_exacta", "codigo": "assert Solution().coinChange([5], 5) == 1"},
        {"nombre": "test_monedas_grandes", "codigo": "assert Solution().coinChange([186, 419, 83, 408], 6249) == 20"}
    ]'::jsonb,
    ARRAY['dynamic-programming', 'leetcode-medium']
)
ON CONFLICT (codigo) DO UPDATE SET
    titulo = EXCLUDED.titulo,
    enunciado = EXCLUDED.enunciado,
    ejemplos_enunciado = EXCLUDED.ejemplos_enunciado,
    ejemplos_few_shot = EXCLUDED.ejemplos_few_shot,
    cantidad_ejemplos_few_shot = EXCLUDED.cantidad_ejemplos_few_shot,
    solucion_referencia = EXCLUDED.solucion_referencia,
    pruebas_funcionales = EXCLUDED.pruebas_funcionales;

COMMIT;
