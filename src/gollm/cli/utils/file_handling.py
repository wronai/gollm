"""File handling utilities for CLI."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import validators
from ...validation.code_validator import validate_and_extract_code
from ...validation.output_validator import validate_saved_code

logger = logging.getLogger("gollm.cli.file_handling")


async def save_generated_files(
    generated_code: str, base_path: Path, validation_options: Dict[str, bool] = None
) -> List[str]:
    """Save generated code to appropriate files, handling multi-file output.
    
    With the new directory structure, base_path is expected to be a file path
    within a project directory. Files with special markers will be saved in the
    appropriate locations within the project directory.

    Args:
        generated_code: Generated code content, possibly with file markers
        base_path: Base path to save files to (should be within a project directory)
        validation_options: Options for code validation

    Returns:
        List of saved file paths
    """
    saved_files = []

    # Get the project directory (parent of the base_path)
    project_dir = base_path.parent
    
    # Check for multi-file format (files separated by --- filename.ext ---)
    if "--- " in generated_code and "\n" in generated_code:
        files_section = generated_code.strip().split("--- ")[1:]

        for file_section in files_section:
            if "\n" not in file_section:
                continue

            file_header, *file_content = file_section.split("\n", 1)
            file_name = file_header.strip()
            file_content = "\n".join(file_content).strip()
            
            # Determine the appropriate path based on file type
            if file_name.endswith(".py"):
                if file_name.startswith("test_"):
                    # Test files go in the tests directory
                    tests_dir = project_dir / "tests"
                    tests_dir.mkdir(parents=True, exist_ok=True)
                    file_path = tests_dir / file_name
                    
                    # Create __init__.py if it doesn't exist
                    init_file = tests_dir / "__init__.py"
                    if not init_file.exists():
                        with open(init_file, 'w') as f:
                            f.write("# Test package for generated code\n")
                        saved_files.append(str(init_file))
                else:
                    file_path = project_dir / file_name
            elif any(file_name.endswith(ext) for ext in [".html", ".css", ".js"]):
                # Web files go in appropriate directories
                if file_name.endswith(".html"):
                    templates_dir = project_dir / "templates"
                    templates_dir.mkdir(parents=True, exist_ok=True)
                    file_path = templates_dir / file_name
                elif file_name.endswith(".css") or file_name.endswith(".js"):
                    static_dir = project_dir / "static"
                    static_dir.mkdir(parents=True, exist_ok=True)
                    file_path = static_dir / file_name
                else:
                    file_path = project_dir / file_name
            else:
                # Other files go in the project root
                file_path = project_dir / file_name

            # Validate code before saving
            file_extension = file_path.suffix.lstrip(".")
            is_valid, validated_content, issues = validate_and_extract_code(
                file_content, file_extension, validation_options
            )

            if not is_valid:
                logger.warning(
                    f"Invalid code detected for {file_path}: {', '.join(issues)}"
                )
                logger.warning("Attempting to extract valid code from content...")

                # If no valid code could be extracted, skip saving this file
                if not validated_content or validated_content.strip() == "":
                    logger.error(
                        f"Skipping file {file_path}: Could not extract any valid code"
                    )
                    continue

            if issues:
                logger.info(
                    f"Code validation issues for {file_path}: {', '.join(issues)}"
                )

            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save the validated content
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(validated_content)
            saved_files.append(str(file_path))

            # Validate that the saved file matches the expected content
            is_valid, validation_issues, details = validate_saved_code(
                file_content, str(file_path)
            )
            if not is_valid:
                logger.warning(
                    f"Output validation failed for {file_path}: {', '.join(validation_issues)}"
                )
                if (
                    "escape_sequences_found" in details
                    and details["escape_sequences_found"]
                ):
                    logger.warning(
                        f"Found escape sequences in original content: {details['escape_sequences_found']}"
                    )
                if "diff_summary" in details and details["diff_summary"]:
                    logger.debug(
                        f"Diff between original and saved content:\n{details['diff_summary']}"
                    )
            else:
                logger.info(f"Output validation passed for {file_path}")
    else:
        # Single file output - validate code first
        file_extension = base_path.suffix.lstrip(".")
        is_valid, validated_content, issues = validate_and_extract_code(
            generated_code, file_extension, validation_options
        )

        if not is_valid:
            logger.warning(
                f"Invalid code detected for {base_path}: {', '.join(issues)}"
            )
            logger.warning("Attempting to extract valid code from content...")

            # If no valid code could be extracted, don't save the file
            if not validated_content or validated_content.strip() == "":
                logger.error(
                    f"Not saving file {base_path}: Could not extract any valid code"
                )
                return saved_files
                
        # Determine if we need to create additional files based on code content
        # For example, if we detect a class definition, we might want to create a separate file for it
        main_file_path = base_path
        additional_files = []
        
        # Check if we're generating a class that should have its own file
        import re
        class_match = re.search(r'class\s+([A-Za-z0-9_]+)', validated_content)
        if class_match and base_path.name == "main.py":
            class_name = class_match.group(1)
            # Create a file named after the class
            class_file_path = base_path.parent / f"{class_name.lower()}.py"
            
            # If the class is the main content, use the class file as the main file
            if validated_content.strip().startswith("class "):
                main_file_path = class_file_path
            else:
                # Otherwise, add it as an additional file
                additional_files.append((class_file_path, validated_content))
                
        # Create a README.md file with project description
        import datetime
        readme_path = base_path.parent / "README.md"
        if not readme_path.exists():
            project_name = base_path.parent.name.replace("_", " ").title()
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            readme_content = f"# {project_name}\n\nGenerated by GoLLM on {current_date}\n\n## Files\n\n- {base_path.name}: Main implementation file\n"
            additional_files.append((readme_path, readme_content))

        if issues:
            logger.info(f"Code validation issues for {base_path}: {', '.join(issues)}")

        # Save the validated content to the main file path
        main_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(main_file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(validated_content)
        saved_files.append(str(main_file_path))
        
        # Save any additional files
        for file_path, content in additional_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            saved_files.append(str(file_path))

        # Validate that the saved file matches the expected content
        is_valid, validation_issues, details = validate_saved_code(
            generated_code, str(base_path)
        )
        if not is_valid:
            logger.warning(
                f"Output validation failed for {base_path}: {', '.join(validation_issues)}"
            )
            if (
                "escape_sequences_found" in details
                and details["escape_sequences_found"]
            ):
                logger.warning(
                    f"Found escape sequences in original content: {details['escape_sequences_found']}"
                )
            if "diff_summary" in details and details["diff_summary"]:
                logger.debug(
                    f"Diff between original and saved content:\n{details['diff_summary']}"
                )
        else:
            logger.info(f"Output validation passed for {base_path}")

    return saved_files


def suggest_filename(request_text: str, is_website: bool = False) -> str:
    """Generate a directory name based on the request text.
    
    Instead of creating a single file with a long descriptive name,
    we now create a directory with a meaningful name and place the
    main code files inside with more specific names like 'main.py'
    or names that reflect their function.

    Args:
        request_text: The text of the request
        is_website: Whether this is a website project

    Returns:
        Suggested directory name
    """
    # Extract main concept from the request
    words = request_text.lower().split()
    
    # Remove common verbs and articles that don't contribute to the name
    common_words = ["create", "make", "build", "implement", "develop", "a", "an", "the", "with"]
    filtered_words = [w for w in words if w not in common_words]
    
    # If we filtered out too much, use original words
    if len(filtered_words) < 2 and len(words) > 2:
        filtered_words = words[:3]  # Use first 3 words
    
    # Join the words to create a clean name
    clean_name = "_".join(filtered_words)
    clean_name = "".join(c if c.isalnum() or c == "_" else "" for c in clean_name)
    clean_name = "_".join(filter(None, clean_name.split("_")))
    
    # Limit the length to avoid excessively long directory names
    if len(clean_name) > 30:
        clean_name = clean_name[:30]
    
    # Always return a directory name
    return clean_name


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

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config_path: str, config: Dict[str, Any]) -> None:
    """Save configuration to file.

    Args:
        config_path: Path to config file
        config: Configuration dictionary
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
