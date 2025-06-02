"""Data models for the LLM orchestrator."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List

@dataclass
class LLMRequest:
    """Represents a request to generate code using an LLM."""
    user_request: str
    context: Dict[str, Any]
    session_id: str
    max_iterations: int = 3

@dataclass
class LLMResponse:
    """Represents a response from the LLM code generation process."""
    generated_code: str
    explanation: str
    validation_result: Dict[str, Any]
    iterations_used: int
    quality_score: int

@dataclass
class LLMIterationResult:
    """Represents the result of a single LLM iteration."""
    generated_code: str
    explanation: str
    validation_result: Dict[str, Any]
    score: float
    iteration: int
    
    @property
    def is_successful(self) -> bool:
        """Check if the iteration was successful."""
        return self.validation_result.get('code_extracted', False) and self.score > 0

@dataclass
class LLMGenerationConfig:
    """Configuration for LLM generation."""
    max_iterations: int = 3
    target_quality_score: float = 90.0
    temperature: float = 0.1
    max_tokens: int = 4000
    model_name: Optional[str] = None
