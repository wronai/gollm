"""
LLM Integration module for goLLM

Provides integration with various LLM providers including:
- OpenAI GPT models
- Anthropic Claude
- Local Ollama models
"""

# Legacy imports for backward compatibility
from .context_builder import ContextBuilder
from .ollama_adapter import OllamaAdapter, OllamaLLMProvider
# Import from the orchestrator package
from .orchestrator import (LLMClient, LLMGenerationConfig, LLMIterationResult,
                           LLMOrchestrator, LLMRequest, LLMResponse,
                           ResponseValidator)
from .prompt_formatter import PromptFormatter

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
    "OllamaLLMProvider",
]
