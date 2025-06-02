"""
LLM Integration module for goLLM

Provides integration with various LLM providers including:
- OpenAI GPT models
- Anthropic Claude
- Local Ollama models
"""

# Import from the orchestrator package
from .orchestrator import (
    LLMOrchestrator,
    LLMRequest,
    LLMResponse,
    LLMIterationResult,
    LLMGenerationConfig,
    LLMClient,
    ResponseValidator
)

# Legacy imports for backward compatibility
from .context_builder import ContextBuilder
from .prompt_formatter import PromptFormatter
from .ollama_adapter import OllamaAdapter, OllamaLLMProvider

__all__ = [
    # Core components
    "LLMOrchestrator",
    "LLMRequest",
    "LLMResponse",
    "LLMIterationResult",
    "LLMGenerationConfig",
    "LLMClient",
    "ResponseValidator",
    
    # Legacy components
    "ContextBuilder", 
    "PromptFormatter",
    "OllamaAdapter",
    "OllamaLLMProvider",
    "OllamaLLMProvider"
]