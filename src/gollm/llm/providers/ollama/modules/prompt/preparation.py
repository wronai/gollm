"""Prompt preparation utilities for Ollama API requests."""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("gollm.ollama.prompt")


def prepare_llm_request_args(
    prompt: str, 
    context: Optional[Dict[str, Any]], 
    model: str,
    **kwargs
) -> Tuple[str, Dict[str, Any]]:
    """Prepare the prompt and parameters for an LLM request.
    
    Args:
        prompt: The original prompt to modify
        context: Additional context for generation
        model: The model to use for generation
        **kwargs: Additional generation parameters
        
    Returns:
        Tuple containing (modified_prompt, generation_params)
    """
    from ..parameters.mapping import prepare_generation_parameters
    
    # Default generation parameters - optimized for code generation
    default_params = {
        "temperature": 0.1,  # Very low for deterministic output
        "max_tokens": 500,  # Increased to allow for longer code blocks
        "top_p": 0.9,  # Focus on high probability tokens
        "top_k": 40,  # Limit sampling pool
        "repeat_penalty": 1.2,  # Penalize repetition more
        "num_ctx": 4096,  # Increased context window for code generation
        "stop": [
            "```",
            "\n\n",
            "\n#",
            "---",
            "===",
            "\n",
        ],  # Stop on formatting
    }

    # Log incoming parameters for debugging
    logger.debug("Original generation parameters: %s", kwargs)

    # Update defaults with any provided kwargs, filtering out None values
    generation_params = {
        **default_params,
        **{k: v for k, v in kwargs.items() if v is not None},
    }

    # Ensure temperature is within valid range
    if "temperature" in generation_params:
        generation_params["temperature"] = max(
            0.0, min(1.0, float(generation_params["temperature"]))
        )

    # Modify the prompt to be extremely explicit about the expected output format
    modified_prompt = prompt
    if "CODE_ONLY" not in prompt:
        modified_prompt = f"""
        {prompt}
        
        RULES:
        - Respond with ONLY the Python code, nothing else
        - No explanations, no markdown, no additional text
        - Just the raw Python code that can be executed directly
        
        Example of the ONLY acceptable response:
        print("Hello, World!")
        
        CODE_ONLY: True
        """.strip()

        # Add a system message to ensure the model understands the format
        if context and "messages" in context:
            # If we have a chat context, insert a system message
            context["messages"].insert(
                0,
                {
                    "role": "system",
                    "content": "You are a code generator. Respond with ONLY the requested code, no explanations, no markdown, just the raw code.",
                },
            )

    # Get generation parameters with overrides
    generation_params = prepare_generation_parameters(
        model=model, **kwargs
    )

    # Force specific parameters for code generation
    generation_params["temperature"] = 0.1
    generation_params["top_p"] = 0.9
    generation_params["top_k"] = 40
    generation_params["repeat_penalty"] = 1.1
    generation_params["num_ctx"] = 4096
    generation_params["num_predict"] = 500  # Override to allow longer responses

    # Ensure consistent stop sequences
    if "stop" not in generation_params or not generation_params["stop"]:
        generation_params["stop"] = ["```", "\n```", "\n#", "---", "==="]
        
    return modified_prompt, generation_params


def extract_response_content(response: Dict[str, Any]) -> str:
    """Extract the generated text from the Ollama API response.
    
    Args:
        response: The raw API response
        
    Returns:
        The extracted text content
    """
    # Extract the generated text from different possible response formats
    generated_text = ""
    
    # Try to extract from standard chat format first
    if "message" in response and "content" in response["message"]:
        generated_text = response["message"]["content"]
        logger.debug(f"Extracted content from message.content: {generated_text[:100]}...")
        
    # If not found, try to extract from response field (some Ollama versions)
    elif "response" in response:
        generated_text = response["response"]
        logger.debug(f"Extracted content from response: {generated_text[:100]}...")
        
    # Try other possible formats
    elif (
        "choices" in response
        and len(response["choices"]) > 0
        and "text" in response["choices"][0]
    ):
        generated_text = response["choices"][0]["text"]
        logger.debug(f"Extracted content from choices[0].text: {generated_text[:100]}...")
        
    elif (
        "choices" in response
        and len(response["choices"]) > 0
        and "message" in response["choices"][0]
    ):
        generated_text = response["choices"][0]["message"].get("content", "")
        logger.debug(f"Extracted content from choices[0].message.content: {generated_text[:100]}...")
    
    # If still no content found, try to find any string field that might contain the response
    else:
        logger.warning(f"Could not find content in standard fields. Keys: {list(response.keys())}")
        for key, value in response.items():
            if isinstance(value, str) and len(value) > 50:  # Likely to be content
                logger.info(f"Found potential content in key '{key}' (length: {len(value)})")
                generated_text = value
                break
    
    return generated_text
