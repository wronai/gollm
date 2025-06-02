"""Formatting utilities for CLI output."""

import click
from typing import Dict, Any, List, Callable, Optional, Union

def format_trend(trend_data: List[Dict[str, Any]], 
                value_formatter: Callable[[Any], str] = str) -> str:
    """Format trend data for display.
    
    Args:
        trend_data: List of trend data points
        value_formatter: Function to format values
        
    Returns:
        Formatted trend string
    """
    if not trend_data:
        return "No trend data available"
    
    # Find min and max values for scaling
    values = [item.get('value', 0) for item in trend_data]
    max_val = max(values) if values else 0
    min_val = min(values) if values else 0
    
    # Scale for visualization (10 steps)
    range_val = max_val - min_val
    scale = 10 / range_val if range_val > 0 else 1
    
    # Build the trend visualization
    result = []
    for item in trend_data:
        date = item.get('date', '')
        value = item.get('value', 0)
        
        # Calculate bar length
        bar_length = int((value - min_val) * scale) if range_val > 0 else 1
        bar = '█' * bar_length
        
        # Format the line
        result.append(f"{date}: {value_formatter(value)} {bar}")
    
    return '\n'.join(result)


def format_quality_score(score: float) -> str:
    """Format quality score with appropriate emoji.
    
    Args:
        score: Quality score (0-100)
        
    Returns:
        Formatted score string with emoji
    """
    if score >= 90:
        return f"🌟 {score:.1f}/100"
    elif score >= 75:
        return f"👍 {score:.1f}/100"
    elif score >= 50:
        return f"👌 {score:.1f}/100"
    else:
        return f"⚠️ {score:.1f}/100"


def format_file_icon(file_path: str) -> str:
    """Get appropriate icon for file type.
    
    Args:
        file_path: Path to file
        
    Returns:
        Icon string
    """
    if file_path.endswith('.py'):
        return "🐍"
    elif file_path.endswith('.md'):
        return "📝"
    elif file_path.endswith('.json'):
        return "📊"
    elif file_path.endswith('.html'):
        return "🌐"
    elif file_path.endswith('.css'):
        return "🎨"
    elif file_path.endswith('.js'):
        return "📜"
    else:
        return "📄"


def format_violations(violations: List[Dict[str, Any]]) -> str:
    """Format code violations for display.
    
    Args:
        violations: List of violation dictionaries
        
    Returns:
        Formatted violations string
    """
    if not violations:
        return "No violations found"
    
    result = []
    for v in violations:
        v_type = v.get('type', 'unknown')
        message = v.get('message', 'No description')
        line = v.get('line_number', 0)
        
        # Choose icon based on violation type
        icon = "⚠️"
        if v_type == "error":
            icon = "❌"
        elif v_type == "warning":
            icon = "⚠️"
        elif v_type == "info":
            icon = "ℹ️"
        
        result.append(f"{icon} Line {line}: {message}")
    
    return '\n'.join(result)


def format_task(task: Dict[str, Any]) -> str:
    """Format a task for display.
    
    Args:
        task: Task dictionary
        
    Returns:
        Formatted task string
    """
    if not task:
        return "No tasks available"
    
    # Priority emoji
    priority_emoji = "🔴" if task.get('priority') == "HIGH" else \
                    "🟡" if task.get('priority') == "MEDIUM" else "🟢"
    
    # Format related files
    related_files = '\n  '.join(
        [f"{format_file_icon(f)} {f}" for f in task.get('related_files', [])]
    )
    
    # Format suggestions
    suggestions = '\n  '.join(
        [f"- {s}" for s in task.get('approach_suggestions', [])]
    )
    
    return f"""Task: {task.get('title', 'Untitled')}
{priority_emoji} Priority: {task.get('priority', 'MEDIUM')}
⏱️ Estimated effort: {task.get('estimated_effort', 'Unknown')}

📋 Description:
{task.get('description', 'No description')}

📂 Related files:
  {related_files or 'None'}

💡 Suggested approach:
  {suggestions or 'No suggestions'}
"""
