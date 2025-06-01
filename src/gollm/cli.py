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
def status(ctx):
    """Show project status"""
    gollm = ctx.obj['gollm']

    # Validate project
    validation_result = gollm.validate_project()
    total_violations = sum(len(file_result['violations'])
                           for file_result in validation_result['files'].values())

    # Get TODO stats
    todo_stats = gollm.todo_manager.get_stats()

    click.echo("📊 goLLM PROJECT STATUS")
    click.echo("=" * 40)
    click.echo(f"Code Quality Score: {100 - min(total_violations * 5, 50)}/100")
    click.echo(f"Total Violations: {total_violations}")
    click.echo(f"TODO Tasks: {todo_stats['total']} ({todo_stats['high_priority']} high priority)")
    click.echo(f"Recent Changes: {gollm.changelog_manager.get_recent_changes_count()}")


if __name__ == '__main__':
    cli()