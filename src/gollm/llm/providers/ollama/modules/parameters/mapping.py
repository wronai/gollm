"""Parameter mapping utilities for Ollama API requests."""

import logging
from typing import Any, Dict

logger = logging.getLogger("gollm.ollama.parameters")


def prepare_generation_parameters(model: str, **kwargs) -> Dict[str, Any]:
    """Prepare generation parameters for the Ollama API.

    Args:
        model: The model name
        **kwargs: Additional generation parameters
            - temperature: Controls randomness (0.0 to 1.0)
            - max_tokens: Maximum number of tokens to generate
            - top_p: Nucleus sampling parameter (0.0 to 1.0)
            - top_k: Limit next token selection to top K (1-100)
            - repeat_penalty: Penalty for repeated tokens (1.0+)
            - stop: List of strings to stop generation

    Returns:
        Dictionary of prepared generation parameters
    """
    # Start with default parameters
    params = {
        "model": model,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "num_ctx": 4096,
        "num_predict": 500,
        "stop": ["```", "\n```", "\n#", "---", "==="],
    }

    # Update with any provided kwargs, filtering out None values
    params.update({k: v for k, v in kwargs.items() if v is not None})

    # Ensure parameter values are within valid ranges
    if "temperature" in params:
        params["temperature"] = max(0.0, min(1.0, float(params["temperature"])))

    if "top_p" in params:
        params["top_p"] = max(0.0, min(1.0, float(params["top_p"])))

    if "top_k" in params:
        params["top_k"] = max(1, min(100, int(params["top_k"])))

    if "repeat_penalty" in params:
        params["repeat_penalty"] = max(1.0, float(params["repeat_penalty"]))

    if "num_predict" in params:
        params["num_predict"] = max(1, int(params["num_predict"]))

    # Ensure stop is a list of strings
    if "stop" in params and params["stop"] is not None:
        if isinstance(params["stop"], str):
            params["stop"] = [params["stop"]]
        elif not isinstance(params["stop"], list):
            params["stop"] = list(map(str, params["stop"]))

    return params


def map_params_to_options(generation_params: Dict[str, Any]) -> Dict[str, Any]:
    """Map generation parameters to Ollama API options format.
    
    Args:
        generation_params: Dictionary of generation parameters
        
    Returns:
        Dictionary of options formatted for the Ollama API
    """
    options = {}

    # Map common parameter names to Ollama's expected names
    param_mapping = {
        "max_tokens": "num_predict",
        "frequency_penalty": "repeat_penalty",
        "presence_penalty": "repeat_penalty",
        "stop": "stop",
    }

    # Add all generation parameters to options with proper mapping
    for param, value in generation_params.items():
        # Skip None values to use Ollama defaults
        if value is None:
            continue

        # Special handling for stop sequences
        if param == "stop" and value:
            if not isinstance(value, list):
                value = [str(value)]
            options["stop"] = [str(s) for s in value]
            continue

        # Map parameter names if needed
        mapped_param = param_mapping.get(param, param)

        # Ensure parameter values are within valid ranges
        if mapped_param == "temperature":
            value = max(0.0, min(1.0, float(value)))
        elif mapped_param in ("top_p", "top_k"):
            value = max(1, min(100, int(value)))
        elif mapped_param == "repeat_penalty":
            value = max(1.0, float(value))
        elif mapped_param == "num_predict":
            value = max(1, int(value))

        options[mapped_param] = value
        
    return options
