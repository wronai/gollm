"""Code generation commands for GoLLM CLI."""

import asyncio
import click
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..utils.formatting import format_quality_score
from ..utils.file_handling import save_generated_files, suggest_filename

logger = logging.getLogger('gollm.commands.generate')

@click.command('generate')
@click.argument('request')
@click.option('--output', '-o', help='Output file or directory path')
@click.option('--critical', is_flag=True, help='Mark as high priority task')
@click.option('--no-todo', is_flag=True, help='Skip creating a TODO item')
@click.option('--fast', '-f', is_flag=True, help='Use fast mode with minimal validation')
@click.option('--iterations', '-i', default=3, type=int, help='Number of generation iterations')
@click.option('--adapter-type', type=click.Choice(['http', 'grpc']), default='http', 
              help='Adapter type for Ollama communication')
@click.option('--use-grpc', is_flag=True, help='Use gRPC for faster communication with Ollama')
@click.pass_context
def generate_command(ctx, request, output, critical, no_todo, fast, iterations, adapter_type, use_grpc):
    """Generate code using LLM with quality validation.
    
    For website projects, specify a directory as output to generate multiple files.
    Example: gollm generate "create website with Flask and React" -o my_website/
    """
    gollm = ctx.obj['gollm']
    
    context = {
        'is_critical': critical,
        'related_files': [output] if output else [],
        'is_website_project': any(keyword in request.lower() for keyword in 
                               ['website', 'web app', 'webapp', 'frontend', 'backend', 'api']),
        'fast_mode': fast,
        'max_iterations': 1 if fast else iterations,
        'adapter_type': adapter_type,
        'use_grpc': use_grpc
    }
    
    if no_todo:
        context['skip_todo'] = True
        
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
        is_website = context.get('is_website_project', False)
        suggested_name = suggest_filename(request, is_website)
        
        # Set up output path
        if output:
            output_path = Path(output)
            if is_website and not output_path.suffix:  # Directory for website
                output_path = output_path / 'app.py'  # Default main file
        else:
            output_path = Path(suggested_name)
        
        try:
            # Add context about the project structure
            if is_website:
                context['project_structure'] = {
                    'type': 'website',
                    'frontend': 'templates/',
                    'backend': 'app.py',
                    'static': 'static/'
                }
            
            result = await gollm.handle_code_generation(request, context=context)
            
            # Save all generated files
            saved_files = await save_generated_files(
                result.generated_code, 
                output_path
            )
            
            # Show results
            quality_score = format_quality_score(result.quality_score)
            
            if len(saved_files) > 1:
                click.echo(f"\n✨ Generated {len(saved_files)} files! {quality_score}")
                for i, file_path in enumerate(saved_files, 1):
                    file_icon = "📄" if file_path.endswith('.py') else "📝"
                    click.echo(f"  {i}. {file_icon} {file_path}")
            else:
                file_icon = "📄" if str(output_path).endswith('.py') else "📝"
                click.echo(f"\n✨ Generation complete! {quality_score} {file_icon} {saved_files[0]}")
            
            # Show next steps for website projects
            if is_website and len(saved_files) > 1:
                click.echo("\n🚀 Next steps:")
                click.echo(f"  $ cd {output_path.parent}")
                click.echo("  $ pip install -r requirements.txt")
                click.echo("  $ python app.py")
            
            # Show validation issues if any
            if result.validation_result.get('code_quality', {}).get('violations'):
                click.echo("\n🔍 Found the following issues:")
                for v in result.validation_result['code_quality']['violations']:
                    click.echo(f"  - {v['type']}: {v['message']}")
                    
            # Show adapter type information if using gRPC
            if use_grpc:
                click.echo("\n🚀 Used gRPC for faster communication with Ollama")
                
        except Exception as e:
            click.echo(f"\n❌ Error during generation: {str(e)}")
            logger.exception("Generation failed")
    
    asyncio.run(run_generation())
