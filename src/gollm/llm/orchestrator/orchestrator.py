"""Main orchestrator for LLM-based code generation."""

import asyncio
import logging
import os
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    LLMRequest,
    LLMResponse,
    LLMIterationResult,
    LLMGenerationConfig
)
from .llm_client import LLMClient
from .response_validator import ResponseValidator
from ..context_builder import ContextBuilder
from ..prompt_formatter import PromptFormatter
from gollm.validation.validators import CodeValidator

logger = logging.getLogger('gollm.orchestrator')

class LLMOrchestrator:
    """Orchestrates the code generation process using LLMs."""
    
    def __init__(
        self,
        config: Any,
        code_validator: Optional[CodeValidator] = None,
        todo_manager: Any = None
    ):
        """Initialize the LLM orchestrator.
        
        Args:
            config: Application configuration
            code_validator: Optional code validator instance
            todo_manager: Optional todo manager for tracking tasks
        """
        self.config = config
        self.todo_manager = todo_manager
        self.current_task_id = None
        
        # Initialize components
        self.context_builder = ContextBuilder(config)
        self.prompt_formatter = PromptFormatter(config)
        self.response_validator = ResponseValidator(
            config,
            code_validator=code_validator or CodeValidator(config)
        )
    
    async def handle_code_generation_request(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """Handle a code generation request.
        
        Args:
            user_request: The user's request for code generation
            context: Additional context for the request
            
        Returns:
            LLMResponse with the generated code and metadata
        """
        context = context or {}
        
        # Create a task in the todo manager if available
        self._create_todo_task(user_request, context)
        
        try:
            # Create request object
            request = self._create_request(user_request, context)
            
            # Process the request
            response = await self._process_llm_request(request)
            
            # Update task with results if successful
            self._update_todo_task(response, context)
            
            return response
            
        except Exception as e:
            # Update task with error if something went wrong
            self._handle_error(e)
            raise
    
    async def _process_llm_request(self, request: LLMRequest) -> LLMResponse:
        """Process an LLM request with multiple iterations if needed."""
        logger.info(f"===== PROCESSING LLM REQUEST =====")
        logger.info(f"User request: {request.user_request[:100]}...")
        logger.info(f"Session ID: {request.session_id}")
        logger.info(f"Max iterations: {request.max_iterations}")
        logger.info(f"Context keys: {list(request.context.keys()) if request.context else []}")
        logger.debug(f"Full context: {request.context}")
        
        # Build context
        full_context = await self.context_builder.build_context(request.context)
        
        # Initialize tracking
        best_result = None
        best_score = 0
        
        # Run iterations
        for iteration in range(request.max_iterations):
            logger.info(f"\n--- Starting iteration {iteration + 1} ---")
            
            # Generate prompt
            prompt = self.prompt_formatter.create_prompt(
                request.user_request,
                full_context,
                iteration=iteration,
                previous_attempt=vars(best_result) if best_result else None
            )
            
            # Generate and validate response
            result = await self._run_llm_iteration(
                prompt=prompt,
                context=full_context,
                iteration=iteration
            )
            
            # Update best result if this one is better
            if result.score > best_score:
                best_score = result.score
                best_result = result
                logger.info(f"New best score: {best_score:.1f}")
            
            # Early exit if we've reached the target quality
            if best_score >= 90.0:  # TODO: Make configurable
                logger.info("Reached target quality score, stopping early")
                break
            
            logger.info(f"--- End of iteration {iteration + 1} ---\n")
        
        # Return the best response
        return self._create_final_response(best_result, request)
    
    async def _run_llm_iteration(
        self,
        prompt: str,
        context: Dict[str, Any],
        iteration: int
    ) -> LLMIterationResult:
        """Run a single LLM iteration and validate the response."""
        logger = logging.getLogger(__name__)
        logger.info(f"===== STARTING ITERATION {iteration + 1} =====")
        logger.info(f"Prompt length: {len(prompt)}")
        logger.debug(f"Prompt first 200 chars: {prompt[:200]}...")
        logger.debug(f"Prompt last 200 chars: {prompt[-200:] if len(prompt) > 200 else prompt}")
        logger.info(f"Context keys: {list(context.keys()) if context else []}")
        
        # Initialize LLM client
        logger.info("Initializing LLM client")
        async with LLMClient(self.config) as llm_client:
            # Generate response
            logger.info("Sending request to LLM")
            start_time = time.time()
            llm_output = await llm_client.generate(prompt, context)
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"Received LLM response in {duration:.2f}s")
            
            # Convert llm_output to string if it's not already
            if not isinstance(llm_output, str):
                logger.warning(f"LLM output is not a string, but {type(llm_output).__name__}. Converting to string.")
                llm_output = str(llm_output)
                
            logger.info(f"Response length: {len(llm_output)}")
            logger.debug(f"Response first 200 chars: {llm_output[:200]}...")
            logger.debug(f"Response last 200 chars: {llm_output[-200:] if len(llm_output) > 200 else llm_output}")
            
            # Validate response
            logger.info("Starting response validation")
            logger.info(f"Sending response of length {len(llm_output)} to validator")
            logger.debug(f"Response preview: {llm_output[:100]}...")
            
            validation_result = await self.response_validator.validate_response(
                llm_output,
                context
            )
            
            logger.info(f"Validation result: {validation_result['success']}")
            if 'code_blocks' in validation_result:
                logger.info(f"Found {len(validation_result['code_blocks'])} code blocks")
                for i, block in enumerate(validation_result['code_blocks']):
                    logger.info(f"Code block {i+1} length: {len(block)}")
                    logger.debug(f"Code block {i+1} preview: {block[:100]}...")
            
            # Calculate score
            score = self.response_validator._calculate_quality_score(validation_result)
            
            return LLMIterationResult(
                generated_code=validation_result.get('extracted_code', ''),
                explanation=validation_result.get('explanation', ''),
                validation_result=validation_result,
                score=score,
                iteration=iteration + 1
            )
    
    def _create_request(
        self,
        user_request: str,
        context: Dict[str, Any]
    ) -> LLMRequest:
        """Create an LLMRequest from user input."""
        import logging
        logger = logging.getLogger('gollm.orchestrator')
        logger.info(f"Creating LLM request for: {user_request[:100]}...")
        
        # Generate a unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Get max iterations from config or use default
        max_iterations = getattr(self.config, 'max_iterations', 3)
        
        # Create and return the request object
        return LLMRequest(
            user_request=user_request,
            context=context,
            session_id=session_id,
            max_iterations=max_iterations
        )
        
    def _create_final_response(
        self,
        best_result: Optional[LLMIterationResult],
        request: LLMRequest
    ) -> LLMResponse:
        """Create a final response from the best result."""
        if not best_result:
            error_msg = "No valid response was generated after all iterations"
            logger.error(error_msg)
            return LLMResponse(
                generated_code="",
                explanation=error_msg,
                validation_result={"error": error_msg, "success": False},
                iterations_used=request.max_iterations,
                quality_score=0
            )
        
        return LLMResponse(
            generated_code=best_result.generated_code,
            explanation=best_result.explanation,
            validation_result=best_result.validation_result,
            iterations_used=best_result.iteration,
            quality_score=best_result.score
        )
    
    def _create_todo_task(self, user_request: str, context: Dict[str, Any]) -> None:
        """Create a task in the todo manager if available."""
        if not self.todo_manager:
            return
            
        task_context = {
            'request': user_request,
            'context': context,
            'is_critical': context.get('is_critical', False),
            'related_files': context.get('related_files', [])
        }
        
        task = self.todo_manager.add_code_generation_task(user_request, task_context)
        self.current_task_id = task.id
    
    def _update_todo_task(self, response: LLMResponse, context: Dict[str, Any]) -> None:
        """Update the todo task with the generation results."""
        if not (self.todo_manager and self.current_task_id):
            return
            
        self.todo_manager.update_code_generation_task(
            self.current_task_id,
            {
                'generated_code': response.generated_code,
                'quality_score': response.quality_score,
                'violations': response.validation_result.get('violations', []),
                'output_file': context.get('output_file', 'unknown.py')
            }
        )
    
    def _handle_error(self, error: Exception) -> None:
        """Handle errors during request processing."""
        if self.todo_manager and self.current_task_id:
            self.todo_manager.update_code_generation_task(
                self.current_task_id,
                {'error': str(error)}
            )
        
        logger.exception("Error processing LLM request")
