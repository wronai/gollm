# src/gollm/llm/orchestrator.py
import asyncio
import json
import logging # Add logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime # For timestamps

from gollm.validation.validators import CodeValidator
from ..core.session_models import GollmSession, GenerationStep, SessionState, CliContext # Session models

from .context_builder import ContextBuilder
from .prompt_formatter import PromptFormatter
from .response_validator import ResponseValidator


@dataclass
class LLMRequest:
    user_request: str
    # context: Dict[str, Any] # Context will be part of GollmSession
    gollm_session: GollmSession # Pass the whole session
    # session_id: str # session_id is part of GollmSession
    max_iterations: int = 3
    fast_mode: bool = False
    current_iteration_type: str = 'initial_code' # To describe the purpose of this LLM call


@dataclass
class LLMResponse:
    generated_code_files: Dict[str, str] = field(default_factory=dict) # {filepath: code}
    explanation: Optional[str] = None
    validation_result: Optional[Dict[str, Any]] = None
    iterations_used: int = 0
    quality_score: Optional[int] = None # Quality score might not always be applicable
    test_code_files: Dict[str, str] = field(default_factory=dict) # {filepath: code}
    has_incomplete_functions: bool = False
    incomplete_functions: Optional[List[Dict[str, str]]] = None
    has_completed_functions: bool = False
    still_has_incomplete_functions: bool = False
    still_incomplete_functions: Optional[List[Dict[str, str]]] = None
    execution_tested: bool = False
    execution_successful: bool = False
    execution_errors: Optional[List[str]] = None
    execution_fixed: bool = False
    execution_fix_attempts: int = 0
    # Add a field to store the final session state if needed by CLI
    final_session_state: Optional[SessionState] = None


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
        self.logger = logging.getLogger(self.__class__.__name__)

    async def handle_code_generation_request(
        self, gollm_session: GollmSession, cli_provided_context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Główny punkt wejścia dla generowania kodu przez LLM"""
        # cli_provided_context might contain overrides or additional runtime info
        # For now, we primarily rely on gollm_session.cli_context for core parameters
        # and gollm_session.current_state for resuming.

        effective_context = gollm_session.cli_context.model_dump() # Start with session's CLI context
        if cli_provided_context:
            effective_context.update(cli_provided_context) # Overlay any CLI runtime specifics

        # If it's a new session (iteration 0 and no history), log initial request
        if not gollm_session.generation_history and gollm_session.current_state.current_iteration == 0:
            initial_step = GenerationStep(
                step_type="session_start",
                prompt_to_llm=gollm_session.original_request,
                feedback_provided=f"CLI Context: {gollm_session.cli_context.model_dump_json(indent=2)}"
            )
            gollm_session.generation_history.append(initial_step)

            
        # Extract parameters from effective_context (derived from gollm_session.cli_context)
        user_request = gollm_session.original_request # The core user prompt
        generate_tests = effective_context.get("generate_tests", True) # Default from CliContext
        max_iterations = effective_context.get("iterations", 6) # Default from CliContext
        # validation_mode = effective_context.get("validation_mode", "strict") # If you have this
        # skip_validation = effective_context.get("skip_validation", False) # If you have this
        use_streaming = effective_context.get("use_streaming", True) # Assuming this is a general setting
        fast_mode = effective_context.get("fast_mode", False) # Default from CliContext

        # TODO: Todo manager integration needs to be adapted if it relies on old context structure
        # For now, focusing on core LLM interaction with session

        # If fast mode is enabled, limit to 1 main generation iteration (session's iterations might be higher for overall task)
        # This 'max_iterations' here is for the _process_llm_request call, not total session iterations.
        current_llm_max_iterations = 1 if fast_mode else max_iterations # For the immediate LLM call

        # Create the LLMRequest for the main generation task
        # We start at gollm_session.current_state.current_iteration
        # The _process_llm_request will handle its own internal looping up to current_llm_max_iterations
        llm_req = LLMRequest(
            user_request=user_request, # This might be refined based on current_state for retries/resumes
            gollm_session=gollm_session,
            max_iterations=current_llm_max_iterations,
            fast_mode=fast_mode,
            current_iteration_type='initial_code_generation' # Or 'resume_code_generation'
        )

        # Initialize an LLMResponse object to aggregate results
        # This will be populated by _process_llm_request and subsequent steps
        final_llm_response = LLMResponse(
            iterations_used=gollm_session.current_state.current_iteration
        )

        try:
            # Process the main code generation request using the current session state
            # _process_llm_request will now directly update gollm_session's history and state
            processed_response_data = await self._process_llm_request(
                llm_req, use_streaming=use_streaming
            )
            
            # _process_llm_request should return the primary generated code and explanation
            # And update gollm_session.current_state.current_code_files, .generation_history etc.
            final_llm_response.generated_code_files = gollm_session.current_state.current_code_files
            # final_llm_response.explanation = processed_response_data.get('explanation') # Assuming _process_llm_request returns this
            final_llm_response.iterations_used = gollm_session.current_state.current_iteration
            final_llm_response.quality_score = gollm_session.current_state.get('quality_score') # If available
            
            # Check for incomplete functions in the generated code
            from gollm.validation.validators.validation_coordinator import check_for_incomplete_functions
            from gollm.validation.validators.incomplete_function_detector import format_for_completion, extract_completed_functions

            # Assume generated_code is now a dict of files {filepath: content}
            # We need to decide which file to check for incomplete functions or iterate through all
            # For simplicity, let's assume a primary code file for now or that _process_llm_request identifies it.
            primary_code_content = ""
            if gollm_session.current_state.current_code_files:
                # Heuristic: find a .py file, or the first file if only one.
                # This needs to be more robust, perhaps storing main_file_path in session state.
                py_files = [content for path, content in gollm_session.current_state.current_code_files.items() if path.endswith('.py')]
                if py_files:
                    primary_code_content = py_files[0]
                elif len(gollm_session.current_state.current_code_files) == 1:
                    primary_code_content = list(gollm_session.current_state.current_code_files.values())[0]
            
            has_incomplete_functions, incomplete_functions_list = check_for_incomplete_functions(primary_code_content)
            final_llm_response.has_incomplete_functions = has_incomplete_functions
            final_llm_response.incomplete_functions = incomplete_functions_list
            
            # If incomplete functions are found and auto-completion is enabled, complete them
            auto_complete_enabled = effective_context.get("auto_complete", True)
            
            if has_incomplete_functions and auto_complete_enabled:
                self.logger.info(f"Found {len(incomplete_functions_list)} incomplete functions. Triggering auto-completion...")
                
                # Format the code for completion
                completion_prompt = format_for_completion(incomplete_functions_list, primary_code_content)
                
                # Create a completion request - this will also update gollm_session
                completion_llm_req = LLMRequest(
                    user_request=completion_prompt,
                    gollm_session=gollm_session, # Pass the same session
                    max_iterations=1, # Typically 1 attempt for completion
                    fast_mode=fast_mode,
                    current_iteration_type='auto_completion'
                )
                
                # Process the completion request
                # _process_llm_request needs to handle this type and update the correct file in current_code_files
                completion_response_data = await self._process_llm_request(
                    completion_llm_req, use_streaming=use_streaming
                )

                # Assume _process_llm_request updated gollm_session.current_state.current_code_files
                # and recorded a GenerationStep for the completion attempt.
                # The 'merged_code' logic might now live inside _process_llm_request or be handled by it.
                # For now, let's assume primary_code_content is updated in the session.
                updated_primary_code_content = "" # Re-fetch from session
                if gollm_session.current_state.current_code_files:
                    py_files = [content for path, content in gollm_session.current_state.current_code_files.items() if path.endswith('.py')]
                    if py_files: updated_primary_code_content = py_files[0]
                    elif len(gollm_session.current_state.current_code_files) == 1: updated_primary_code_content = list(gollm_session.current_state.current_code_files.values())[0]

                final_llm_response.has_completed_functions = True # Mark that we attempted
                
                # Check if there are still incomplete functions after the completion attempt
                still_has_incomplete, still_incomplete_list = check_for_incomplete_functions(updated_primary_code_content)
                if still_has_incomplete:
                    self.logger.warning(f"Still found {len(still_incomplete_list)} incomplete functions after auto-completion.")
                    final_llm_response.still_has_incomplete_functions = True
                    final_llm_response.still_incomplete_functions = still_incomplete_list
                else:
                    self.logger.info("Successfully completed all incomplete functions.")
                    final_llm_response.still_has_incomplete_functions = False
            elif has_incomplete_functions:
                self.logger.info(f"Found {len(incomplete_functions_list)} incomplete functions, but auto-completion is disabled.")
                # Already set: final_llm_response.has_incomplete_functions = True
                # Already set: final_llm_response.incomplete_functions = incomplete_functions_list
            else:
                final_llm_response.has_incomplete_functions = False
            
            # Test code execution and fix errors if needed
            from gollm.validation.validators.code_executor import execute_python_code, format_error_for_completion
            
            # Check if execution testing is enabled
            execute_test_enabled = effective_context.get("execute_test", True)
            auto_fix_execution_enabled = effective_context.get("auto_fix_execution", True)
            max_execution_fix_attempts = effective_context.get("max_fix_attempts", 5)
            execution_timeout_seconds = effective_context.get("execution_timeout", 15)

            # Again, assuming primary_code_content is the one to test, or iterate through all relevant files
            # This part needs careful handling for multi-file projects.
            # For now, we'll use the 'updated_primary_code_content' from the auto-completion step if it ran,
            # otherwise the 'primary_code_content' from initial generation.
            code_to_execute = updated_primary_code_content if final_llm_response.has_completed_functions else primary_code_content
            
            if execute_test_enabled and code_to_execute and code_to_execute.strip():
                # Only test Python code for now
                if code_to_execute.strip().startswith("#!/usr/bin/env python") or "def " in code_to_execute or "import " in code_to_execute:
                    self.logger.info("Testing code execution...")
                    final_llm_response.execution_tested = True
                    
                    # Execute the code with enhanced error handling
                    success, error_output, exec_stdout = execute_python_code(code_to_execute, timeout=execution_timeout_seconds)
                    final_llm_response.execution_successful = success
                    final_llm_response.execution_errors = [error_output] if error_output else []
                    gollm_session.current_state.last_error_context = error_output # Save last error

                    # Record execution attempt as a generation step
                    exec_step = GenerationStep(
                        step_type='execution_test',
                        generated_code_snapshot=gollm_session.current_state.current_code_files.copy(),
                        execution_results={'success': success, 'error': error_output, 'output': exec_stdout},
                        feedback_provided=f"Execution test performed. Success: {success}."
                    )
                    gollm_session.generation_history.append(exec_step)
                    
                    if success and exec_stdout:
                        self.logger.debug(f"Code execution output:\n{exec_stdout}")
                    
                    if not success and auto_fix_execution_enabled:
                        self.logger.info(f"Code execution failed with error: {error_output}. Attempting to fix...")
                        
                        for attempt in range(max_execution_fix_attempts):
                            gollm_session.current_state.current_fix_attempt = attempt + 1
                            final_llm_response.execution_fix_attempts += 1
                            
                            fix_prompt = format_error_for_completion(code_to_execute, error_output)
                            if attempt > 0 and final_llm_response.execution_errors:
                                prev_errors = ', '.join(final_llm_response.execution_errors[-min(3, len(final_llm_response.execution_errors)):])[:500]
                                fix_prompt += f"\n\nThis is fix attempt #{attempt+1}. Previous fix attempts failed with these errors:\n```\n{prev_errors}\n```\n\nPlease provide a more robust solution."

                            fix_llm_req = LLMRequest(
                                user_request=fix_prompt,
                                gollm_session=gollm_session,
                                max_iterations=1, # One attempt per fix call to LLM
                                fast_mode=fast_mode, # Or consider not using fast_mode for fixes
                                current_iteration_type='execution_fix_attempt'
                            )
                            
                            # _process_llm_request handles updating session state and history for the fix
                            fix_response_data = await self._process_llm_request(
                                fix_llm_req, use_streaming=use_streaming
                            )
                            
                            # Re-fetch the potentially fixed code from the session state
                            code_to_execute = "" # Re-fetch from session
                            if gollm_session.current_state.current_code_files:
                                py_f = [c for p, c in gollm_session.current_state.current_code_files.items() if p.endswith('.py')]
                                if py_f: code_to_execute = py_f[0]
                                elif len(gollm_session.current_state.current_code_files) == 1: code_to_execute = list(gollm_session.current_state.current_code_files.values())[0]

                            # Re-test execution
                            success, error_output, exec_stdout = execute_python_code(code_to_execute, timeout=execution_timeout_seconds)
                            final_llm_response.execution_successful = success
                            final_llm_response.execution_errors.append(error_output) if error_output else None
                            gollm_session.current_state.last_error_context = error_output

                            # Record this fix attempt and its execution result
                            fix_exec_step = GenerationStep(
                                step_type=f'execution_fix_attempt_result_after_attempt_{attempt+1}',
                                generated_code_snapshot=gollm_session.current_state.current_code_files.copy(),
                                execution_results={'success': success, 'error': error_output, 'output': exec_stdout},
                                feedback_provided=f"Execution test after fix attempt {attempt+1}. Success: {success}."
                            )
                            gollm_session.generation_history.append(fix_exec_step)

                            if success:
                                self.logger.info(f"Code execution succeeded after fix attempt {attempt + 1}.")
                                final_llm_response.execution_fixed = True
                                break # Exit fix loop
                            else:
                                self.logger.info(f"Fix attempt {attempt + 1} failed. Error: {error_output}")
                        

            # If test generation is enabled, generate tests for the code
            # This also needs to be adapted for multi-file and use the session
            if generate_tests and gollm_session.current_state.current_code_files:
                self.logger.info("Generating tests for the code...")
                # Assuming test generation is for the primary code content
                code_for_tests = code_to_execute # Use the latest version of the code
                
                test_generation_prompt = self.prompt_formatter.format_test_generation_prompt(
                    code_for_tests, user_request
                )
                test_llm_req = LLMRequest(
                    user_request=test_generation_prompt,
                    gollm_session=gollm_session,
                    max_iterations=1, 
                    fast_mode=fast_mode,
                    current_iteration_type='test_generation'
                )
                # _process_llm_request should handle saving test code to gollm_session.current_state.current_test_files
                test_response_data = await self._process_llm_request(
                    test_llm_req, use_streaming=use_streaming
                )
                final_llm_response.test_code_files = gollm_session.current_state.current_test_files
                self.logger.info("Tests generated successfully.")
            else:
                final_llm_response.test_code_files = {}

            # Update task status in todo manager (if used and adapted)
            # if self.todo_manager and self.current_task_id:
            #     self.todo_manager.update_task_status(self.current_task_id, "completed")

            gollm_session.current_state.is_complete = True # Mark session as processed for this run
            final_llm_response.final_session_state = gollm_session.current_state
            return final_llm_response

        except Exception as e:
            self.logger.error(f"Error during code generation: {e}", exc_info=True)
            # if self.todo_manager and self.current_task_id:
            #     self.todo_manager.update_task_status(self.current_task_id, "failed")
            
            # Record the error in session history
            error_step = GenerationStep(
                step_type='error',
                feedback_provided=f"Orchestrator error: {type(e).__name__} - {str(e)}"
            )
            gollm_session.generation_history.append(error_step)
            gollm_session.current_state.is_complete = True # Mark as complete due to error
            gollm_session.current_state.last_error_context = f"Orchestrator error: {type(e).__name__} - {str(e)}"

            # Return a partial response or raise exception
            return LLMResponse(
                explanation=f"Error: {e}",
                final_session_state=gollm_session.current_state
            )

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
