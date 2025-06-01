# src/gollm/cli.py
import click
import asyncio
from pathlib import Path

from .main import GollmCore


@click.group()
@click.option('--config', default='gollm.json', help='Path to config file')
@click.pass_context
def cli(ctx, config):
    """goLLM - Go Learn, Lead, Master!"""
    ctx.ensure_object(dict)
    ctx.obj['gollm'] = GollmCore(config)


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
@click.option('--output', '-o', help='Output file path')
@click.option('--critical', is_flag=True, help='Mark as high priority task')
@click.option('--no-todo', is_flag=True, help='Skip creating a TODO item')
@click.pass_context
def generate(ctx, request, output, critical, no_todo):
    """Generate code using LLM with quality validation"""
    gollm = ctx.obj['gollm']
    
    context = {
        'is_critical': critical,
        'related_files': [output] if output else []
    }
    
    if no_todo:
        context['skip_todo'] = True
    
    async def run_generation():
        click.echo("🚀 Starting code generation...")
        click.echo(f"📝 Request: {request}")
        
        if output:
            click.echo(f"💾 Will save to: {output}")
        
        try:
            result = await gollm.handle_code_generation(request, context=context)
            
            # Save the generated code if output file is specified
            if output:
                output_path = Path(output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.generated_code)
                click.echo(f"✅ Code saved to: {output_path.absolute()}")
            
            # Show generation results
            click.echo("\n✨ Generation complete!")
            
            if result.quality_score > 0:
                score_emoji = "🌟" if result.quality_score >= 90 else "👍"
                click.echo(f"{score_emoji} Quality Score: {result.quality_score}/100")
            
            # Show validation results if available
            if result.validation_result.get('code_quality'):
                quality = result.validation_result['code_quality']
                violations = quality.get('violations', [])
                
                if violations:
                    click.echo("\n🔍 Found the following issues:")
                    for v in violations:
                        severity = v.get('severity', 'info').upper()
                        click.echo(f"  - [{severity}] {v.get('message', 'Unknown issue')}")
                        if 'suggested_fix' in v:
                            click.echo(f"    💡 Suggestion: {v['suggested_fix']}")
                else:
                    click.echo("✅ No code quality issues found!")
            
            # Show next steps
            if not no_todo:
                next_task = gollm.todo_manager.get_next_task()
                if next_task:
                    click.echo(f"\n📋 Next Task: {next_task['title']}")
                    click.echo(f"   Priority: {next_task['priority']}")
                    if next_task.get('estimated_effort'):
                        click.echo(f"   Estimated Effort: {next_task['estimated_effort']}")
            
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


@cli.command()
@click.pass_context
def config(ctx):
    """Show complete configuration"""
    gollm = ctx.obj['gollm']
    config = gollm.config
    
    click.echo("🔧 goLLM CONFIGURATION")
    click.echo("=" * 40)
    
    # LLM Configuration
    llm_config = config.llm_integration
    click.echo("\n🤖 LLM SETTINGS")
    click.echo(f"  Provider:    {llm_config.api_provider or 'Not configured'}")
    click.echo(f"  Model:       {llm_config.model_name or 'Not specified'}")
    click.echo(f"  Max Tokens:  {llm_config.token_limit}")
    click.echo(f"  Max Iters:   {llm_config.max_iterations}")
    
    # Provider-specific settings
    if llm_config.providers:
        click.echo("\n🌐 PROVIDER CONFIGURATION")
        for provider, settings in llm_config.providers.items():
            click.echo(f"  {provider.upper()}:")
            for key, value in settings.items():
                if key.lower().endswith('key') or key.lower().endswith('token'):
                    value = "*" * 8 + (str(value)[-4:] if value else "")
                click.echo(f"    {key}: {value}")
    
    # Validation Rules
    click.echo("\n✅ VALIDATION RULES")
    rules = config.validation_rules
    click.echo(f"  Max Line Length: {rules.max_line_length}")
    click.echo(f"  Allow Print:    {not rules.forbid_print_statements}")
    click.echo(f"  Require Docs:   {rules.require_docstrings}")
    
    # Project Settings
    click.echo("\n📁 PROJECT SETTINGS")
    click.echo(f"  Project Root:  {config.project_root}")
    click.echo(f"  TODO File:     {config.project_management.todo_file}")
    click.echo(f"  Changelog:     {config.project_management.changelog_file}")


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


if __name__ == '__main__':
    cli()