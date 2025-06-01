
# src/gollm/llm/response_validator.py
import re
import ast
from typing import Dict, Any, List, Optional

class ResponseValidator:
    """Waliduje odpowiedzi z LLM"""
    
    def __init__(self, config):
        self.config = config
    
    async def validate_response(self, llm_output: str) -> Dict[str, Any]:
        """Waliduje odpowiedź z LLM"""
        
        validation_result = {
            "raw_output": llm_output,
            "code_extracted": False,
            "extracted_code": "",
            "explanation": "",
            "code_blocks_found": 0,
            "syntax_valid": False,
            "violations": []
        }
        
        # 1. Wyodrębnij bloki kodu
        code_blocks = self._extract_code_blocks(llm_output)
        validation_result["code_blocks_found"] = len(code_blocks)
        
        if code_blocks:
            validation_result["code_extracted"] = True
            validation_result["extracted_code"] = code_blocks[0]  # Pierwszy blok
            
            # 2. Sprawdź składnię
            syntax_check = self._validate_syntax(code_blocks[0])
            validation_result["syntax_valid"] = syntax_check["valid"]
            if not syntax_check["valid"]:
                validation_result["violations"].append({
                    "type": "syntax_error",
                    "message": syntax_check["error"]
                })
        
        # 3. Wyodrębnij wyjaśnienie
        validation_result["explanation"] = self._extract_explanation(llm_output)
        
        return validation_result
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Wyodrębnia bloki kodu z odpowiedzi LLM"""
        
        # Szukaj bloków ```python ... ```
        python_pattern = r'```python\s*\n(.*?)\n```'
        python_blocks = re.findall(python_pattern, text, re.DOTALL)
        
        if python_blocks:
            return [block.strip() for block in python_blocks]
        
        # Szukaj ogólnych bloków ``` ... ```
        general_pattern = r'```\s*\n(.*?)\n```'
        general_blocks = re.findall(general_pattern, text, re.DOTALL)
        
        if general_blocks:
            # Filtruj bloki które wyglądają jak Python
            python_like = []
            for block in general_blocks:
                if self._looks_like_python(block):
                    python_like.append(block.strip())
            return python_like
        
        return []
    
    def _looks_like_python(self, code: str) -> bool:
        """Sprawdza czy kod wygląda jak Python"""
        python_keywords = ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ']
        
        return any(keyword in code for keyword in python_keywords)
    
    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """Sprawdza składnię Python"""
        try:
            ast.parse(code)
            return {"valid": True, "error": None}
        except SyntaxError as e:
            return {"valid": False, "error": f"Syntax error: {e.msg} at line {e.lineno}"}
        except Exception as e:
            return {"valid": False, "error": f"Parse error: {str(e)}"}
    
    def _extract_explanation(self, text: str) -> str:
        """Wyodrębnia wyjaśnienie z odpowiedzi LLM"""
        
        # Usuń bloki kodu
        text_without_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Wyczyść i zwróć
        explanation = text_without_code.strip()
        
        # Ogranicz długość
        if len(explanation) > 500:
            explanation = explanation[:497] + "..."
        
        return explanation