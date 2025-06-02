"""Response validation for LLM outputs."""

import logging
import os
import re
import tempfile
from typing import Dict, Any, Optional, Tuple

from gollm.validation.validators import CodeValidator

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
            # Try to extract code and explanation
            code, explanation = self._extract_code_and_explanation(llm_output)
            
            if not code:
                return {
                    'success': False,
                    'error': 'No code block found in response',
                    'code_extracted': False,
                    'explanation': explanation or 'No explanation provided'
                }
            
            # Validate code quality if we have a validator
            code_quality = {}
            if self.code_validator:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                    temp_file.write(code)
                    temp_file_path = temp_file.name
                
                try:
                    code_quality = self.code_validator.validate_file(temp_file_path)
                finally:
                    os.unlink(temp_file_path)
            
            return {
                'success': True,
                'code_extracted': True,
                'extracted_code': code,
                'explanation': explanation,
                'code_quality': code_quality
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
        
        Args:
            text: Raw LLM response text
            
        Returns:
            Tuple of (code, explanation)
        """
        if not text:
            return '', 'No content in response'
        
        # Clean up the text first
        text = text.strip()
        
        # First, check for the simplest case - just a print statement
        simple_print = re.search(r'^print\([\'"].*?[\"\']\)\s*$', text, re.MULTILINE)
        if simple_print:
            return simple_print.group(0).strip(), 'Simple print statement extracted'
        
        # Try to find code blocks with different formats
        explanation = ''
        
        # Try to find the first Python code block (with or without language specifier)
        code_block_match = re.search(
            r'```(?:python\n)?\s*([\s\S]*?)\s*```', 
            text, 
            re.MULTILINE
        )
        
        if code_block_match:
            # Found a code block, extract it and any explanation before it
            code = code_block_match.group(1).strip()
            explanation = text[:code_block_match.start()].strip()
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
