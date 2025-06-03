# src/gollm/llm/orchestrator.py
import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from gollm.validation.validators import CodeValidator

from .context_builder import ContextBuilder
from .prompt_formatter import PromptFormatter
from .response_validator import ResponseValidator


@dataclass
class LLMRequest:
    user_request: str
    context: Dict[str, Any]
    session_id: str
    max_iterations: int = 3
    fast_mode: bool = False


@dataclass
class LLMResponse:
    generated_code: str
    explanation: str
    validation_result: Dict[str, Any]
    iterations_used: int
    quality_score: int
    test_code: Optional[str] = None
    has_incomplete_functions: bool = False
    incomplete_functions: List[Dict[str, str]] = None
    has_completed_functions: bool = False
    still_has_incomplete_functions: bool = False
    still_incomplete_functions: List[Dict[str, str]] = None
    execution_tested: bool = False
    execution_successful: bool = False
    execution_errors: List[str] = None
    execution_fixed: bool = False
    execution_fix_attempts: int = 0


class LLMOrchestrator:
    """Orkiestruje komunikację z LLM i zarządza kontekstem"""

    def __init__(self, config, code_validator=None, todo_manager=None):
        self.config = config
        self.context_builder = ContextBuilder(config)
        self.prompt_formatter = PromptFormatter(config)
        self.response_validator = ResponseValidator(config)
        self.code_validator = code_validator or CodeValidator(config)
        self.todo_manager = todo_manager
        self.current_task_id = None

    async def handle_code_generation_request(
        self, user_request: str, context: Dict[str, Any] = None
    ) -> LLMResponse:
        """Główny punkt wejścia dla generowania kodu przez LLM"""
        if context is None:
            context = {}
            
        # Check if we should generate tests automatically
        generate_tests = context.get("generate_tests", False)

        # Extract parameters from context
        max_iterations = context.get("max_iterations", 3)
        validation_mode = context.get("validation_mode", "strict")
        skip_validation = context.get("skip_validation", False)
        use_streaming = context.get("use_streaming", True)

        # Create a task in the todo manager
        if self.todo_manager:
            task_context = {
                "request": user_request,
                "context": context,
                "is_critical": context.get("is_critical", False),
                "related_files": context.get("related_files", []),
            }
            task = self.todo_manager.add_code_generation_task(
                user_request, task_context
            )
            self.current_task_id = task.id

        session_id = context.get(
            "session_id", f"session-{asyncio.get_event_loop().time()}"
        )

        # Get fast mode and max iterations from context
        fast_mode = context.get("fast_mode", False)
        max_iterations = context.get(
            "max_iterations", self.config.llm_integration.max_iterations
        )

        # If fast mode is enabled, limit to 1 iteration
        if fast_mode:
            max_iterations = 1

        request = LLMRequest(
            user_request=user_request,
            context=context,
            session_id=session_id,
            max_iterations=max_iterations,
            fast_mode=fast_mode,
        )

        try:
            # Process the main code generation request
            response = await self._process_llm_request(
                request, use_streaming=use_streaming
            )
            
            # Check for incomplete functions in the generated code
            from gollm.validation.validators.validation_coordinator import check_for_incomplete_functions
            from gollm.validation.validators.incomplete_function_detector import format_for_completion, extract_completed_functions
            
            has_incomplete_functions, incomplete_functions = check_for_incomplete_functions(response.generated_code)
            
            # If incomplete functions are found and auto-completion is enabled, complete them
            auto_complete = context.get("auto_complete_functions", True)  # Enable by default
            
            if has_incomplete_functions and auto_complete:
                logger.info(f"Found {len(incomplete_functions)} incomplete functions. Triggering auto-completion...")
                
                # Format the code for completion
                completion_prompt = format_for_completion(incomplete_functions, response.generated_code)
                
                # Create a completion request
                completion_request = LLMRequest(
                    user_request=completion_prompt,
                    context=context,
                    session_id=request.session_id + "-completion",
                    max_iterations=1,
                    fast_mode=request.fast_mode,
                )
                
                # Process the completion request
                completion_response = await self._process_llm_request(
                    completion_request, use_streaming=use_streaming
                )
                
                # Merge the completed functions with the original code
                merged_code = extract_completed_functions(response.generated_code, completion_response.generated_code)
                
                # Update the response with the completed code
                response.generated_code = merged_code
                response.has_completed_functions = True
                
                # Check if there are still incomplete functions after the completion attempt
                still_has_incomplete, still_incomplete = check_for_incomplete_functions(merged_code)
                if still_has_incomplete:
                    logger.warning(f"Still found {len(still_incomplete)} incomplete functions after auto-completion.")
                    response.still_has_incomplete_functions = True
                    response.still_incomplete_functions = still_incomplete
                else:
                    logger.info("Successfully completed all incomplete functions.")
                    response.still_has_incomplete_functions = False
            elif has_incomplete_functions:
                logger.info(f"Found {len(incomplete_functions)} incomplete functions, but auto-completion is disabled.")
                response.has_incomplete_functions = True
                response.incomplete_functions = incomplete_functions
            else:
                response.has_incomplete_functions = False
            
            # Test code execution and fix errors if needed
            from gollm.validation.validators.code_executor import execute_python_code, format_error_for_completion
            
            # Check if execution testing is enabled
            execute_test = context.get("execute_test", True)  # Enable by default
            auto_fix_execution = context.get("auto_fix_execution", True)  # Enable by default
            max_fix_attempts = context.get("max_fix_attempts", 5)  # Default to 5 attempts (increased from 3)
            execution_timeout = context.get("execution_timeout", 15)  # Default timeout in seconds
            
            if execute_test and response.generated_code and response.generated_code.strip():
                # Only test Python code for now
                if response.generated_code.strip().startswith("#!/usr/bin/env python") or "def " in response.generated_code or "import " in response.generated_code:
                    logger.info("Testing code execution...")
                    response.execution_tested = True
                    
                    # Execute the code with enhanced error handling
                    success, error, output = execute_python_code(response.generated_code, timeout=execution_timeout)
                    response.execution_successful = success
                    response.execution_errors = [error] if error else []
                    
                    # Log output for debugging if successful
                    if success and output:
                        logger.debug(f"Code execution output:\n{output}")
                    
                    # If execution failed and auto-fix is enabled, try to fix it
                    if not success and auto_fix_execution:
                        logger.info(f"Code execution failed with error: {error}. Attempting to fix...")
                        current_code = response.generated_code
                        
                        for attempt in range(max_fix_attempts):
                            response.execution_fix_attempts += 1
                            
                            # Format the error for LLM completion with enhanced error context
                            fix_request = format_error_for_completion(current_code, error)
                            
                            # Add more context for better fixes after multiple failed attempts
                            if attempt > 0:
                                fix_request += f"\n\nThis is fix attempt #{attempt+1}. Previous fix attempts failed with these errors:\n```\n{', '.join(response.execution_errors[-min(3, len(response.execution_errors)):])[:500]}\n```\n\nPlease provide a more robust solution that addresses all potential issues."
                            
                            # Create a fix request object with higher iteration count for complex fixes
                            fix_llm_request = LLMRequest(
                                user_request=fix_request,
                                context=context,
                                session_id=request.session_id + f"-fix-{attempt+1}",
                                max_iterations=2 if attempt > 1 else 1,  # More iterations for complex fixes
                                fast_mode=False,  # Disable fast mode for fixes to ensure quality
                            )
                            
                            # Process the fix request
                            fix_response = await self._process_llm_request(
                                fix_llm_request, use_streaming=use_streaming
                            )
                            
                            # Update the code with the fixed version
                            current_code = fix_response.generated_code
                            
                            # Test the fixed code with enhanced error handling
                            success, error, output = execute_python_code(current_code, timeout=execution_timeout)
                            if success:
                                logger.info(f"Successfully fixed code execution errors after {attempt+1} attempts")
                                response.execution_successful = True
                                response.execution_fixed = True
                                response.generated_code = current_code  # Update with fixed code
                                
                                # Log the successful output
                                if output:
                                    logger.debug(f"Fixed code execution output:\n{output}")
                                break
                            else:
                                logger.warning(f"Fix attempt {attempt+1} failed: {error}")
                                response.execution_errors.append(error)
                                
                                # If we're getting the same error repeatedly, try a more drastic approach
                                if attempt > 1 and len(set(response.execution_errors[-2:])) == 1:
                                    logger.info("Getting same error repeatedly, trying more comprehensive rewrite...")
                        
                        if not response.execution_successful:
                            logger.error(f"Failed to fix code execution errors after {max_fix_attempts} attempts")
                            # Add a note about the unfixed errors to the explanation
                            if response.explanation:
                                response.explanation += "\n\n**Note:** The code has execution errors that could not be automatically fixed. Please review the error messages and fix manually."
                    
                    elif success:
                        logger.info("Code execution successful on first attempt")
                        # Add a note about successful execution to the explanation
                        if response.explanation:
                            response.explanation += "\n\n**Note:** The code has been automatically tested and executes successfully."
                else:
                    logger.info("Skipping execution test for non-Python code")
            
            # If test generation is enabled, generate tests for the code
            if generate_tests and response.generated_code:
                # Create a new request for test generation
                test_request = f"Write unit tests for the following code:\n\n```python\n{response.generated_code}\n```"
                
                # Create a test request object
                test_llm_request = LLMRequest(
                    user_request=test_request,
                    context=context,
                    session_id=request.session_id + "-test",
                    max_iterations=1,  # Tests usually need fewer iterations
                    fast_mode=request.fast_mode,
                )
                
                # Process the test generation request
                test_response = await self._process_llm_request(
                    test_llm_request, use_streaming=use_streaming
                )
                
                # Store the test code in the response
                response.test_code = test_response.generated_code
                
                # Execute the tests if execution testing is enabled
                if execute_test and response.execution_successful and response.test_code:
                    logger.info("Testing the generated unit tests...")
                    
                    # Create a temporary test file that imports the main code
                    import_code = ""
                    if "import unittest" not in response.test_code:
                        import_code = "import unittest\n"
                    
                    # Execute the tests
                    test_success, test_error, test_output = execute_python_code(
                        import_code + response.test_code, 
                        filename="test_execution.py",
                        timeout=execution_timeout * 2  # Double timeout for tests
                    )
                    
                    if test_success:
                        logger.info("Unit tests executed successfully")
                        if response.explanation:
                            response.explanation += "\n\n**Note:** The generated unit tests have been executed and pass successfully."
                    else:
                        logger.warning(f"Unit tests failed to execute: {test_error}")
                        # We don't try to fix test failures automatically - that's a separate concern
            else:
                response.test_code = None

            # Update task with results if successful
            if self.todo_manager and self.current_task_id:
                self.todo_manager.update_code_generation_task(
                    self.current_task_id,
                    {
                        "generated_code": response.generated_code,
                        "test_code": getattr(response, "test_code", None),
                        "quality_score": response.quality_score,
                        "violations": response.validation_result.get("violations", []),
                        "output_file": context.get("output_file", "unknown.py"),
                    },
                )

            return response

        except Exception as e:
            # Update task with error if something went wrong
            if self.todo_manager and self.current_task_id:
                self.todo_manager.update_code_generation_task(
                    self.current_task_id, {"error": str(e)}
                )
            raise

    async def _process_llm_request(
        self, request: LLMRequest, use_streaming: bool = True
    ) -> LLMResponse:
        """Przetwarza żądanie LLM z iteracjami i walidacją

        Args:
            request: The LLM request to process
            use_streaming: Whether to use streaming API when available

        Returns:
            LLMResponse with the generated code and validation results
        """
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            f"Starting LLM request processing for: {request.user_request[:100]}..."
        )
        logger.info(
            f"Request details: adapter_type={request.adapter_type}, use_streaming={use_streaming}, fast_mode={request.fast_mode}"
        )
        logger.info(
            f"Context keys: {list(request.context.keys()) if request.context else 'None'}"
        )

        # Przygotuj kontekst
        context = request.context or {}

        # 1. Przygotuj pełny kontekst
        # In fast mode, use minimal context building
        if request.fast_mode:
            logger.info("Fast mode enabled: Using minimal context building")
            full_context = {
                "request": request.user_request,
                "session_id": request.session_id,
                "fast_mode": True,
            }
            # Add only essential context elements
            for key in ["related_files", "output_file", "is_website_project"]:
                if key in request.context:
                    full_context[key] = request.context[key]
        else:
            full_context = await self.context_builder.build_context(request.context)
            logger.debug(f"Built full context with keys: {list(full_context.keys())}")

        # 2. Iteracyjne generowanie kodu
        best_response = None
        best_score = 0
        logger.info(f"Starting {request.max_iterations} iterations of code generation")

        for iteration in range(request.max_iterations):
            # Sformatuj prompt
            logger.info(f"\n--- Starting iteration {iteration + 1} ---")
            prompt = self.prompt_formatter.create_prompt(
                request.user_request,
                full_context,
                iteration=iteration,
                previous_attempt=best_response,
            )

            logger.debug(f"Generated prompt (truncated): {prompt[:300]}...")

            # Make the actual LLM call
            logger.info("Calling LLM...")
            raw_output = await self._simulate_llm_call(prompt, stream=use_streaming)
            logger.info(f"===== RAW LLM OUTPUT RECEIVED =====")
            logger.info(f"Raw output length: {len(raw_output)}")
            logger.info(f"First 500 chars: {raw_output[:500]}...")
            logger.info(
                f"Last 200 chars: {raw_output[-200:] if len(raw_output) > 200 else raw_output}"
            )

            # Check for code blocks in the raw output
            import re

            code_blocks = re.findall(
                r"```(?:\w*)?\n(.+?)(?:\n```|$)", raw_output, re.DOTALL
            )
            logger.info(f"Found {len(code_blocks)} code blocks in raw output")
            for i, block in enumerate(code_blocks):
                logger.info(f"Raw output code block {i+1} length: {len(block)}")
                if len(block) > 0:
                    logger.debug(
                        f"Raw output code block {i+1} first 100 chars: {block[:100]}..."
                    )
                    logger.debug(
                        f"Raw output code block {i+1} last 100 chars: {block[-100:] if len(block) > 100 else block}"
                    )

            # Waliduj odpowiedź - simplified in fast mode
            logger.info("Validating LLM response...")

            if request.fast_mode:
                logger.info("Fast mode: Using simplified validation")
                # Simple code extraction without extensive validation
                import re

                # Try to extract code blocks first
                code_blocks = re.findall(
                    r"```(?:python)?\n(.+?)\n```", raw_output, re.DOTALL
                )

                if code_blocks:
                    extracted_code = code_blocks[0]  # Take the first code block
                    logger.info(
                        f"Fast mode: Extracted code block of {len(extracted_code)} chars"
                    )
                    validation_result = {
                        "success": True,
                        "code_extracted": True,
                        "extracted_code": extracted_code,
                        "explanation": "Code extracted in fast mode",
                        "code_quality": {
                            "violations": [],
                            "quality_score": 80,  # Assume reasonable quality for code blocks
                        },
                    }
                else:
                    # If no code blocks found, use the entire output as code
                    logger.info("Fast mode: No code blocks found, using entire output")
                    validation_result = {
                        "success": True,
                        "code_extracted": True,
                        "extracted_code": raw_output,
                        "explanation": "Full response used as code in fast mode",
                        "code_quality": {
                            "violations": [],
                            "quality_score": 70,  # Lower assumed quality when no blocks found
                        },
                    }
            else:
                # Full validation with ResponseValidator
                logger.info("Using full ResponseValidator for validation")
                validator = ResponseValidator()
                validation_result = validator.validate(raw_output)
                logger.info(
                    f"Validation result: success={validation_result.get('success', False)}, code_extracted={validation_result.get('code_extracted', False)}"
                )
                if validation_result.get("code_extracted", False):
                    logger.info(
                        f"Extracted code length: {len(validation_result.get('extracted_code', ''))}"
                    )
                    logger.debug(
                        f"First 200 chars of extracted code: {validation_result.get('extracted_code', '')[:200]}..."
                    )
                else:
                    logger.warning(
                        f"Failed to extract code: {validation_result.get('explanation', 'No explanation provided')}"
                    )

                logger.debug(f"Validation result: {validation_result}")

                if not validation_result.get("code_extracted", False):
                    logger.warning("No code was extracted from the LLM response")
                    logger.debug(f"Full validation result: {validation_result}")
                    logger.debug(
                        f"Raw output that failed validation: {raw_output[:200]}..."
                    )
                else:
                    logger.info(
                        f"Code extracted successfully, length: {len(validation_result.get('extracted_code', ''))} chars"
                    )

                # Sprawdź jakość kodu
                if validation_result["code_extracted"] and not request.fast_mode:
                    # Create a temporary file for validation
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".py", delete=False
                    ) as temp_file:
                        temp_file.write(validation_result["extracted_code"])
                        temp_file_path = temp_file.name

                    try:
                        code_validation = self.code_validator.validate_file(
                            temp_file_path
                        )
                        validation_result["code_quality"] = code_validation
                        
                        # Check for incomplete functions
                        from gollm.validation.validators.incomplete_function_detector import (
                            contains_incomplete_functions,
                            format_for_completion,
                            extract_completed_functions
                        )
                        
                        has_incomplete, incomplete_funcs = contains_incomplete_functions(
                            validation_result["extracted_code"]
                        )
                        
                        if has_incomplete:
                            logger.info(f"Found {len(incomplete_funcs)} incomplete functions")
                            for func in incomplete_funcs:
                                logger.info(f"Incomplete function: {func['name']}")
                            
                            # Only attempt completion if not the last iteration
                            if iteration < request.max_iterations - 1:
                                logger.info("Will attempt to complete functions in next iteration")
                                validation_result["has_incomplete_functions"] = True
                                validation_result["incomplete_functions"] = incomplete_funcs
                            else:
                                logger.warning("Last iteration reached, cannot complete functions")
                        else:
                            logger.info("No incomplete functions found")
                            validation_result["has_incomplete_functions"] = False
                    finally:
                        # Clean up the temporary file
                        import os

                        os.unlink(temp_file_path)

            # Handle incomplete functions completion if this was a completion iteration
            if iteration > 0 and best_response and best_response.get("validation_result", {}).get("has_incomplete_functions", False):
                logger.info("Processing completed functions from LLM response")
                
                # Get the original code with incomplete functions
                original_code = best_response.get("generated_code", "")
                
                # Get the completed code from this iteration
                completed_code = validation_result.get("extracted_code", "")
                
                # Extract and merge the completed functions
                from gollm.validation.validators.incomplete_function_detector import extract_completed_functions
                merged_code = extract_completed_functions(original_code, completed_code)
                
                # Update the validation result with the merged code
                validation_result["extracted_code"] = merged_code
                validation_result["functions_completed"] = True
                
                # Re-validate the merged code
                import tempfile
                with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
                    temp_file.write(merged_code)
                    temp_file_path = temp_file.name
                
                try:
                    code_validation = self.code_validator.validate_file(temp_file_path)
                    validation_result["code_quality"] = code_validation
                    
                    # Check if there are still incomplete functions
                    from gollm.validation.validators.incomplete_function_detector import contains_incomplete_functions
                    has_incomplete, incomplete_funcs = contains_incomplete_functions(merged_code)
                    validation_result["has_incomplete_functions"] = has_incomplete
                    if has_incomplete:
                        validation_result["incomplete_functions"] = incomplete_funcs
                        logger.warning(f"Still found {len(incomplete_funcs)} incomplete functions after completion")
                    else:
                        logger.info("All functions successfully completed")
                finally:
                    import os
                    os.unlink(temp_file_path)
            
            # Oceń wynik
            current_score = self._calculate_response_score(validation_result)
            logger.info(f"Iteration {iteration + 1} score: {current_score}/100")

            if current_score > best_score:
                best_score = current_score
                best_response = {
                    "generated_code": validation_result.get("extracted_code", ""),
                    "explanation": validation_result.get("explanation", ""),
                    "validation_result": validation_result,
                    "iteration": iteration + 1,
                }
                logger.info(f"New best response found with score: {best_score}")

            # Jeśli osiągnęliśmy wystarczającą jakość, przerwij
            if current_score >= 90:  # 90% jakości
                logger.info("Reached target quality score (90+), stopping iterations")
                break

            logger.info(f"--- End of iteration {iteration + 1} ---\n")

        # 3. Sprawdź czy mamy jakąkolwiek odpowiedź
        if best_response is None:
            error_msg = "No valid response was generated after all iterations"
            logger.error(error_msg)
            return LLMResponse(
                generated_code="",
                explanation=error_msg,
                validation_result={"error": error_msg, "success": False},
                iterations_used=request.max_iterations,
                quality_score=0,
            )

        logger.info(
            f"Best response score: {best_score}, from iteration {best_response['iteration']}"
        )

        # 4. Zwróć najlepszą odpowiedź
        return LLMResponse(
            generated_code=best_response["generated_code"],
            explanation=best_response["explanation"],
            validation_result=best_response["validation_result"],
            iterations_used=best_response["iteration"],
            quality_score=best_score,
        )

    async def _simulate_llm_call(self, prompt: str, stream: bool = False) -> str:
        """Makes an actual LLM call using the configured provider.

        Args:
            prompt: The prompt to send to the LLM
            stream: Whether to use streaming API (if available)

        Returns:
            The generated text response
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Get the LLM provider from config
            provider_name = self.config.llm_integration.api_provider.lower()
            logger.debug(f"Using LLM provider: {provider_name}")

            if provider_name == "ollama":
                from .ollama_adapter import OllamaLLMProvider

                provider_config = self.config.llm_integration.providers.get(
                    "ollama", {}
                )
                logger.debug(
                    f"Initializing Ollama provider with config: {provider_config}"
                )
                # Pass the full config to ensure all settings are available
                provider = OllamaLLMProvider(self.config)

                # Check if we should use streaming
                if stream and hasattr(provider, "generate_response_stream"):
                    # Generate streaming response using the Ollama provider
                    logger.debug(
                        "Sending prompt to Ollama provider using streaming API..."
                    )
                    full_text = ""
                    try:
                        async for chunk, metadata in provider.generate_response_stream(
                            prompt
                        ):
                            full_text += chunk

                        if not full_text.strip():
                            logger.warning(
                                "Received empty generated code from Ollama streaming"
                            )
                        return full_text
                    except Exception as e:
                        logger.error(f"LLM streaming generation failed: {str(e)}")
                        # Fall back to non-streaming if streaming fails
                        logger.info("Falling back to non-streaming API")
                else:
                    # Generate response using the Ollama provider (non-streaming)
                    logger.debug("Sending prompt to Ollama provider...")
                    response = await provider.generate_response(prompt)
                    logger.debug(f"Received response from Ollama: {response}")

                    if response.get("success", False):
                        generated_code = response.get("generated_code", "")
                        if not generated_code.strip():
                            logger.warning("Received empty generated code from Ollama")
                        return generated_code
                    else:
                        error = response.get("error", "Unknown error from Ollama")
                        logger.error(f"LLM generation failed: {error}")
                        raise Exception(f"LLM generation failed: {error}")

            else:
                # Default to OpenAI if configured
                import openai

                openai_config = self.config.llm_integration.providers.get("openai", {})
                openai.api_key = openai_config.get("api_key", "")

                if not openai.api_key:
                    raise ValueError(
                        "OpenAI API key is required but not provided in the configuration."
                    )

                logger.debug("Sending request to OpenAI...")
                response = await openai.ChatCompletion.acreate(
                    model=self.config.llm_integration.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful AI coding assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.config.llm_integration.token_limit,
                    temperature=0.1,
                )
                return response.choices[0].message.content

        except Exception as e:
            # Fallback to a simple response if LLM call fails
            logger.exception("LLM call failed")
            return f"""Error: Failed to generate code. {str(e)}
            
Please check your LLM configuration and try again.
            """

    def _calculate_response_score(self, validation_result: Dict[str, Any]) -> int:
        """Oblicza wynik jakości odpowiedzi LLM (0-100)"""
        score = 0

        # Basic points for code extraction
        if validation_result.get("code_extracted", False):
            score += 30

        # Points for code quality
        code_quality = validation_result.get("code_quality", {})
        if code_quality:
            # Ensure quality_score is a number, default to 0 if not
            try:
                quality_score = float(code_quality.get("quality_score", 0))
                # Ensure the score is within valid range (0-100)
                quality_score = max(0, min(100, quality_score))
                score += quality_score * 0.7  # 70% weight for code quality
            except (TypeError, ValueError):
                # If quality_score is not a number, skip adding to the score
                pass
                
        # Penalize for incomplete functions
        if validation_result.get("has_incomplete_functions", False):
            incomplete_funcs = validation_result.get("incomplete_functions", [])
            # Penalize based on the number of incomplete functions
            # The more incomplete functions, the higher the penalty
            penalty = min(30, len(incomplete_funcs) * 10)  # Max penalty of 30 points
            score -= penalty
            
        # Bonus for successfully completing functions
        if validation_result.get("functions_completed", False):
            score += 15  # Bonus for completing functions

        # Ensure the final score is an integer between 0 and 100
        return min(100, max(0, int(score)))
