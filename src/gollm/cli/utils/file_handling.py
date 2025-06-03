"""File handling utilities for CLI."""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


import logging
import os
from pathlib import Path

# Import code validator
from ...validation.code_validator import validate_and_extract_code

logger = logging.getLogger('gollm.cli.file_handling')

async def save_generated_files(generated_code: str, base_path: Path) -> List[str]:
    """Save generated code to appropriate files, handling multi-file output.
    
    Args:
        generated_code: Generated code content, possibly with file markers
        base_path: Base path to save files to
        
    Returns:
        List of saved file paths
    """
    saved_files = []
    
    # Check for multi-file format (files separated by --- filename.ext ---)
    if '--- ' in generated_code and '\n' in generated_code:
        files_section = generated_code.strip().split('--- ')[1:]
        
        for file_section in files_section:
            if '\n' not in file_section:
                continue
                
            file_header, *file_content = file_section.split('\n', 1)
            file_path = base_path / file_header.strip()
            file_content = '\n'.join(file_content).strip()
            
            # Validate code before saving
            file_extension = file_path.suffix.lstrip('.')
            is_valid, validated_content, issues = validate_and_extract_code(file_content, file_extension)
            
            if not is_valid:
                logger.warning(f"Invalid code detected for {file_path}: {', '.join(issues)}")
                logger.warning("Attempting to extract valid code from content...")
                
            if issues:
                logger.info(f"Code validation issues for {file_path}: {', '.join(issues)}")
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the validated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(validated_content)
            saved_files.append(str(file_path))
    else:
        # Single file output - validate code first
        file_extension = base_path.suffix.lstrip('.')
        is_valid, validated_content, issues = validate_and_extract_code(generated_code, file_extension)
        
        if not is_valid:
            logger.warning(f"Invalid code detected for {base_path}: {', '.join(issues)}")
            logger.warning("Attempting to extract valid code from content...")
            
        if issues:
            logger.info(f"Code validation issues for {base_path}: {', '.join(issues)}")
        
        # Save the validated content
        base_path.parent.mkdir(parents=True, exist_ok=True)
        with open(base_path, 'w', encoding='utf-8') as f:
            f.write(validated_content)
        saved_files.append(str(base_path))
        
    return saved_files


def suggest_filename(request_text: str, is_website: bool = False) -> str:
    """Generate a filename or directory name based on the request text.
    
    Args:
        request_text: The text of the request
        is_website: Whether this is a website project
        
    Returns:
        Suggested filename or directory name
    """
    clean_name = request_text.lower().replace(' ', '_')
    clean_name = ''.join(c if c.isalnum() or c == '_' else '' for c in clean_name)
    clean_name = '_'.join(filter(None, clean_name.split('_')))
    
    if is_website:
        return clean_name  # Directory for website projects
    return f"{clean_name}.py"


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(config_path: str, config: Dict[str, Any]) -> None:
    """Save configuration to file.
    
    Args:
        config_path: Path to config file
        config: Configuration dictionary
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
