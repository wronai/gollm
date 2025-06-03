
# src/gollm/llm/response_validator.py
import re
import ast
from typing import Dict, Any, List, Optional

class ResponseValidator:
    """Waliduje odpowiedzi z LLM"""
    
    def __init__(self, config):
        self.config = config
    
    async def validate_response(self, llm_output: str) -> Dict[str, Any]:
        """Waliduje odpowiedź z LLM"""
        
        validation_result = {
            "raw_output": llm_output,
            "code_extracted": False,
            "extracted_code": "",
            "explanation": "",
            "code_blocks_found": 0,
            "syntax_valid": False,
            "violations": []
        }
        
        # 1. Wyodrębnij bloki kodu
        code_blocks = self._extract_code_blocks(llm_output)
        validation_result["code_blocks_found"] = len(code_blocks)
        
        if code_blocks:
            validation_result["code_extracted"] = True
            validation_result["extracted_code"] = code_blocks[0]  # Pierwszy blok
            
            # 2. Sprawdź składnię
            syntax_check = self._validate_syntax(code_blocks[0])
            validation_result["syntax_valid"] = syntax_check["valid"]
            if not syntax_check["valid"]:
                validation_result["violations"].append({
                    "type": "syntax_error",
                    "message": syntax_check["error"]
                })
        
        # 3. Wyodrębnij wyjaśnienie
        validation_result["explanation"] = self._extract_explanation(llm_output)
        
        return validation_result
    
    def _extract_code_blocks(self, text: str) -> List[str]:
        """Wyodrębnia bloki kodu z odpowiedzi LLM"""
        import logging
        logger = logging.getLogger('gollm.validator')
        logger.info(f"===== CODE EXTRACTION STARTED =====")
        
        # Log the input text for debugging
        logger.info(f"Extracting code blocks from text of length {len(text)}")
        logger.debug(f"Text first 200 chars: {text[:200]}...")
        logger.debug(f"Text last 200 chars: {text[-200:] if len(text) > 200 else text}")
        
        # Try to extract markdown code blocks with various formats
        # This handles both ```python and ``` formats, with optional language specifier
        code_blocks = re.findall(r'```(?:\w*)?\n(.+?)(?:\n```|$)', text, re.DOTALL)
        
        # Log how many blocks were found
        logger.info(f"Found {len(code_blocks)} code blocks using markdown pattern")
        
        # Log each code block found for debugging
        for i, block in enumerate(code_blocks):
            logger.info(f"Code block {i+1} length: {len(block)}")
            logger.debug(f"Code block {i+1} first 100 chars: {block[:100]}...")
            logger.debug(f"Code block {i+1} last 100 chars: {block[-100:] if len(block) > 100 else block}")
        
        # If we found code blocks, clean them up
        if code_blocks:
            # Clean up each code block
            cleaned_blocks = []
            for block in code_blocks:
                # Remove trailing whitespace and ensure it ends with a newline
                cleaned = block.rstrip() + '\n'
                cleaned_blocks.append(cleaned)
            return cleaned_blocks
        
        # If no code blocks found with markdown, try to extract code directly
        logger.info("No markdown code blocks found, trying to extract Python code directly")
        
        # Check if the text looks like Python code
        if self._looks_like_python(text):
            logger.info("Text appears to be Python code, using as-is")
            # Clean the text to make it more likely to be valid Python
            cleaned_text = self._clean_text_for_python(text)
            if cleaned_text:
                return [cleaned_text]
            
        # As a last resort, try to find Python-like patterns in the text
        logger.info("Attempting to find Python-like patterns in text")
        
        # Look for common Python patterns like class/def declarations
        python_patterns = re.findall(r'(?:class|def)\s+\w+\s*\([^)]*\):\s*(?:\n\s+.+)+', text, re.DOTALL)
        if python_patterns:
            logger.info(f"Found {len(python_patterns)} Python-like patterns")
            return python_patterns
            
        # If all else fails, log the issue and return an empty list
        logger.warning(f"Could not extract any code blocks from text: {text[:100]}...")
        return []
    
    def _looks_like_python(self, code: str) -> bool:
        """Sprawdza czy kod wygląda jak Python"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not code or not code.strip():
            logger.warning("Empty code provided to _looks_like_python")
            return False
            
        # More comprehensive list of Python keywords and patterns
        python_keywords = [
            'def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'return ',
            'with ', 'try:', 'except:', 'finally:', 'as ', 'in ', 'is ', 'not ', 'and ', 'or ',
            'print(', 'self.', '__init__', 'lambda ', 'async ', 'await ', 'yield ',
            # Common Python patterns
            ' = ', '==', '!=', '>=', '<=', '+=', '-=', '*=', '/=',
            # Common Python libraries
            'import os', 'import sys', 'import re', 'import json', 'import time',
            'import numpy', 'import pandas', 'import matplotlib', 'import requests'
        ]
        
        # Check for Python keywords
        has_keywords = any(keyword in code for keyword in python_keywords)
        
        # Check for Python indentation patterns (spaces at beginning of lines)
        indentation_pattern = re.search(r'\n\s{2,}\S', code)
        has_indentation = bool(indentation_pattern)
        
        # Check for Python docstrings
        docstring_pattern = re.search(r'""".*?"""', code, re.DOTALL)
        has_docstring = bool(docstring_pattern)
        
        # Check for Python function or class definitions
        definition_pattern = re.search(r'(def|class)\s+\w+\s*\(', code)
        has_definition = bool(definition_pattern)
        
        # Log the detection results
        if has_keywords or has_indentation or has_docstring or has_definition:
            logger.debug(f"Code looks like Python: keywords={has_keywords}, indentation={has_indentation}, docstring={has_docstring}, definition={has_definition}")
            return True
        else:
            logger.debug("Code does not appear to be Python")
            return False
    
    def validate_python_code(self, code: str) -> Dict[str, Any]:
        """Waliduje kod Python"""
        import logging
        logger = logging.getLogger('gollm.validator')
        logger.info(f"===== VALIDATING PYTHON CODE =====")
        logger.info(f"Code length: {len(code)}")
        logger.debug(f"Code first 100 chars: {code[:100]}...")
        logger.debug(f"Code last 100 chars: {code[-100:] if len(code) > 100 else code}")
        
        # Check if code looks like Python before parsing
        if not self._looks_like_python(code):
            logger.warning("Code does not appear to be Python based on heuristics")
            # Continue anyway, but log the warning
        
        # Use the enhanced syntax validation method
        is_valid, error_msg = self._validate_syntax(code)
        
        if is_valid:
            logger.info("✅ Python code validation successful")
            return {"valid": True, "error": None}
        else:
            logger.error(f"❌ Python code validation failed: {error_msg}")
            return {"valid": False, "error": error_msg}
    
    def _validate_syntax(self, code: str) -> Tuple[bool, str]:
        """Sprawdza składnię Python"""
        import logging
        logger = logging.getLogger('gollm.validator')
        
        logger.info(f"===== VALIDATING PYTHON SYNTAX =====")
        logger.info(f"Code length: {len(code)}")
        
        try:
            logger.info("Attempting to parse code with ast.parse")
            ast.parse(code)
            logger.info("✅ Syntax validation successful")
            return True, "Syntax is valid"
        except SyntaxError as e:
            logger.error(f"❌ Syntax error: {str(e)}")
            logger.debug(f"Error details: line {e.lineno}, column {e.offset}, {e.text}")
            # Log the problematic line and surrounding lines for context
            if e.lineno is not None:
                lines = code.split('\n')
                if 0 <= e.lineno - 1 < len(lines):
                    problem_line = lines[e.lineno - 1]
                    logger.error(f"Problem line ({e.lineno}): {problem_line}")
                    # Show surrounding lines for context
                    start = max(0, e.lineno - 3)
                    end = min(len(lines), e.lineno + 2)
                    for i in range(start, end):
                        if i != e.lineno - 1:  # Skip the problem line as we already showed it
                            logger.debug(f"Line {i+1}: {lines[i]}")
            return False, f"Syntax error: {str(e)}"
        except Exception as e:
            logger.error(f"❌ Error validating syntax: {str(e)}")
            return False, f"Error validating syntax: {str(e)}"
    
    def _clean_text_for_python(self, text: str) -> str:
        """Attempt to clean text to make it valid Python"""
        import logging
        logger = logging.getLogger('gollm.validator')
        logger.info(f"Attempting to clean text of length {len(text)} for Python parsing")
        
        # Remove common non-code elements
        # Remove markdown headers
        cleaned = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
        # Remove bullet points
        cleaned = re.sub(r'^\s*[-*]\s+', '', cleaned, flags=re.MULTILINE)
        # Remove numbered lists
        cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
        # Remove HTML-like tags
        cleaned = re.sub(r'<.*?>', '', cleaned)
        
        # Try to validate if it's Python code
        try:
            ast.parse(cleaned)
            logger.info("Successfully cleaned and parsed text as Python code")
            return cleaned.strip()
        except SyntaxError:
            # If full text doesn't parse, try to extract just the parts that look like code
            lines = cleaned.split('\n')
            code_lines = []
            current_block = []
            in_code_block = False
            
            for line in lines:
                stripped = line.strip()
                # Skip empty lines and obvious non-code lines
                if not stripped or stripped.startswith('#') or ':' in stripped and not any(kw in stripped for kw in ['if', 'else', 'elif', 'def', 'class', 'for', 'while', 'try', 'except']):
                    if in_code_block and current_block:
                        # End of a code block
                        code_lines.extend(current_block)
                        current_block = []
                        in_code_block = False
                    continue
                
                # Lines that look like code
                if any(kw in stripped for kw in ['def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'return ']):
                    in_code_block = True
                
                if in_code_block:
                    current_block.append(line)
            
            # Add any remaining code block
            if current_block:
                code_lines.extend(current_block)
            
            if code_lines:
                result = '\n'.join(code_lines)
                logger.info(f"Extracted {len(code_lines)} lines of potential Python code")
                return result.strip()
            
            logger.warning("Could not extract valid Python code from text")
            return ''
        except Exception as e:
            logger.warning(f"Error cleaning text for Python: {str(e)}")
            return ''

    def _extract_explanation(self, text: str) -> str:
        """Wyodrębnia wyjaśnienie z odpowiedzi LLM"""
        
        # Usuń bloki kodu
        text_without_code = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Wyczyść i zwróć
        explanation = text_without_code.strip()
        
        # Ogranicz długość
        if len(explanation) > 500:
            explanation = explanation[:497] + "..."
        
        return explanation