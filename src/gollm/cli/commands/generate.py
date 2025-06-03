"""Code generation commands for GoLLM CLI."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..utils.file_handling import save_generated_files, suggest_filename
from ..utils.formatting import format_quality_score

logger = logging.getLogger("gollm.commands.generate")


@click.command("generate")
@click.argument("request")
@click.option("--output", "-o", help="Output file or directory path")
@click.option("--critical", is_flag=True, help="Mark as high priority task")
@click.option("--no-todo", is_flag=True, help="Skip creating a TODO item")
@click.option(
    "--fast", "-f", is_flag=True, help="Use fast mode with minimal validation"
)
@click.option(
    "--iterations", "-i", default=6, type=int, help="Number of generation iterations"
)
@click.option(
    "--adapter-type",
    type=click.Choice(["http", "grpc", "modular"]),
    default="modular",
    help="Adapter type for Ollama communication",
)
@click.option(
    "--use-streaming",
    is_flag=True,
    default=True,
    help="Use streaming API for faster response times",
)
@click.option(
    "--use-grpc",
    is_flag=True,
    help="Use gRPC for faster communication with Ollama (deprecated, use --adapter-type grpc)",
)
@click.option(
    "--no-tests",
    is_flag=True,
    help="Disable automatic test generation",
)
@click.option(
    "--no-auto-complete",
    is_flag=True,
    help="Disable automatic completion of incomplete functions",
)
@click.option(
    "--no-execute-test",
    is_flag=True,
    help="Disable automatic execution testing of generated code",
)
@click.option(
    "--no-auto-fix",
    is_flag=True,
    help="Disable automatic fixing of execution errors",
)
@click.option(
    "--max-fix-attempts",
    type=int,
    default=3,
    help="Maximum number of attempts to fix execution errors (default: 3)",
)
@click.pass_context
def generate_command(
    ctx,
    request,
    output,
    critical,
    no_todo,
    fast,
    iterations,
    adapter_type,
    use_streaming,
    use_grpc,
    no_tests,
    no_auto_complete,
    no_execute_test,
    no_auto_fix,
    max_fix_attempts,
):
    """Generate code using LLM with quality validation.

    For website projects, specify a directory as output to generate multiple files.
    Example: gollm generate "create website with Flask and React" -o my_website/
    """
    gollm = ctx.obj["gollm"]

    context = {
        "is_critical": critical,
        "related_files": [output] if output else [],
        "is_website_project": any(
            keyword in request.lower()
            for keyword in [
                "website",
                "web app",
                "webapp",
                "frontend",
                "backend",
                "api",
            ]
        ),
        "fast_mode": fast,
        "max_iterations": 1 if fast else iterations,
        "adapter_type": adapter_type,
        "use_streaming": use_streaming,
        "use_grpc": use_grpc,
        "generate_tests": not no_tests,  # Enable test generation by default
        "auto_complete_functions": not no_auto_complete,  # Enable auto-completion by default
        "execute_test": not no_execute_test,  # Enable execution testing by default
        "auto_fix_execution": not no_auto_fix,  # Enable auto-fixing by default
        "max_fix_attempts": max_fix_attempts,  # Maximum fix attempts
    }

    # Set environment variables for adapter type and streaming
    import os

    os.environ["OLLAMA_ADAPTER_TYPE"] = adapter_type
    os.environ["GOLLM_USE_STREAMING"] = str(use_streaming).lower()

    # Log adapter and streaming information
    logging.info(f"Using {adapter_type} adapter for Ollama communication")
    if use_streaming and adapter_type == "modular":
        logging.info("Streaming enabled for faster response times")

    if no_todo:
        context["skip_todo"] = True

    # Log mode information
    if fast:
        logging.info("Using fast mode with minimal validation")
    else:
        logging.info(f"Using standard mode with up to {iterations} iterations")

    if use_grpc:
        logging.info("Using gRPC for faster communication with Ollama")
    else:
        logging.info(f"Using {adapter_type} adapter for Ollama communication")

    async def run_generation():
        is_website = context.get("is_website_project", False)
        suggested_name = suggest_filename(request, is_website)

        # Set up output path - always create a directory structure
        project_dir = Path(output) if output else Path(suggested_name)
        
        # Create the project directory if it doesn't exist
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            
        # Determine the main file name based on the content to be generated
        if is_website:
            # For websites, use app.py as the main file
            output_path = project_dir / "app.py"
        else:
            # For other code, determine an appropriate main file name
            # based on what we're likely generating
            if any(keyword in request.lower() for keyword in ["class", "processor", "manager", "service"]):
                # If generating a class, name the file after the class
                class_name = None
                for word in request.lower().split():
                    if word in ["class", "processor", "manager", "service"]:
                        # Try to find the class name in the request
                        idx = request.lower().split().index(word)
                        if idx > 0:
                            class_name = request.lower().split()[idx-1]
                        elif idx < len(request.lower().split()) - 1:
                            class_name = request.lower().split()[idx+1]
                
                if class_name:
                    file_name = f"{class_name.lower()}.py"
                else:
                    file_name = "main.py"
            elif any(keyword in request.lower() for keyword in ["function", "utility", "util", "helper"]):
                # If generating utility functions
                file_name = "utils.py"
            else:
                # Default to main.py
                file_name = "main.py"
                
            output_path = project_dir / file_name

        try:
            # Add context about the project structure
            if is_website:
                context["project_structure"] = {
                    "type": "website",
                    "frontend": "templates/",
                    "backend": "app.py",
                    "static": "static/",
                }

            result = await gollm.handle_code_generation(request, context=context)

            # Save all generated files
            saved_files = await save_generated_files(
                result.generated_code,
                output_path,
                context.get("validation_options", {}),
            )
            
            # If test code was generated, save it as a separate file in a tests directory
            test_files = []
            if hasattr(result, 'test_code') and result.test_code:
                # Create a tests directory inside the project directory
                tests_dir = project_dir / "tests"
                tests_dir.mkdir(exist_ok=True)
                
                # Determine the test file path
                if output_path.suffix == '.py':
                    # For Python files, use test_filename.py naming convention in the tests directory
                    test_file_name = f"test_{output_path.stem}.py"
                else:
                    # For other files, append _test to the filename
                    test_file_name = f"{output_path.stem}_test{output_path.suffix}"
                
                test_file_path = tests_dir / test_file_name
                
                # Save the test code
                test_files = await save_generated_files(
                    result.test_code,
                    test_file_path,
                    context.get("validation_options", {}),
                )
                
                # Add test files to the list of saved files
                saved_files.extend(test_files)
                
                # Create an __init__.py file in the tests directory to make it a proper package
                init_file = tests_dir / "__init__.py"
                if not init_file.exists():
                    with open(init_file, 'w') as f:
                        f.write("# Test package for generated code\n")
                    saved_files.append(str(init_file))

            # Show results
            quality_score = format_quality_score(result.quality_score)

            if not saved_files:
                click.echo(f"\n⚠️ No files were saved! {quality_score}")
                click.echo("  The generated content could not be validated as code.")
                click.echo(
                    "  Try providing a more specific request or check the logs for details."
                )
            elif len(saved_files) > 1:
                click.echo(f"\n✨ Generated {len(saved_files)} files! {quality_score}")
                for i, file_path in enumerate(saved_files, 1):
                    file_icon = "📄" if file_path.endswith(".py") else "📝"
                    click.echo(f"  {i}. {file_icon} {file_path}")
            else:
                file_icon = "📄" if str(output_path).endswith(".py") else "📝"
                click.echo(
                    f"\n✨ Generation complete! {quality_score} {file_icon} {saved_files[0]}"
                )

            # Show next steps for website projects
            if is_website and len(saved_files) > 1:
                click.echo("\n🚀 Next steps:")
                click.echo(f"  $ cd {output_path.parent}")
                click.echo("  $ pip install -r requirements.txt")
                click.echo("  $ python app.py")

            # If no files were saved, show suggestions for improving the request
            if not saved_files:
                click.echo("\n💡 Suggestions to improve results:")
                click.echo("  1. Be more specific in your request")
                click.echo("  2. Include programming language in your request")
                click.echo("  3. Break down complex requests into smaller parts")
                click.echo(
                    "  4. Check if the LLM is in thinking mode rather than code generation mode"
                )

            # Show validation issues from code quality
            validation_issues = []
            if result.validation_result.get("code_quality", {}).get("violations"):
                for v in result.validation_result["code_quality"]["violations"]:
                    validation_issues.append(f"{v.type}: {v.message}")

            # Show code validation issues from our validator
            if (
                hasattr(result, "code_validation_issues")
                and result.code_validation_issues
            ):
                validation_issues.extend(result.code_validation_issues)

            # Display all validation issues
            if validation_issues:
                click.echo("\n🔍 Found the following issues:")
                for issue in validation_issues:
                    click.echo(f"  - {issue}")
            
            # Show information about incomplete functions and their completion status
            if hasattr(result, "has_incomplete_functions") and result.has_incomplete_functions:
                if hasattr(result, "has_completed_functions") and result.has_completed_functions:
                    click.echo("\n🔄 Detected and automatically completed incomplete functions!")
                    if hasattr(result, "still_has_incomplete_functions") and result.still_has_incomplete_functions:
                        click.echo(f"⚠️ Still found {len(result.still_incomplete_functions)} functions that couldn't be fully completed.")
                        for func in result.still_incomplete_functions:
                            click.echo(f"  - {func['name']}")
                    else:
                        click.echo("✅ All functions were successfully completed.")
                else:
                    click.echo("\n⚠️ Detected incomplete functions but auto-completion was disabled:")
                    for func in result.incomplete_functions:
                        click.echo(f"  - {func['name']}")
                    click.echo("💡 Run with auto-completion enabled to complete these functions automatically.")
            
            # Show information about code execution testing and fixing
            if hasattr(result, "execution_tested") and result.execution_tested:
                if hasattr(result, "execution_successful") and result.execution_successful:
                    if hasattr(result, "execution_fixed") and result.execution_fixed:
                        click.echo(f"\n👍 Successfully fixed code execution errors after {result.execution_fix_attempts} attempts!")
                    else:
                        click.echo("\n✅ Code executed successfully on first attempt!")
                else:
                    click.echo("\n⛔ Code execution failed with errors:")
                    for i, error in enumerate(result.execution_errors):
                        if i < 3:  # Show at most 3 errors to avoid cluttering the output
                            click.echo(f"  - Attempt {i+1}: {error}")
                    if len(result.execution_errors) > 3:
                        click.echo(f"  ... and {len(result.execution_errors) - 3} more errors")
                    
                    if hasattr(result, "execution_fix_attempts") and result.execution_fix_attempts > 0:
                        click.echo(f"🔧 Made {result.execution_fix_attempts} attempts to fix the code, but errors persist.")
                        click.echo("💡 You may need to manually fix the code or try again with different options.")

            # If we had to extract code from a prompt-like response, notify the user
            if (
                hasattr(result, "extracted_from_prompt")
                and result.extracted_from_prompt
            ):
                click.echo(
                    "\n⚠️ Note: The generated content appeared to contain non-code text."
                )
                click.echo("    Code was automatically extracted from the response.")
                click.echo("    Please verify the generated code is correct.")

            # If we had to fix syntax errors, notify the user
            if hasattr(result, "fixed_syntax") and result.fixed_syntax:
                click.echo(
                    "\n⚠️ Note: Syntax errors were automatically fixed in the generated code."
                )

            # If the response was detected as thinking-style output
            if hasattr(result, "validation_result") and result.validation_result.get(
                "thinking_detected"
            ):
                click.echo(
                    "\n⚠️ Note: The LLM output appeared to be in 'thinking mode' rather than code generation."
                )
                click.echo(
                    "    This often happens when the model is explaining its thought process."
                )
                click.echo(
                    "    Try running the command again or being more specific in your request."
                )

            # If the response was detected as prompt-like but no code could be extracted
            if hasattr(result, "validation_result") and result.validation_result.get(
                "prompt_no_code"
            ):
                click.echo(
                    "\n⚠️ Note: The LLM output appeared to be a prompt response without any code."
                )
                click.echo(
                    "    Try adding 'in Python' or another language to your request."
                )
                click.echo(
                    "    Example: 'Create a user class in Python' instead of 'Create a user class'"
                )
                click.echo(
                    "    You can also try running the command again with more specific instructions."
                )

            # If the response had critical validation issues
            if hasattr(result, "validation_result") and result.validation_result.get(
                "critical_issues"
            ):
                click.echo(
                    "\n❌ Critical validation issues prevented saving the generated code."
                )
                click.echo("    The LLM output could not be parsed as valid code.")
                click.echo(
                    "    Try running the command again or refining your request."
                )
                for issue in result.validation_result.get("critical_issues", []):
                    click.echo(f"    - {issue}")

                click.echo("    Please verify the generated code is correct.")
                click.echo(
                    "    You may want to regenerate if the code doesn't work as expected."
                )

            # Show adapter type information if using gRPC
            if use_grpc:
                click.echo("\n🚀 Used gRPC for faster communication with Ollama")

        except Exception as e:
            click.echo(f"\n❌ Error during generation: {str(e)}")

            # Check if this is a result from a timeout with additional information
            if hasattr(e, "__dict__") and isinstance(
                getattr(e, "__dict__", None), dict
            ):
                error_dict = e.__dict__
                if error_dict.get("timeout") and "suggestions" in error_dict:
                    click.echo("\n⏱️ Request timed out - Troubleshooting suggestions:")
                    for suggestion in error_dict["suggestions"]:
                        click.echo(f"  • {suggestion}")
                    if "details" in error_dict:
                        click.echo(f"\nDetails: {error_dict['details']}")

            logger.exception("Generation failed")

    asyncio.run(run_generation())
