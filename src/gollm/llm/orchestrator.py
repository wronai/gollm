# src/gollm/llm/orchestrator.py
import asyncio
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .context_builder import ContextBuilder
from .prompt_formatter import PromptFormatter
from .response_validator import ResponseValidator
from ..validation.validators import CodeValidator

@dataclass
class LLMRequest:
    user_request: str
    context: Dict[str, Any]
    session_id: str
    max_iterations: int = 3

@dataclass
class LLMResponse:
    generated_code: str
    explanation: str
    validation_result: Dict[str, Any]
    iterations_used: int
    quality_score: int

class LLMOrchestrator:
    """Orkiestruje komunikację z LLM i zarządza kontekstem"""
    
    def __init__(self, config):
        self.config = config
        self.context_builder = ContextBuilder(config)
        self.prompt_formatter = PromptFormatter(config)
        self.response_validator = ResponseValidator(config)
        self.code_validator = CodeValidator(config)
    
    async def handle_code_generation_request(self, user_request: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Główny punkt wejścia dla generowania kodu przez LLM"""
        
        if context is None:
            context = {}
        
        session_id = context.get('session_id', f"session-{asyncio.get_event_loop().time()}")
        
        request = LLMRequest(
            user_request=user_request,
            context=context,
            session_id=session_id,
            max_iterations=self.config.llm_integration.max_iterations
        )
        
        return await self._process_llm_request(request)
    
    async def _process_llm_request(self, request: LLMRequest) -> LLMResponse:
        """Przetwarza żądanie LLM z iteracjami i walidacją"""
        
        # 1. Przygotuj pełny kontekst
        full_context = await self.context_builder.build_context(request.context)
        
        # 2. Iteracyjne generowanie kodu
        best_response = None
        best_score = 0
        
        for iteration in range(request.max_iterations):
            # Sformatuj prompt
            prompt = self.prompt_formatter.create_prompt(
                request.user_request, 
                full_context, 
                iteration=iteration,
                previous_attempt=best_response
            )
            
            # Symulacja wywołania LLM (w rzeczywistej implementacji tutaj byłby prawdziwy API call)
            llm_output = await self._simulate_llm_call(prompt)
            
            # Waliduj odpowiedź
            validation_result = await self.response_validator.validate_response(llm_output)
            
            # Sprawdź jakość kodu
            if validation_result['code_extracted']:
                code_validation = self.code_validator.validate_content(
                    validation_result['extracted_code'], 
                    "generated_code.py"
                )
                validation_result['code_quality'] = code_validation
            
            # Oceń wynik
            current_score = self._calculate_response_score(validation_result)
            
            if current_score > best_score:
                best_score = current_score
                best_response = {
                    'generated_code': validation_result.get('extracted_code', ''),
                    'explanation': validation_result.get('explanation', ''),
                    'validation_result': validation_result,
                    'iteration': iteration + 1
                }
            
            # Jeśli osiągnęliśmy wystarczającą jakość, przerwij
            if current_score >= 90:  # 90% jakości
                break
        
        # 3. Zwróć najlepszą odpowiedź
        return LLMResponse(
            generated_code=best_response['generated_code'],
            explanation=best_response['explanation'],
            validation_result=best_response['validation_result'],
            iterations_used=best_response['iteration'],
            quality_score=best_score
        )
    
    async def _simulate_llm_call(self, prompt: str) -> str:
        """Symuluje wywołanie LLM (do zastąpienia prawdziwym API)"""
        
        # W rzeczywistej implementacji tutaj byłoby:
        # response = await openai.ChatCompletion.acreate(...)
        # return response.choices[0].message.content
        
        # Symulacja - zwraca przykładowy kod na podstawie promptu
        if "calculate_discount" in prompt.lower():
            return '''Here's a refactored discount calculation function:

```python
from dataclasses import dataclass
from typing import Dict
import logging

logger = logging.getLogger(__name__)

@dataclass
class DiscountRequest:
    """Data structure for discount calculation parameters."""
    user_type: str
    product_price: float
    quantity: int
    is_vip: bool
    season: str
    product_category: str
    is_first_purchase: bool
    loyalty_points: int
    previous_orders_count: int

class DiscountCalculator:
    """Calculates product discounts based on business rules."""
    
    def calculate(self, request: DiscountRequest) -> float:
        """
        Calculate discount based on user profile and product details.
        
        Args:
            request: DiscountRequest containing all necessary data
            
        Returns:
            float: Final price after discount
        """
        logger.info(f"Calculating discount for {request.user_type}")
        
        discount_rate = self._get_discount_rate(request)
        final_price = request.product_price * (1 - discount_rate)
        
        return final_price
    
    def _get_discount_rate(self, request: DiscountRequest) -> float:
        """Get discount rate based on user type."""
        if request.user_type == "premium":
            return self._calculate_premium_discount(request)
        return 0.01
    
    def _calculate_premium_discount(self, request: DiscountRequest) -> float:
        """Calculate discount for premium users."""
        base_rate = 0.05
        
        if request.product_price > 1000:
            base_rate += 0.10
        if request.quantity > 5:
            base_rate += 0.05
        if request.is_vip:
            base_rate += 0.10
            
        return min(base_rate, 0.35)  # Cap at 35%
```

This refactored code:
1. Uses dataclass to group parameters (9 → 1)
2. Implements proper logging instead of print
3. Reduces cyclomatic complexity through method extraction
4. Adds comprehensive docstrings
5. Follows single responsibility principle
'''
        else:
            return '''Here's a sample Python function:

```python
def sample_function():
    """
    A sample function that demonstrates good practices.
    
    Returns:
        str: A greeting message
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Generating greeting")
    return "Hello, World!"
```

This code follows the project quality standards.
'''
    
    def _calculate_response_score(self, validation_result: Dict[str, Any]) -> int:
        """Oblicza wynik jakości odpowiedzi LLM (0-100)"""
        score = 0
        
        # Podstawowe punkty za wyodrębnienie kodu
        if validation_result.get('code_extracted', False):
            score += 30
        
        # Punkty za jakość kodu
        code_quality = validation_result.get('code_quality', {})
        if code_quality:
            quality_score = code_quality.get('quality_score', 0)
            score += quality_score * 0.7  # 70% wagi za jakość kodu
        
        return int(score)
