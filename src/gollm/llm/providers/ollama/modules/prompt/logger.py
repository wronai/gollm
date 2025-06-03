"""Prompt logging module for Ollama adapter."""

import codecs
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("gollm.ollama.prompt")


class PromptLogger:
    """Handles detailed logging of prompts, responses, and metadata."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the prompt logger.

        Args:
            config: Configuration dictionary with logging options
        """
        self.config = config
        self.show_prompt = config.get("show_prompt", False)
        self.show_response = config.get("show_response", False)
        self.show_metadata = config.get("show_metadata", False)

    def log_request(
        self,
        prompt: Union[str, List[Dict[str, str]]],
        model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log details about an LLM request.

        Args:
            prompt: The prompt or messages sent to the LLM
            model: The model being used
            metadata: Additional metadata about the request
        """
        if not any([self.show_prompt, self.show_metadata]):
            # Basic logging if detailed logging is disabled
            if isinstance(prompt, str):
                truncated = prompt[:50] + "..." if len(prompt) > 50 else prompt
                logger.info(f"Sending request to model {model}: {truncated}")
            else:
                logger.info(f"Sending {len(prompt)} messages to model {model}")
            return

        # Detailed logging
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "model": model,
            "request_type": "completion" if isinstance(prompt, str) else "chat",
        }

        # Add metadata if available
        if metadata and self.show_metadata:
            log_data["metadata"] = metadata

        # Log the prompt content if enabled
        if self.show_prompt:
            if isinstance(prompt, str):
                log_data["prompt"] = prompt
            else:
                log_data["messages"] = prompt

        # Log the formatted data
        logger.info(
            f"LLM Request: {json.dumps(log_data, indent=2, ensure_ascii=False)}"
        )

    def _detect_escape_sequences(self, text: str) -> Tuple[bool, Dict[str, int]]:
        """Detect escape sequences in text.

        Args:
            text: The text to analyze for escape sequences

        Returns:
            Tuple containing:
            - Boolean indicating if escape sequences were found
            - Dictionary with counts of each escape sequence type
        """
        escape_sequences = {
            "\\n": 0,  # newline
            "\\t": 0,  # tab
            "\\r": 0,  # carriage return
            '\\"': 0,  # double quote
            "\\'": 0,  # single quote
            "\\\\": 0,  # backslash
            "\\x": 0,  # hex escape
            "\\u": 0,  # unicode escape
        }

        has_escapes = False

        for seq in escape_sequences.keys():
            count = text.count(seq)
            if count > 0:
                escape_sequences[seq] = count
                has_escapes = True

        # Check for hex escapes (\x00-\xFF)
        hex_escapes = re.findall(r"\\x[0-9a-fA-F]{2}", text)
        if hex_escapes:
            escape_sequences["\\x"] = len(hex_escapes)
            has_escapes = True

        # Check for unicode escapes (\u0000-\uFFFF)
        unicode_escapes = re.findall(r"\\u[0-9a-fA-F]{4}", text)
        if unicode_escapes:
            escape_sequences["\\u"] = len(unicode_escapes)
            has_escapes = True

        return has_escapes, escape_sequences

    def _analyze_code_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Analyze code blocks in text for escape sequences.

        Args:
            text: The text to analyze for code blocks

        Returns:
            List of dictionaries with code block analysis
        """
        code_blocks = []

        # Find code blocks with language specifier
        blocks = re.findall(r"```(?:\w*)?\n(.+?)(?:\n```|$)", text, re.DOTALL)

        for i, block in enumerate(blocks):
            has_escapes, escape_counts = self._detect_escape_sequences(block)

            # Try to decode the block if it has escape sequences
            decoded_block = None
            if has_escapes:
                try:
                    decoded_block = codecs.decode(block, "unicode_escape")
                except Exception as e:
                    logger.debug(
                        f"Failed to decode code block {i+1} with unicode_escape: {str(e)}"
                    )

            code_blocks.append(
                {
                    "block_index": i + 1,
                    "length": len(block),
                    "has_escape_sequences": has_escapes,
                    "escape_counts": escape_counts,
                    "first_100_chars": (
                        block[:100] + "..." if len(block) > 100 else block
                    ),
                    "decoded_length": len(decoded_block) if decoded_block else None,
                }
            )

        return code_blocks

    def log_response(self, response: Dict[str, Any], duration: float) -> None:
        """Log details about an LLM response.

        Args:
            response: The response from the LLM
            duration: Time taken for the request in seconds
        """
        # Always log basic timing information
        logger.info(f"Received response in {duration:.2f}s")

        # Extract the response content for analysis
        response_content = None
        if "response" in response:
            response_content = response["response"]
        elif "text" in response:
            response_content = response["text"]
        elif "content" in response:
            response_content = response["content"]
        elif "message" in response and "content" in response["message"]:
            response_content = response["message"]["content"]
        elif "generated_text" in response:
            response_content = response["generated_text"]

        # Analyze escape sequences in the response if content was extracted
        escape_analysis = None
        code_blocks_analysis = None
        if response_content:
            has_escapes, escape_counts = self._detect_escape_sequences(response_content)
            if has_escapes:
                logger.warning(f"Found escape sequences in response: {escape_counts}")
                escape_analysis = {
                    "has_escape_sequences": has_escapes,
                    "escape_counts": escape_counts,
                }

            # Analyze code blocks
            code_blocks_analysis = self._analyze_code_blocks(response_content)
            if code_blocks_analysis:
                logger.info(
                    f"Found {len(code_blocks_analysis)} code blocks in response"
                )
                for block in code_blocks_analysis:
                    if block["has_escape_sequences"]:
                        logger.warning(
                            f"Code block {block['block_index']} contains escape sequences: {block['escape_counts']}"
                        )

        if not any([self.show_response, self.show_metadata]):
            return

        # Detailed logging
        log_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": duration,
        }

        # Add metadata if available and enabled
        if self.show_metadata and "metadata" in response:
            log_data["metadata"] = response["metadata"]

        # Add escape sequence analysis if available
        if escape_analysis:
            log_data["escape_analysis"] = escape_analysis

        # Add code blocks analysis if available and not too verbose
        if code_blocks_analysis and len(code_blocks_analysis) <= 5:
            log_data["code_blocks"] = code_blocks_analysis

        # Add response content if enabled
        if self.show_response:
            # Extract the actual response content based on response structure
            if response_content:
                log_data["response"] = response_content
            else:
                # Include the full response if we can't extract the content
                log_data["full_response"] = response

        # Log the formatted data
        logger.info(
            f"LLM Response: {json.dumps(log_data, indent=2, ensure_ascii=False)}"
        )

    def log_error(
        self,
        error: Union[str, Exception],
        prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
        model: Optional[str] = None,
    ) -> None:
        """Log details about an error during LLM request.

        Args:
            error: The error message or exception
            prompt: The prompt that caused the error (if available)
            model: The model being used (if available)
        """
        error_msg = str(error)

        # Basic error logging
        logger.error(f"Error in LLM request: {error_msg}")

        if not any([self.show_prompt, self.show_metadata]):
            return

        # Detailed error logging
        log_data = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "error": error_msg}

        # Add model information if available
        if model:
            log_data["model"] = model

        # Add prompt information if available and enabled
        if prompt and self.show_prompt:
            if isinstance(prompt, str):
                log_data["prompt"] = prompt
            else:
                log_data["messages"] = prompt

        # Log the formatted data
        logger.error(
            f"LLM Error Details: {json.dumps(log_data, indent=2, ensure_ascii=False)}"
        )
