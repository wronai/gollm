"""Project management commands for GoLLM CLI."""

import asyncio
import click
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..utils.formatting import format_trend, format_task

logger = logging.getLogger('gollm.commands.project')

@click.command('next-task')
@click.pass_context
def next_task_command(ctx):
    """Get the next task from the TODO list.
    
    Displays the highest priority pending task from the project's TODO list.
    
    Example: gollm next-task
    """
    gollm = ctx.obj['gollm']
    task = gollm.get_next_task()
    
    if not task:
        click.echo("\n✅ No pending tasks in the TODO list!")
        return
    
    click.echo("\n📋 Next task to work on:\n")
    click.echo(format_task(task))


@click.command('metrics')
@click.pass_context
def metrics_command(ctx):
    """Show code quality metrics for the project.
    
    Analyzes the project and displays various code quality metrics.
    
    Example: gollm metrics
    """
    gollm = ctx.obj['gollm']
    metrics = gollm.get_code_metrics()
    
    click.echo("\n📊 Code Quality Metrics:\n")
    
    # Overall score
    score = metrics.get('overall_score', 0)
    score_emoji = "🌟" if score >= 90 else "👍" if score >= 75 else "👌"
    click.echo(f"{score_emoji} Overall Quality Score: {score:.1f}/100\n")
    
    # File metrics
    click.echo("📁 File Metrics:")
    click.echo(f"  Total Files: {metrics.get('file_count', 0)}")
    click.echo(f"  Average File Length: {metrics.get('avg_file_length', 0):.1f} lines")
    click.echo(f"  Files Exceeding Length: {metrics.get('files_too_long', 0)}")
    
    # Function metrics
    click.echo("\n🔧 Function Metrics:")
    click.echo(f"  Total Functions: {metrics.get('function_count', 0)}")
    click.echo(f"  Average Function Length: {metrics.get('avg_function_length', 0):.1f} lines")
    click.echo(f"  Functions Exceeding Length: {metrics.get('functions_too_long', 0)}")
    click.echo(f"  Average Complexity: {metrics.get('avg_complexity', 0):.1f}")
    
    # Documentation metrics
    click.echo("\n📝 Documentation Metrics:")
    click.echo(f"  Documentation Coverage: {metrics.get('doc_coverage', 0):.1f}%")
    click.echo(f"  Missing Docstrings: {metrics.get('missing_docstrings', 0)}")
    
    # Validation metrics
    click.echo("\n🔍 Validation Metrics:")
    click.echo(f"  Total Violations: {metrics.get('total_violations', 0)}")
    click.echo(f"  Error-level Violations: {metrics.get('error_violations', 0)}")
    click.echo(f"  Warning-level Violations: {metrics.get('warning_violations', 0)}")


@click.command('trend')
@click.option('--period', '-p', default='week', type=click.Choice(['day', 'week', 'month', 'year']),
              help='Time period for trend analysis')
@click.pass_context
def trend_command(ctx, period):
    """Show code quality trends over time.
    
    Displays how code quality metrics have changed over the specified time period.
    
    Example: gollm trend --period month
    """
    gollm = ctx.obj['gollm']
    
    # Convert period to days for filtering
    days_map = {
        'day': 1,
        'week': 7,
        'month': 30,
        'year': 365
    }
    days = days_map.get(period, 7)
    
    # Get trend data
    trend_data = gollm.get_quality_trend(days)
    
    if not trend_data:
        click.echo(f"\n⚠️ No trend data available for the past {period}")
        return
    
    click.echo(f"\n📈 Code Quality Trend ({period}):\n")
    
    # Format overall score trend
    score_trend = [{
        'date': item.get('date', ''),
        'value': item.get('overall_score', 0)
    } for item in trend_data]
    
    click.echo("Overall Quality Score:")
    click.echo(format_trend(score_trend, lambda v: f"{v:.1f}/100"))
    
    # Format violation trend
    violation_trend = [{
        'date': item.get('date', ''),
        'value': item.get('total_violations', 0)
    } for item in trend_data]
    
    click.echo("\nTotal Violations:")
    click.echo(format_trend(violation_trend))
