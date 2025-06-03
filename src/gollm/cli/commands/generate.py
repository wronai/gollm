"""Code generation commands for GoLLM CLI."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from ..utils.file_handling import save_generated_files, suggest_filename
from ..utils.formatting import format_quality_score
from ...core.session_manager import SessionManager
from ...core.session_models import GollmSession, GenerationStep # For type hinting and creating steps

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
@click.option(
    "--save-session",
    type=click.Path(dir_okay=False, writable=True),
    help="Save the generation session to a JSON file."
)
@click.option(
    "--load-session",
    type=click.Path(dir_okay=False, readable=True, exists=True),
    help="Load a previous generation session from a JSON file and continue."
)
@click.pass_context
def generate_command(
    ctx: click.Context,
    request: str,
    output: Optional[str],
    critical: bool,
    no_todo: bool,
    fast: bool,
    iterations: int,
    adapter_type: str,
    use_streaming: bool,
    use_grpc: bool,
    no_tests: bool,
    no_auto_complete: bool,
    no_execute_test: bool,
    no_auto_fix: bool,
    max_fix_attempts: int,
    save_session: Optional[str], # Populated by @click.option for --save-session
    load_session: Optional[str]  # Populated by @click.option for --load-session
) -> None:
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

    gollm_session: Optional[GollmSession] = None
    session_manager = SessionManager()

    if load_session:
        logger.info(f"Loading session from: {load_session}")
        gollm_session = session_manager.load_session(Path(load_session))
        if not gollm_session:
            logger.error("Failed to load session. Exiting.")
            ctx.exit(1)
        
        # Override CLI parameters with loaded session's context if needed, or use them to inform
        # For now, let's assume we primarily use the loaded session's state and original request.
        # The 'request' argument might be ignored or used as a new prompt for continuation.
        request = gollm_session.original_request # Or a new request for continuation
        # Potentially update other CLI params from gollm_session.cli_context
        iterations = gollm_session.cli_context.iterations # Example
        # ... and so on for other relevant params
        logger.info(f"Resuming session for request: '{request}'")
        # output_path might need to be re-evaluated or taken from session
        if gollm_session.cli_context.output_path:
            output_path = Path(gollm_session.cli_context.output_path)
        else:
            # Fallback if not in session, though it should be if saved properly
            output_path = Path(output) if output else Path(suggest_filename(request))

    else:
        logger.info(f"Received generation request: '{request}'")
        # Determine output path for new session
        if output:
            output_path = Path(output)
        else:
            # New logic: suggest_filename now returns a directory name
            project_dir_name = suggest_filename(request)
            output_path = Path(project_dir_name) # This is the project directory

        # Create CLI context for a new session
        cli_params_for_session = {
            'request': request,
            'output_path': str(output_path),
            'iterations': iterations,
            'fast': fast,
            'auto_complete': not no_auto_complete,
            'execute_test': not no_execute_test,
            'auto_fix_execution': not no_auto_fix,
            'max_fix_attempts': max_fix_attempts,
            'tests': not no_tests,
            'adapter_type': adapter_type,
            'model_name': ctx.obj.get("MODEL_NAME"), # Assuming model name is in context
            'temperature': ctx.obj.get("TEMPERATURE"), # Assuming temperature is in context
            # 'context_files' would need to be passed if used
        }
        gollm_session = session_manager.create_new_session(request, cli_params_for_session)

    logger.info(f"Effective output path: {output_path}")
    logger.info(f"Iterations: {iterations}")

    if use_grpc:
        logging.info("Using gRPC for faster communication with Ollama")
    else:
        logging.info(f"Using {adapter_type} adapter for Ollama communication")

    async def run_generation():
        is_website = ctx.obj.get("is_website_project", False)
        suggested_name = suggest_filename(request, is_website)

        # Set up output path - always create a directory structure
        project_dir = output_path
        
        # Create the project directory if it doesn't exist
        if not project_dir.exists():
            project_dir.mkdir(parents=True, exist_ok=True)
            
        # Determine the main file name based on the content to be generated
        if is_website:
            # For websites, use app.py as the main file
            main_script_path = project_dir / "app.py"
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
                
            main_script_path = project_dir / file_name

        try:
            # Add context about the project structure
            if is_website:
                context["project_structure"] = {
                    "type": "website",
                    "frontend": "templates/",
                    "backend": "app.py",
                    "static": "static/",
                }

            # Pass the whole session object to the orchestrator
            response = await gollm.handle_code_generation_request(
                gollm_session, # Pass the entire session object
                cli_provided_context=ctx.obj, # Pass click context obj for runtime params
                # output_path, project_name, main_file_name are now part of session.cli_context or derived
            )

            # Save all generated files
            saved_files = await save_generated_files(
                response.generated_code,
                main_script_path,
                context.get("validation_options", {}),
            )
            
            # If test code was generated, save it as a separate file in a tests directory
            test_files = []
            if hasattr(response, 'test_code') and response.test_code:
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
                    response.test_code, # Changed from result.test_code
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
            quality_score = format_quality_score(response.quality_score)

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
            if response.validation_result.get("code_quality", {}).get("violations"):
                for v in response.validation_result["code_quality"]["violations"]:
                    validation_issues.append(f"{v.type}: {v.message}")

            # Show code validation issues from our validator
            if (
                hasattr(response, "code_validation_issues")
                and response.code_validation_issues
            ):
                validation_issues.extend(response.code_validation_issues)

            # Display all validation issues
            if validation_issues:
                click.echo("\n🔍 Found the following issues:")
                for issue in validation_issues:
                    click.echo(f"  - {issue}")
            
            # Show information about incomplete functions and their completion status
            if hasattr(response, "has_incomplete_functions") and response.has_incomplete_functions:
                if hasattr(response, "has_completed_functions") and response.has_completed_functions:
                    click.echo("\n🔄 Detected and automatically completed incomplete functions!")
                    if hasattr(response, "still_has_incomplete_functions") and response.still_has_incomplete_functions:
                        click.echo(f"⚠️ Still found {len(response.still_incomplete_functions)} functions that couldn't be fully completed.")
                        for func in response.still_incomplete_functions:
                            click.echo(f"  - {func['name']}")
                    else:
                        click.echo("✅ All functions were successfully completed.")
                else:
                    click.echo("\n⚠️ Detected incomplete functions but auto-completion was disabled:")
                    for func in response.incomplete_functions:
                        click.echo(f"  - {func['name']}")
                    click.echo("💡 Run with auto-completion enabled to complete these functions automatically.")
            
            # Show information about code execution testing and fixing
            if hasattr(response, "execution_tested") and response.execution_tested:
                if hasattr(response, "execution_successful") and response.execution_successful:
                    if hasattr(response, "execution_fixed") and response.execution_fixed:
                        click.echo(f"\n👍 Successfully fixed code execution errors after {response.execution_fix_attempts} attempts!")
                    else:
                        click.echo("\n✅ Code executed successfully on first attempt!")
                else:
                    click.echo("\n⛔ Code execution failed with errors:")
                    for i, error in enumerate(response.execution_errors):
                        if i < 3:  # Show at most 3 errors to avoid cluttering the output
                            click.echo(f"  - Attempt {i+1}: {error}")
                    if len(response.execution_errors) > 3:
                        click.echo(f"  ... and {len(response.execution_errors) - 3} more errors")
                    
                    if hasattr(response, "execution_fix_attempts") and response.execution_fix_attempts > 0:
                        click.echo(f"🔧 Made {response.execution_fix_attempts} attempts to fix the code, but errors persist.")
                        click.echo("💡 You may need to manually fix the code or try again with different options.")

            # If we had to extract code from a prompt-like response, notify the user
            if (
                hasattr(response, "extracted_from_prompt")
                and response.extracted_from_prompt
            ):
                click.echo(
                    "\n⚠️ Note: The generated content appeared to contain non-code text."
                )
                click.echo("    Code was automatically extracted from the response.")
                click.echo("    Please verify the generated code is correct.")

            # If we had to fix syntax errors, notify the user
            if hasattr(response, "fixed_syntax") and response.fixed_syntax:
                click.echo(
                    "\n⚠️ Note: Syntax errors were automatically fixed in the generated code."
                )

            # If the response was detected as thinking-style output
            if hasattr(response, "validation_result") and response.validation_result.get(
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
            if hasattr(response, "validation_result") and response.validation_result.get(
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
            if hasattr(response, "validation_result") and response.validation_result.get(
                "critical_issues"
            ):
                click.echo(
                    "\n❌ Critical validation issues prevented saving the generated code."
                )
                click.echo("    The LLM output could not be parsed as valid code.")
                click.echo(
                    "    Try running the command again or refining your request."
                )
                for issue in response.validation_result.get("critical_issues", []):
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

            # Check if this is a response from a timeout with additional information
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

    # Save the session if requested, after all generation steps are complete
    if save_session and gollm_session:
        logger.info(f"Saving session to: {save_session}")
        session_manager.save_session(gollm_session, Path(save_session))
