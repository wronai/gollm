"""Prompt formatting utilities for Ollama provider."""

import json
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("gollm.ollama.prompt")


def format_prompt_for_ollama(
    prompt: str, context: Optional[Dict[str, Any]] = None
) -> str:
    """Format a prompt for the Ollama API.

    Args:
        prompt: The prompt to format
        context: Additional context for prompt formatting

    Returns:
        Formatted prompt string
    """
    if not context:
        return prompt

    # Extract context variables
    system_prompt = context.get("system_prompt", "")
    chat_history = context.get("chat_history", [])
    code_context = context.get("code_context", "")
    file_context = context.get("file_context", "")
    task_description = context.get("task_description", "")

    # Format based on available context
    formatted_prompt = ""

    # Add system prompt if available
    if system_prompt:
        formatted_prompt += f"System: {system_prompt}\n\n"

    # Add code context if available
    if code_context:
        formatted_prompt += f"Code Context:\n```\n{code_context}\n```\n\n"

    # Add file context if available
    if file_context:
        formatted_prompt += f"File Context:\n{file_context}\n\n"

    # Add task description if available
    if task_description:
        formatted_prompt += f"Task: {task_description}\n\n"

    # Add chat history if available
    if chat_history:
        formatted_prompt += "Chat History:\n"
        for entry in chat_history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            formatted_prompt += f"{role.capitalize()}: {content}\n"
        formatted_prompt += "\n"

    # Add the actual prompt
    formatted_prompt += f"User: {prompt}"

    logger.debug(f"Formatted prompt: {formatted_prompt[:100]}...")
    return formatted_prompt


def format_chat_messages(
    prompt: str, context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """Format chat messages for the Ollama API.

    Args:
        prompt: The prompt to format
        context: Additional context for message formatting

    Returns:
        List of message dictionaries with 'role' and 'content' keys
    """
    messages = []

    if not context:
        return [{"role": "user", "content": prompt}]

    # Extract context variables
    system_prompt = context.get("system_prompt", "")
    chat_history = context.get("chat_history", [])
    code_context = context.get("code_context", "")
    file_context = context.get("file_context", "")
    task_description = context.get("task_description", "")

    # Add system message if available
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Build content preamble with code and file context
    content_preamble = ""

    if code_context:
        content_preamble += f"Code Context:\n```\n{code_context}\n```\n\n"

    if file_context:
        content_preamble += f"File Context:\n{file_context}\n\n"

    if task_description:
        content_preamble += f"Task: {task_description}\n\n"

    # Add chat history if available
    if chat_history:
        for entry in chat_history:
            messages.append(entry)

    # Add the actual prompt with context preamble
    if content_preamble:
        messages.append({"role": "user", "content": f"{content_preamble}\n{prompt}"})
    else:
        messages.append({"role": "user", "content": prompt})

    logger.debug(f"Formatted {len(messages)} chat messages")
    return messages


def extract_response_content(response: Dict[str, Any]) -> str:
    """Extract the content from an Ollama API response.

    Args:
        response: The response from the Ollama API

    Returns:
        The extracted content as a string
    """
    # Handle chat API responses
    if "message" in response and isinstance(response["message"], dict):
        return response["message"].get("content", "")

    # Handle generate API responses
    if "response" in response:
        return response["response"]

    # Handle streaming responses that have been aggregated
    if "responses" in response and isinstance(response["responses"], list):
        return "".join([r.get("response", "") for r in response["responses"]])

    # If we can't find the content, return an empty string
    logger.warning(f"Could not extract content from response: {response}")
    return ""


def extract_model_info(response: Dict[str, Any]) -> Dict[str, Any]:
    """Extract model information from an Ollama API response.

    Args:
        response: The response from the Ollama API

    Returns:
        Dictionary containing model information
    """
    model_info = {}

    # Extract common fields
    for field in [
        "model",
        "created_at",
        "total_duration",
        "load_duration",
        "prompt_eval_count",
        "eval_count",
        "eval_duration",
    ]:
        if field in response:
            model_info[field] = response[field]

    return model_info
