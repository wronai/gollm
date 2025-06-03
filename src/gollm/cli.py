# src/gollm/cli.py
import click
import asyncio
import logging
import sys
from pathlib import Path
from .main import GollmCore
from .commands.direct import direct_group

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)


@click.group()
@click.option('--config', default='gollm.json', help='Path to config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """goLLM - Go Learn, Lead, Master!"""
    # Configure logging level
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Enable HTTP request logging if verbose
    if verbose:
        http_logger = logging.getLogger('aiohttp.client')
        http_logger.setLevel(logging.DEBUG)
        http_logger.propagate = True
    
    ctx.ensure_object(dict)
    ctx.obj['gollm'] = GollmCore(config)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('file_path')
@click.pass_context
def validate(ctx, file_path):
    """Validate a single file"""
    gollm = ctx.obj['gollm']
    result = gollm.validate_file(file_path)

    if result['violations']:
        click.echo(f"❌ Found {len(result['violations'])} violations in {file_path}")
        for violation in result['violations']:
            click.echo(f"  - {violation['type']}: {violation['message']}")
    else:
        click.echo(f"✅ No violations found in {file_path}")


@cli.command()
@click.pass_context
def validate_project(ctx):
    """Validate entire project"""
    gollm = ctx.obj['gollm']
    result = gollm.validate_project()

    total_violations = sum(len(file_result['violations'])
                           for file_result in result['files'].values())

    if total_violations > 0:
        click.echo(f"❌ Found {total_violations} violations across project")
    else:
        click.echo("✅ No violations found in project")


@cli.command()
@click.argument('request')
@click.option('--output', '-o', help='Output file or directory path')
@click.option('--critical', is_flag=True, help='Mark as high priority task')
@click.option('--no-todo', is_flag=True, help='Skip creating a TODO item')
@click.option('--fast', '-f', is_flag=True, help='Use fast mode with minimal validation')
@click.option('--iterations', '-i', default=3, type=int, help='Number of generation iterations')
@click.option('--strict-validation', is_flag=True, help='Use strict validation mode (no auto-fixing)')
@click.option('--allow-prompt-text', is_flag=True, help='Allow prompt-like text in generated code')
@click.option('--skip-validation', is_flag=True, help='Skip code validation entirely (not recommended)')
@click.option('--adapter-type', type=click.Choice(['http', 'grpc', 'modular']), help='Adapter type for Ollama communication')
@click.option('--use-streaming', is_flag=True, help='Use streaming API for faster response times')
@click.pass_context
def generate(ctx, request, output, critical, no_todo, fast, iterations, strict_validation, allow_prompt_text, skip_validation, adapter_type, use_streaming):
    """Generate code using LLM with quality validation
    
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
        'validation_options': {
            'strict_validation': strict_validation,
            'allow_prompt_text': allow_prompt_text,
            'skip_validation': skip_validation
        },
        # Use streaming if specified or default to True for better performance
        'use_streaming': use_streaming if use_streaming is not None else True,
        # Use specified adapter type or default to modular for better streaming support
        'adapter_type': adapter_type if adapter_type else 'modular'
    }
    
    # Set environment variables for adapter type and streaming
    if adapter_type:
        import os
        os.environ['OLLAMA_ADAPTER_TYPE'] = adapter_type
        logging.info(f"Using {adapter_type} adapter for Ollama communication")
    else:
        logging.info(f"Using modular adapter for Ollama communication")
    
    if no_todo:
        context['skip_todo'] = True
        
    # Log mode information
    if fast:
        logging.info("Using fast mode with minimal validation")
    else:
        logging.info(f"Using standard mode with up to {iterations} iterations")
        
    # Log validation options
    if skip_validation:
        logging.warning("Code validation is disabled - this may result in invalid code being saved")
    elif strict_validation:
        logging.info("Using strict validation mode - no automatic fixing of syntax errors")
    
    if allow_prompt_text:
        logging.info("Prompt-like text will be allowed in generated code")
    
    def suggest_filename(request_text: str, is_website: bool = False) -> str:
        """Generate a filename or directory name based on the request text"""
        clean_name = request_text.lower().replace(' ', '_')
        clean_name = ''.join(c if c.isalnum() or c == '_' else '' for c in clean_name)
        clean_name = '_'.join(filter(None, clean_name.split('_')))
        
        if is_website:
            return clean_name  # Directory for website projects
        return f"{clean_name}.py"
    
    async def save_generated_files(generated_code: str, base_path: Path) -> list:
        """Save generated code to appropriate files, handling multi-file output"""
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
                
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                saved_files.append(str(file_path))
        else:
            # Single file output
            base_path.parent.mkdir(parents=True, exist_ok=True)
            with open(base_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            saved_files.append(str(base_path))
            
        return saved_files
        
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
            
            # Extract parameters from context
            max_iterations = context.get('max_iterations', 3)
            validation_mode = 'strict' if context.get('validation_options', {}).get('strict_validation', False) else 'standard'
            skip_validation = context.get('validation_options', {}).get('skip_validation', False)
            use_streaming = context.get('use_streaming', True)
            
            # Call with explicit parameters for better control
            result = await gollm.handle_code_generation(
                request, 
                context=context,
                max_iterations=max_iterations,
                validation_mode=validation_mode,
                skip_validation=skip_validation,
                use_streaming=use_streaming
            )
            
            # Save all generated files
            saved_files = await save_generated_files(
                result.generated_code, 
                output_path
            )
            
            # Show results
            score_emoji = "🌟" if result.quality_score >= 90 else "👍"
            
            if len(saved_files) > 1:
                click.echo(f"\n✨ Generated {len(saved_files)} files! {score_emoji} Quality: {result.quality_score}/100")
                for i, file_path in enumerate(saved_files, 1):
                    file_icon = "📄" if file_path.endswith('.py') else "📝"
                    click.echo(f"  {i}. {file_icon} {file_path}")
            else:
                file_icon = "📄" if str(output_path).endswith('.py') else "📝"
                click.echo(f"\n✨ Generation complete! {score_emoji} Quality: {result.quality_score}/100 {file_icon} {saved_files[0]}")
            
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
                    severity = getattr(v, 'severity', 'info').upper()
                    message = getattr(v, 'message', 'Unknown issue')
                    click.echo(f"  - [{severity}] {message}")
            
            # Show next task if available
            if not no_todo:
                next_task = gollm.todo_manager.get_next_task()
                if next_task:
                    click.echo(f"\n📋 Next Task: {next_task['title']}")
                    click.echo(f"   Priority: {next_task['priority']}")
            
            return result
            
        except Exception as e:
            click.echo(f"❌ Error during code generation: {str(e)}", err=True)
            raise
    
    asyncio.run(run_generation())


@cli.command()
@click.pass_context
def next_task(ctx):
    """Get next task from TODO"""
    gollm = ctx.obj['gollm']
    task = gollm.get_next_task()

    if task:
        click.echo(f"🎯 Next Task: {task['title']}")
        click.echo(f"Priority: {task['priority']}")
        click.echo(f"Description: {task['description']}")
    else:
        click.echo("✅ No pending tasks found")


def _format_trend(trend_data, value_formatter=str):
    """Format trend data for display"""
    if not trend_data:
        return "No data available"
    
    # Group by date for better visualization
    date_groups = {}
    for ts, value in trend_data:
        date = ts.split('T')[0]  # Just get the date part
        date_groups[date] = value
    
    # Create a simple bar chart
    max_value = max(date_groups.values()) if date_groups else 0
    scale = 30.0 / max_value if max_value > 0 else 1
    
    lines = []
    for date, value in sorted(date_groups.items()):
        bar = '█' * int(value * scale)
        lines.append(f"{date}: {bar} {value_formatter(value)}")
    
    return '\n'.join(lines)

@cli.group()
@click.pass_context
def metrics(ctx):
    """Track and analyze code quality metrics"""
    pass

@metrics.command()
@click.option('--period', type=click.Choice(['day', 'week', 'month'], case_sensitive=False), 
              default='month', help='Time period to analyze')
@click.pass_context
def trend(ctx, period):
    """Show code quality trends over time"""
    gollm = ctx.obj['gollm']
    
    # Get quality trends
    quality_trend = gollm.metrics_tracker.get_quality_trend(period)
    violations_trend = gollm.metrics_tracker.get_violations_trend(period)
    
    click.echo("📈 CODE QUALITY TRENDS")
    click.echo("=" * 40)
    
    # Show quality score trend
    click.echo("\n🟢 CODE QUALITY SCORE")
    click.echo(_format_trend(quality_trend, lambda x: f"{x:.1f}"))
    
    # Show violations trend
    click.echo("\n🔴 CODE VIOLATIONS")
    click.echo(_format_trend(violations_trend, lambda x: f"{int(x)} issues"))
    
    # Show summary
    if quality_trend:
        first_score = quality_trend[0][1]
        last_score = quality_trend[-1][1]
        trend_emoji = "📈" if last_score > first_score else "📉" if last_score < first_score else "➡️"
        click.echo(f"\n{trend_emoji} Trend: {first_score:.1f} → {last_score:.1f}")

@cli.command()
@click.option('--interactive', '-i', is_flag=True, help='Enter interactive mode to modify configuration')
@click.pass_context
def config(ctx, interactive):
    """Show or modify configuration"""
    gollm = ctx.obj['gollm']
    config = gollm.config
    
    def display_config():
        click.clear()
        click.echo("🔧 goLLM CONFIGURATION")
        click.echo("=" * 40)
        
        # LLM Configuration
        llm_config = config.llm_integration
        click.echo("\n🤖 LLM SETTINGS")
        click.echo(f"  1. Provider:    {llm_config.api_provider or 'Not configured'}")
        click.echo(f"  2. Model:       {llm_config.model_name or 'Not specified'}")
        click.echo(f"  3. Max Tokens:  {llm_config.token_limit}")
        click.echo(f"  4. Max Iters:   {llm_config.max_iterations}")
        
        # Provider-specific settings
        if llm_config.providers:
            click.echo("\n🌐 PROVIDER CONFIGURATION")
            for i, (provider, settings) in enumerate(llm_config.providers.items(), 5):
                click.echo(f"  {i}. {provider.upper()}:")
                for key, value in settings.items():
                    if key.lower().endswith('key') or key.lower().endswith('token'):
                        value = "*" * 8 + (str(value)[-4:] if value else "")
                    click.echo(f"     {key}: {value}")
        
        # Validation Rules
        click.echo("\n✅ VALIDATION RULES")
        rules = config.validation_rules
        click.echo(f"  5. Max Line Length: {rules.max_line_length}")
        click.echo(f"  6. Allow Print:    {not rules.forbid_print_statements}")
        click.echo(f"  7. Require Docs:   {rules.require_docstrings}")
        
        # Project Settings
        click.echo("\n📁 PROJECT SETTINGS")
        click.echo(f"  8. Project Root:  {config.project_root}")
        click.echo(f"  9. TODO File:     {config.project_management.todo_file}")
        click.echo(f" 10. Changelog:     {config.project_management.changelog_file}")
        click.echo("\n 0. Save and Exit")
        click.echo(" q. Quit without saving")
    
    if not interactive:
        display_config()
        return
    
    # Interactive mode
    while True:
        display_config()
        
        choice = click.prompt("\nSelect an option to modify (or 0/q to exit)", default="0")
        
        if choice.lower() == 'q':
            if click.confirm("Discard all changes?", default=False):
                return
            continue
            
        if choice == '0':
            config.save()
            click.echo("\n✅ Configuration saved!")
            return
            
        try:
            option = int(choice)
            if 1 <= option <= 10:
                if option == 1:  # Provider
                    # List available providers
                    providers = [
                        {"name": "openai", "description": "OpenAI API"},
                        {"name": "ollama", "description": "Local Ollama"},
                        {"name": "anthropic", "description": "Anthropic Claude"},
                        {"name": "custom", "description": "Custom API endpoint"}
                    ]
                    
                    click.echo("\n🛠️  Available providers:")
                    for i, provider in enumerate(providers, 1):
                        click.echo(f"  {i}. {provider['name']} - {provider['description']}")
                    
                    while True:
                        choice = click.prompt("\nSelect provider (number) or enter custom name", default=config.llm_integration.api_provider)
                        
                        try:
                            # Try to convert to number
                            num_choice = int(choice)
                            if 1 <= num_choice <= len(providers):
                                new_provider = providers[num_choice-1]['name']
                                break
                            click.echo("❌ Invalid selection. Please try again.", err=True)
                        except ValueError:
                            # Not a number, use as custom provider
                            new_provider = choice.strip()
                            if new_provider:
                                break
                            click.echo("❌ Provider name cannot be empty.", err=True)
                    
                    config.llm_integration.api_provider = new_provider
                    
                    # Special handling for Ollama provider
                    if new_provider.lower() == 'ollama':
                        try:
                            import requests
                            click.echo("\n🔄 Fetching available Ollama models...")
                            response = requests.get("http://localhost:11434/api/tags")
                            if response.status_code == 200:
                                models = response.json().get('models', [])
                                if models:
                                    click.echo("\n📦 Available Ollama models:")
                                    for i, model in enumerate(models, 1):
                                        size_gb = model.get('size', 0) / 1024 / 1024 / 1024
                                        click.echo(f"  {i}. {model.get('name')} ({size_gb:.1f}GB)")
                                    
                                    while True:
                                        choice = click.prompt("\nSelect model (number) or enter custom model name", 
                                                           default=config.llm_integration.model_name)
                                        try:
                                            num_choice = int(choice)
                                            if 1 <= num_choice <= len(models):
                                                selected_model = models[num_choice-1]['name']
                                                click.echo(f"✅ Selected: {selected_model}")
                                                config.llm_integration.model_name = selected_model
                                                break
                                            click.echo("❌ Invalid selection. Please try again.", err=True)
                                        except ValueError:
                                            # Not a number, use as custom model name
                                            if choice.strip():
                                                config.llm_integration.model_name = choice.strip()
                                                break
                                            click.echo("❌ Model name cannot be empty.", err=True)
                                else:
                                    click.echo("ℹ️ No models found in Ollama.", err=True)
                            else:
                                click.echo("❌ Could not connect to Ollama. Is it running?", err=True)
                        except Exception as e:
                            click.echo(f"❌ Error: {str(e)}", err=True)
                        click.pause()
                    
                elif option == 2:  # Model
                    new_model = click.prompt("Enter model name", 
                                           default=config.llm_integration.model_name)
                    config.llm_integration.model_name = new_model
                    
                elif option == 3:  # Max Tokens
                    new_tokens = click.prompt("Enter max tokens", 
                                            default=config.llm_integration.token_limit,
                                            type=int)
                    config.llm_integration.token_limit = new_tokens
                    
                elif option == 4:  # Max Iterations
                    new_iters = click.prompt("Enter max iterations", 
                                           default=config.llm_integration.max_iterations,
                                           type=int)
                    config.llm_integration.max_iterations = new_iters
                    
                elif option == 5:  # Max Line Length
                    new_length = click.prompt("Enter max line length", 
                                            default=config.validation_rules.max_line_length,
                                            type=int)
                    config.validation_rules.max_line_length = new_length
                    
                elif option == 6:  # Allow Print
                    allow_print = click.confirm("Allow print statements?", 
                                              default=not config.validation_rules.forbid_print_statements)
                    config.validation_rules.forbid_print_statements = not allow_print
                    
                elif option == 7:  # Require Docstrings
                    require_docs = click.confirm("Require docstrings?", 
                                               default=config.validation_rules.require_docstrings)
                    config.validation_rules.require_docstrings = require_docs
                    
                elif option == 8:  # Project Root
                    new_root = click.prompt("Enter project root path", 
                                          default=config.project_root)
                    config.project_root = new_root
                    
                elif option == 9:  # TODO File
                    new_todo = click.prompt("Enter TODO file path", 
                                          default=config.project_management.todo_file)
                    config.project_management.todo_file = new_todo
                    
                elif option == 10:  # Changelog File
                    new_changelog = click.prompt("Enter changelog file path", 
                                               default=config.project_management.changelog_file)
                    config.project_management.changelog_file = new_changelog
                    
            else:
                click.echo("❌ Invalid option. Please try again.", err=True)
                
        except ValueError:
            click.echo("❌ Please enter a valid number.", err=True)
            
        click.pause()


@cli.command()
@click.pass_context
def status(ctx):
    """Show project status and configuration"""
    gollm = ctx.obj['gollm']

    # Get configurations
    config = gollm.config
    llm_config = config.llm_integration
    
    # Get LLM provider details
    provider_name = llm_config.api_provider or 'Not configured'
    model_name = llm_config.model_name or 'Not specified'
    
    # Get provider-specific details
    provider_details = ""
    if provider_name.lower() == 'ollama':
        provider_details = " (local)"
    elif provider_name.lower() == 'openai':
        provider_details = " (cloud)"
    
    # Validate project (skip if it takes too long)
    try:
        validation_result = gollm.validate_project()
        total_violations = sum(len(file_result['violations'])
                            for file_result in validation_result['files'].values())
        quality_score = 100 - min(total_violations, 20) * 5  # Cap at 20 violations for score
    except Exception as e:
        click.echo(f"⚠️  Could not validate project: {str(e)}", err=True)
        total_violations = "N/A"
        quality_score = "N/A"

    # Get TODO stats
    try:
        todo_stats = gollm.todo_manager.get_stats()
        todo_info = f"{todo_stats['pending']} pending ({todo_stats['high_priority']} 🔴, {todo_stats.get('code_generation_tasks', 0)} 🤖)"
    except Exception as e:
        click.echo(f"⚠️  Could not get TODO stats: {str(e)}", err=True)
        todo_info = "N/A"

    # Get recent changes
    try:
        recent_changes = gollm.changelog_manager.get_recent_changes_count()
    except Exception as e:
        click.echo(f"⚠️  Could not get changelog: {str(e)}", err=True)
        recent_changes = "N/A"

    # Display status
    click.echo("🚀 goLLM PROJECT STATUS")
    click.echo("=" * 50)
    
    # LLM Configuration
    click.echo("\n🤖 LLM CONFIGURATION")
    click.echo(f"  Provider:    {provider_name.upper()}{provider_details}")
    click.echo(f"  Model:       {model_name}")
    click.echo(f"  Max Tokens:  {llm_config.token_limit}")
    
    # Show provider-specific configuration if available
    if provider_name.lower() == 'ollama':
        base_url = llm_config.providers.get('ollama', {}).get('base_url', 'http://localhost:11434')
        click.echo(f"  Base URL:    {base_url}")
    elif provider_name.lower() == 'openai':
        model_version = llm_config.providers.get('openai', {}).get('model_version', 'Not specified')
        click.echo(f"  Model Ver:   {model_version}")
    
    # Project Status
    click.echo("\n📊 PROJECT STATUS")
    click.echo(f"  Quality:     {quality_score}/100")
    click.echo(f"  Violations:  {total_violations}")
    click.echo(f"  TODOs:       {todo_info}")
    click.echo(f"  Changes:     {recent_changes} recent")
    
    # Quick Actions
    click.echo("\n🔧 QUICK ACTIONS")
    click.echo("  gollm next-task    Show next task")
    click.echo("  gollm generate     Generate new code")
    click.echo("  gollm config       Show full configuration")


# Register the direct command group
cli.add_command(direct_group)

if __name__ == '__main__':
    cli()