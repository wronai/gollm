# src/gollm/llm/ollama_adapter.py
import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    model: str = "codellama:7b"
    timeout: int = 60
    max_tokens: int = 4000
    temperature: float = 0.1

class OllamaAdapter:
    """Adapter dla integracji z Ollama LLM"""
    
    def __init__(self, config: OllamaConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def is_available(self) -> bool:
        """Sprawdza czy Ollama jest dostępne"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """Zwraca listę dostępnych modeli"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.config.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
        except Exception:
            pass
        return []
    
    async def generate_code(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generuje kod używając Ollama"""
        
        if not self.session:
            raise RuntimeError("OllamaAdapter not properly initialized. Use 'async with' context manager.")
        
        # Przygotuj prompt z kontekstem goLLM
        formatted_prompt = self._format_prompt_for_ollama(prompt, context or {})
        
        payload = {
            "model": self.config.model,
            "prompt": formatted_prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        try:
            async with self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Ollama API error: {response.status} - {error_text}",
                        "generated_code": "",
                        "raw_response": ""
                    }
                
                result = await response.json()
                generated_text = result.get('response', '')
                
                return {
                    "success": True,
                    "error": None,
                    "generated_code": self._extract_code_from_response(generated_text),
                    "raw_response": generated_text,
                    "model_used": self.config.model,
                    "tokens_used": result.get('eval_count', 0)
                }
                
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Timeout after {self.config.timeout} seconds",
                "generated_code": "",
                "raw_response": ""
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "generated_code": "",
                "raw_response": ""
            }
    
    def _format_prompt_for_ollama(self, user_prompt: str, context: Dict[str, Any]) -> str:
        """Formatuje prompt dla Ollama z kontekstem goLLM"""
        
        # Podstawowe informacje o kontekście
        context_info = []
        
        if context.get('project_config'):
            rules = context['project_config'].get('validation_rules', {})
            context_info.append(f"Code Quality Rules:")
            context_info.append(f"- Max function lines: {rules.get('max_function_lines', 50)}")
            context_info.append(f"- Max parameters: {rules.get('max_function_params', 5)}")
            context_info.append(f"- Require docstrings: {rules.get('require_docstrings', True)}")
            context_info.append(f"- Forbid print statements: {rules.get('forbid_print_statements', True)}")
        
        # Informacje o ostatnich błędach
        if context.get('execution_context', {}).get('last_error'):
            error = context['execution_context']['last_error']
            context_info.append(f"Recent Error: {error.get('type', 'Unknown')} - {error.get('message', '')}")
        
        # Zadania TODO
        if context.get('todo_context', {}).get('next_task'):
            task = context['todo_context']['next_task']
            context_info.append(f"Priority Task: {task.get('title', '')}")
        
        context_text = "\n".join(context_info) if context_info else "No specific context available."
        
        return f"""You are a Python code assistant focused on generating high-quality, clean code.

Project Context:
{context_text}

User Request: {user_prompt}

Requirements:
1. Generate clean, well-documented Python code
2. Follow PEP 8 style guidelines
3. Use proper logging instead of print statements
4. Keep functions focused and under 50 lines
5. Limit function parameters to 5 or fewer
6. Include comprehensive docstrings
7. Handle errors appropriately

Please provide only the Python code with brief explanation. Format your response with code blocks using ```python markers."""
    
    def _extract_code_from_response(self, response_text: str) -> str:
        """Wyodrębnia kod Python z odpowiedzi Ollama"""
        import re
        
        # Szukaj bloków kodu Python
        python_pattern = r'```python\s*\n(.*?)\n```'
        python_matches = re.findall(python_pattern, response_text, re.DOTALL)
        
        if python_matches:
            return python_matches[0].strip()
        
        # Szukaj ogólnych bloków kodu
        code_pattern = r'```\s*\n(.*?)\n```'
        code_matches = re.findall(code_pattern, response_text, re.DOTALL)
        
        if code_matches:
            # Sprawdź czy wygląda jak Python
            for code in code_matches:
                if any(keyword in code for keyword in ['def ', 'class ', 'import ', 'from ']):
                    return code.strip()
        
        # Jeśli nie ma bloków kodu, zwróć całą odpowiedź
        return response_text.strip()

class OllamaLLMProvider:
    """Provider LLM dla Ollama - kompatybilny z interfejsem goLLM"""
    
    def __init__(self, config: Dict[str, Any]):
        ollama_config = OllamaConfig(
            base_url=config.get('base_url', 'http://localhost:11434'),
            model=config.get('model_name', 'codellama:7b'),
            timeout=config.get('timeout', 60),
            max_tokens=config.get('token_limit', 4000),
            temperature=config.get('temperature', 0.1)
        )
        self.adapter = OllamaAdapter(ollama_config)
    
    async def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generuje odpowiedź kompatybilną z interfejsem goLLM LLM"""
        
        async with self.adapter as adapter:
            result = await adapter.generate_code(prompt, context)
            
            # Konwertuj do formatu oczekiwanego przez goLLM
            return {
                "generated_code": result.get("generated_code", ""),
                "explanation": "Code generated by Ollama",
                "success": result.get("success", False),
                "error": result.get("error"),
                "model_info": {
                    "provider": "ollama",
                    "model": adapter.config.model,
                    "tokens_used": result.get("tokens_used", 0)
                }
            }
    
    async def is_available(self) -> bool:
        """Sprawdza dostępność Ollama"""
        return await self.adapter.is_available()
