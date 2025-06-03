"""Response validation for LLM outputs."""

import logging
import os
import re
import tempfile
from typing import Dict, Any, Optional, Tuple, List

from gollm.validation.validators import CodeValidator
from gollm.validation.code_validator import validate_and_extract_code, looks_like_prompt

logger = logging.getLogger('gollm.orchestrator.validator')

class ResponseValidator:
    """Validates and processes LLM responses."""
    
    def __init__(self, config, code_validator: Optional[CodeValidator] = None):
        """Initialize the response validator.
        
        Args:
            config: Application configuration
            code_validator: Optional code validator instance
        """
        self.config = config
        self.code_validator = code_validator or CodeValidator(config)
    
    async def validate_response(
        self,
        llm_output: Any,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate and process an LLM response.
        
        Args:
            llm_output: Raw output from the LLM (can be str or dict)
            context: Additional context for validation
            
        Returns:
            Dictionary with validation results
        """
        if not llm_output:
            return {
                'success': False,
                'error': 'Empty LLM output',
                'code_extracted': False
            }
            
        # Extract text from response if it's a dictionary
        if isinstance(llm_output, dict):
            llm_output = llm_output.get('generated_text', '')
        
        # If still not a string, convert to string
        if not isinstance(llm_output, str):
            llm_output = str(llm_output)
        
        try:
            # Try to extract code and explanation using the legacy method first
            code, explanation = self._extract_code_and_explanation(llm_output)
            
            # Determine file extension from context or default to Python
            file_extension = 'py'
            if context and 'output_path' in context:
                output_path = context['output_path']
                if isinstance(output_path, str) and '.' in output_path:
                    file_extension = output_path.split('.')[-1]
            
            # Apply our enhanced code validation
            validation_issues = []
            extracted_from_prompt = False
            fixed_syntax = False
            thinking_detected = False
            prompt_no_code = False
            critical_issues = []
            
            # Check if the content looks like a prompt rather than code
            if looks_like_prompt(code):
                logger.warning("Generated content appears to be a prompt rather than code")
                extracted_from_prompt = True
                validation_issues.append("Content appears to be a prompt or natural language text, not code")
                
                # Check for thinking patterns in the original response
                thinking_patterns = [
                    r'<think>\s*([\s\S]*)',
                    r'\[thinking\]\s*([\s\S]*)',
                    r'\*\*thinking\*\*\s*([\s\S]*)',
                    r'Let me think about this[\s\S]*',
                    r'I need to create[\s\S]*',
                    r'Let\'s tackle this[\s\S]*',
                    r'Okay, let\'s tackle this[\s\S]*'
                ]
                
                for pattern in thinking_patterns:
                    if re.search(pattern, llm_output, re.IGNORECASE):
                        thinking_detected = True
                        logger.warning("Detected thinking-style output in LLM response")
                        break
            
            # Extract validation options from context
            validation_options = {}
            if context and 'validation_options' in context:
                validation_options = context.get('validation_options', {})
                
                # Log validation options if present
                if validation_options.get('strict_validation'):
                    logger.info("Using strict validation mode - no automatic fixing of syntax errors")
                if validation_options.get('allow_prompt_text'):
                    logger.info("Prompt-like text will be allowed in generated code")
                if validation_options.get('skip_validation'):
                    logger.warning("Code validation is disabled - this may result in invalid code being saved")
            
            # Validate and potentially fix the code
            is_valid, validated_code, issues = validate_and_extract_code(code, file_extension, validation_options)
            
            if issues:
                validation_issues.extend(issues)
                
            if not is_valid and not validated_code:
                logger.error("Failed to extract valid code from LLM response")
                prompt_no_code = True
                critical_issues.append("No valid code could be extracted from the response")
                if thinking_detected:
                    critical_issues.append("LLM output appears to be in 'thinking mode' rather than code generation")
                
                return {
                    'success': False,
                    'error': 'No valid code could be extracted from response',
                    'code_extracted': False,
                    'explanation': explanation or 'No explanation provided',
                    'code_validation_issues': validation_issues,
                    'thinking_detected': thinking_detected,
                    'prompt_no_code': prompt_no_code,
                    'critical_issues': critical_issues
                }
            
            # Check if we had to fix syntax errors
            if validated_code != code and is_valid:
                fixed_syntax = True
                logger.info("Fixed syntax errors in generated code")
                code = validated_code
            
            # Validate code quality if we have a validator
            code_quality = {}
            if self.code_validator:
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{file_extension}', delete=False) as temp_file:
                    temp_file.write(code)
                    temp_file_path = temp_file.name
                
                try:
                    code_quality = self.code_validator.validate_file(temp_file_path)
                finally:
                    os.unlink(temp_file_path)
            
            # If we had to fix syntax errors, track that
            if any(issue.startswith('syntax_error') for issue in issues):
                fixed_syntax = True
                
            # Return the validated code with all metadata
            return {
                'success': True,
                'code': validated_code,
                'explanation': explanation,
                'code_extracted': True,
                'extracted_code': validated_code,
                'code_quality': code_quality,
                'extracted_from_prompt': extracted_from_prompt,
                'fixed_syntax': fixed_syntax,
                'code_validation_issues': validation_issues,
                'thinking_detected': thinking_detected,
                'prompt_no_code': prompt_no_code,
                'critical_issues': critical_issues
            }
            
        except Exception as e:
            logger.exception("Error validating LLM response")
            return {
                'success': False,
                'error': f"Validation error: {str(e)}",
                'code_extracted': False
            }
    
    def _extract_code_and_explanation(self, text: str) -> Tuple[str, str]:
        """Extract code and explanation from LLM response.
        
        This method is designed to be extremely permissive in what it accepts as code,
        especially for minimal examples like 'print("Hello, World!")'.
        
        Args:
            text: Raw LLM response text
            
        Returns:
            Tuple of (code, explanation)
        """
        if not text:
            return '', 'No content in response'
        
        # Clean up the text first
        text = text.strip()
        
        # Check for thinking-style output (common in LLM responses)
        thinking_patterns = [
            r'<think>\s*([\s\S]*)',
            r'\[thinking\]\s*([\s\S]*)',
            r'\*\*thinking\*\*\s*([\s\S]*)',
            r'Let me think about this[\s\S]*',
            r'I need to create[\s\S]*',
            r'Let\'s tackle this[\s\S]*',
            r'Okay, let\'s tackle this[\s\S]*'
        ]
        
        for pattern in thinking_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug("Detected thinking-style output in LLM response")
                # This is clearly a prompt-like response, not code
                return '', f'Thinking-style output detected: {text[:50]}...'
        
        # Check for common non-code indicators at the beginning of the text
        non_code_indicators = [
            r'^\s*Okay,\s',
            r'^\s*I will\s',
            r'^\s*Here\s',
            r'^\s*Let me\s',
            r'^\s*First,\s',
            r'^\s*To create\s',
            r'^\s*Now I\'ll\s',
            r'^\s*I\'m going to\s'
        ]
        
        for pattern in non_code_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug("Detected natural language beginning in LLM response")
                # This might be a prompt-like response, but we'll still try to extract code later
                break
        
        # First, check for the absolute simplest case - just a print statement
        simple_print = re.search(r'^print\([\'"].*?[\"\']\)\s*$', text, re.MULTILINE)
        if simple_print:
            return simple_print.group(0).strip(), 'Simple print statement extracted'
            
        # Check for print statement with possible whitespace before/after
        simple_print_ws = re.search(r'^\s*print\([\'"].*?[\"\']\)\s*$', text, re.MULTILINE)
        if simple_print_ws:
            return simple_print_ws.group(0).strip(), 'Simple print statement with whitespace extracted'
        
        # Check for print statement with newlines
        simple_print_nl = re.search(r'^\s*print\([\'"].*?[\"\']\)\s*$', text, re.MULTILINE | re.DOTALL)
        if simple_print_nl:
            return simple_print_nl.group(0).strip(), 'Simple print statement with newlines extracted'
        
        # Try to find code blocks with different formats
        explanation = ''
        
        # Try to find Python code blocks with or without language specifier, handling various formats
        code_block_patterns = [
            # Triple backticks with optional language specifier
            r'```(?:python\n)?\s*([\s\S]*?)\s*```',
            # Code fences with indentation
            r'(?m)^(?:> )?(?:\s*\n)?( {4,}|\t+)([\s\S]*?)(?=\n\s*\n|\Z)',
            # Inline code with backticks
            r'`([^`]+)`',
            # Any line that looks like code
            r'(?m)^(?!\s*#|\s*-\s|\s*\*\s|\s*$).+$'
        ]
        
        for pattern in code_block_patterns:
            code_block_match = re.search(pattern, text, re.MULTILINE)
            if code_block_match:
                # Get the first non-None group that matched
                code = next((g for g in code_block_match.groups() if g), '').strip()
                if code:
                    # Clean up the code
                    code = re.sub(r'^\s*>>>\s*', '', code, flags=re.MULTILINE)  # Remove Python REPL prompts
                    code = re.sub(r'^\s*\$\s*', '', code, flags=re.MULTILINE)  # Remove shell prompts
                    code = re.sub(r'\n\s*\n', '\n', code).strip()  # Remove empty lines
                    
                    # Extract any explanation before the code block
                    explanation = text[:code_block_match.start()].strip()
                    
                    # If we have a print statement after cleaning, return it
                    if re.match(r'^print\([\'"].*?[\"\']\)$', code):
                        return code, explanation or 'Simple print statement extracted from code block'
                        
                    return code, explanation or 'Code block extracted from response'
        
        # If no code blocks found, try to extract just the code
        # Look for Python code patterns (imports, def, class, etc.)
        code_patterns = [
            # Function or class definition
            r'(?s)(?:(?:def|class)\s+\w+\s*[(:].*?)(?=\n\s*\n|\Z)',
            # Import statements
            r'(?m)^(?:from\s+\S+\s+import\s+\S+|import\s+\S+(?:\s*,\s*\S+)*)\s*$',
            # Print statements or simple expressions
            r'(?m)^(?:print\([^\n]*\)|\w+\s*=\s*[^\n]+|\w+\([^\n]*\))\s*$',
            # Any line that looks like code
            r'(?m)^(?!\s*#|\s*$).+$'
        ]
        
        # Try each pattern in order of specificity
        for pattern in code_patterns:
            code_matches = re.finditer(pattern, text, re.MULTILINE)
            code_lines = []
            
            for match in code_matches:
                line = match.group(0).strip()
                # Skip lines that look like explanations
                if not line or line.startswith('#') or '```' in line:
                    continue
                code_lines.append(line)
            
            if code_lines:
                code = '\n'.join(code_lines).strip()
                # Remove any remaining markdown code block markers
                code = re.sub(r'^```(?:python)?\n?|```$', '', code, flags=re.MULTILINE).strip()
                if code:
                    return code, 'Code extracted from response text'
        
        # If we still don't have code, check if the entire text looks like code
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # If it's a single line that looks like code
            if len(lines) == 1 and any(c in lines[0] for c in ['(', ')', '=', 'import', 'print']):
                return lines[0], 'Single line of code extracted'
            # If it's multiple lines that look like code
            if len(lines) > 1 and any('def ' in line or 'class ' in line or 'import ' in line or 'print(' in line for line in lines):
                return '\n'.join(lines), 'Multiple lines of code extracted'
        
        # If no code found, return empty code and full text as explanation
        return '', text or 'No code found in response'
    
    def _calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """Calculate a quality score based on validation results.
        
        Args:
            validation_result: Validation result dictionary
            
        Returns:
            Quality score between 0 and 100
        """
        if not validation_result.get('code_extracted', False):
            return 0.0
        
        score = 30.0  # Base score for having code
        
        # Add points based on code quality
        code_quality = validation_result.get('code_quality', {})
        if code_quality:
            # Add up to 70 points based on code quality (0-100 scaled to 0-70)
            quality_score = float(code_quality.get('quality_score', 0))
            score += min(70.0, max(0.0, quality_score * 0.7))
        
        # Penalize for errors/warnings
        if 'errors' in code_quality and code_quality['errors']:
            error_penalty = min(30.0, len(code_quality['errors']) * 5)
            score = max(0.0, score - error_penalty)
            
        if 'warnings' in code_quality and code_quality['warnings']:
            warning_penalty = min(15.0, len(code_quality['warnings']) * 2)
            score = max(0.0, score - warning_penalty)
        
        return min(100.0, max(0.0, score))
