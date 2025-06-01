# src/spyq/cli.py
import click
import asyncio
from pathlib import Path

from .main import SpyqCore

@click.group()
@click.option('--config', default='spyq.json', help='Path to config file')
@click.pass_context
def cli(ctx, config):
    """SPYQ - Smart Python Quality Guardian"""
    ctx.ensure_object(dict)
    ctx.obj['spyq'] = SpyqCore(config)

@cli.command()
@click.argument('file_path')
@click.pass_context
def validate(ctx, file_path):
    """Validate a single file"""
    spyq = ctx.obj['spyq']
    result = spyq.validate_file(file_path)
    
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
    spyq = ctx.obj['spyq']
    result = spyq.validate_project()
    
    total_violations = sum(len(file_result['violations']) 
                          for file_result in result['files'].values())
    
    if total_violations > 0:
        click.echo(f"❌ Found {total_violations} violations across project")
    else:
        click.echo("✅ No violations found in project")

@cli.command()
@click.argument('request')
@click.pass_context
def generate(ctx, request):
    """Generate code using LLM"""
    spyq = ctx.obj['spyq']
    
    async def run_generation():
        result = await spyq.handle_code_generation(request)
        click.echo(result['generated_code'])
    
    asyncio.run(run_generation())

@cli.command()
@click.pass_context
def next_task(ctx):
    """Get next task from TODO"""
    spyq = ctx.obj['spyq']
    task = spyq.get_next_task()
    
    if task:
        click.echo(f"🎯 Next Task: {task['title']}")
        click.echo(f"Priority: {task['priority']}")
        click.echo(f"Description: {task['description']}")
    else:
        click.echo("✅ No pending tasks found")

@cli.command()
@click.pass_context
def status(ctx):
    """Show project status"""
    spyq = ctx.obj['spyq']
    
    # Validate project
    validation_result = spyq.validate_project()
    total_violations = sum(len(file_result['violations']) 
                          for file_result in validation_result['files'].values())
    
    # Get TODO stats
    todo_stats = spyq.todo_manager.get_stats()
    
    click.echo("📊 SPYQ PROJECT STATUS")
    click.echo("=" * 40)
    click.echo(f"Code Quality Score: {100 - min(total_violations * 5, 50)}/100")
    click.echo(f"Total Violations: {total_violations}")
    click.echo(f"TODO Tasks: {todo_stats['total']} ({todo_stats['high_priority']} high priority)")
    click.echo(f"Recent Changes: {spyq.changelog_manager.get_recent_changes_count()}")

if __name__ == '__main__':
    cli()