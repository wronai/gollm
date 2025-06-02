"""Direct API access commands for fast LLM requests without extensive validation."""

import asyncio
import click
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ...llm.direct_api import DirectLLMClient

logger = logging.getLogger('gollm.commands.direct')

@click.group(name='direct')
def direct_group():
    """Direct API commands for fast LLM access with minimal processing."""
    pass

@direct_group.command()
@click.argument('prompt')
@click.option('--model', '-m', default='deepseek-coder:1.3b', help='Model to use')
@click.option('--temperature', '-t', default=0.1, type=float, help='Sampling temperature (0.0 to 1.0)')
@click.option('--max-tokens', default=1000, type=int, help='Maximum tokens to generate')
@click.option('--api-url', default='http://localhost:11434', help='API base URL')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--use-grpc', is_flag=True, help='Use gRPC for faster communication')
@click.pass_context
def generate(ctx, prompt, model, temperature, max_tokens, api_url, output, format, use_grpc):
    """Generate text using direct API access without validation pipeline.
    
    This command makes a direct API call similar to using curl, bypassing
    the extensive validation and processing pipeline for faster results.
    
    Example: gollm direct generate "Write Hello World in Python"
    """
    async def run_direct_generate():
        async with DirectLLMClient(base_url=api_url, use_grpc=use_grpc) as client:
            result = await client.generate(
                model=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if 'error' in result and result.get('success', True) is False:
                click.echo(f"❌ Error: {result['error']}")
                return
                
            # Extract the generated text
            generated_text = ''
            if 'response' in result:
                generated_text = result['response']
            elif 'message' in result and isinstance(result['message'], dict):
                generated_text = result['message'].get('content', '')
            
            # Format and display the result
            if format == 'json':
                formatted_result = json.dumps(result, indent=2)
                click.echo(formatted_result)
            else:
                click.echo(generated_text)
            
            # Save to file if requested
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    if format == 'json':
                        json.dump(result, f, indent=2)
                    else:
                        f.write(generated_text)
                        
                click.echo(f"✅ Output saved to {output_path}")
            
            # Show timing information
            if 'total_duration' in result:
                duration_ms = result['total_duration'] / 1_000_000  # Convert nanoseconds to milliseconds
                click.echo(f"⏱️ Generated in {duration_ms:.2f}ms")
                
            # Show adapter type information if using gRPC
            if use_grpc:
                click.echo("🚀 Used gRPC for faster communication")
    
    asyncio.run(run_direct_generate())

@direct_group.command()
@click.argument('prompt')
@click.option('--model', '-m', default='deepseek-coder:1.3b', help='Model to use')
@click.option('--temperature', '-t', default=0.1, type=float, help='Sampling temperature (0.0 to 1.0)')
@click.option('--max-tokens', default=1000, type=int, help='Maximum tokens to generate')
@click.option('--api-url', default='http://localhost:11434', help='API base URL')
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--format', '-f', type=click.Choice(['text', 'json']), default='text', help='Output format')
@click.option('--use-grpc', is_flag=True, help='Use gRPC for faster communication')
@click.pass_context
def chat(ctx, prompt, model, temperature, max_tokens, api_url, output, format, use_grpc):
    """Chat with LLM using direct API access without validation pipeline.
    
    This command makes a direct API call similar to using curl, bypassing
    the extensive validation and processing pipeline for faster results.
    
    Example: gollm direct chat "Write Hello World in Python"
    """
    async def run_direct_chat():
        async with DirectLLMClient(base_url=api_url, use_grpc=use_grpc) as client:
            result = await client.chat_completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if 'error' in result and result.get('success', True) is False:
                click.echo(f"❌ Error: {result['error']}")
                return
                
            # Extract the generated text
            generated_text = ''
            if 'message' in result and isinstance(result['message'], dict):
                generated_text = result['message'].get('content', '')
            
            # Format and display the result
            if format == 'json':
                formatted_result = json.dumps(result, indent=2)
                click.echo(formatted_result)
            else:
                click.echo(generated_text)
            
            # Save to file if requested
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    if format == 'json':
                        json.dump(result, f, indent=2)
                    else:
                        f.write(generated_text)
                        
                click.echo(f"✅ Output saved to {output_path}")
            
            # Show timing information
            if 'total_duration' in result:
                duration_ms = result['total_duration'] / 1_000_000  # Convert nanoseconds to milliseconds
                click.echo(f"⏱️ Generated in {duration_ms:.2f}ms")
                
            # Show adapter type information if using gRPC
            if use_grpc:
                click.echo("🚀 Used gRPC for faster communication")
    
    asyncio.run(run_direct_chat())
