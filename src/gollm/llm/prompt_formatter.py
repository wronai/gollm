
# src/gollm/llm/prompt_formatter.py
from typing import Dict, Any, Optional

class PromptFormatter:
    """Formatuje prompty dla LLM z kontekstem projektu"""
    
    def __init__(self, config):
        self.config = config
    
    def create_prompt(self, user_request: str, context: Dict[str, Any], 
                     iteration: int = 0, previous_attempt: Optional[Dict] = None) -> str:
        """Tworzy sformatowany prompt dla LLM"""
        
        base_prompt = self._build_base_prompt(user_request, context)
        
        if iteration > 0 and previous_attempt:
            iteration_prompt = self._build_iteration_prompt(previous_attempt, iteration)
            return f"{base_prompt}\n\n{iteration_prompt}"
        
        return base_prompt
    
    def _build_base_prompt(self, user_request: str, context: Dict[str, Any]) -> str:
        """Buduje podstawowy prompt"""
        
        # Kontekst projektu
        project_context = self._format_project_context(context)
        
        # Kontekst wykonania
        execution_context = self._format_execution_context(context.get('execution_context', {}))
        
        # Zadania TODO
        todo_context = self._format_todo_context(context.get('todo_context', {}))
        
        # Reguły jakości
        quality_rules = self._format_quality_rules()
        
        prompt = f"""goLLM CODE GENERATION REQUEST

USER REQUEST:
{user_request}

{project_context}

{execution_context}

{todo_context}

{quality_rules}

REQUIREMENTS:
1. Generate code that follows all project quality standards
2. Include comprehensive docstrings for all functions
3. Use proper logging instead of print statements
4. Keep functions under {self.config.validation_rules.max_function_lines} lines
5. Limit function parameters to {self.config.validation_rules.max_function_params}
6. Maintain cyclomatic complexity under {self.config.validation_rules.max_cyclomatic_complexity}

Please provide:
1. Clean, well-documented code that passes all validation rules
2. Brief explanation of the approach taken
3. Any assumptions made during implementation
"""
        
        return prompt
    
    def _format_project_context(self, context: Dict[str, Any]) -> str:
        """Formatuje kontekst projektu"""
        config_ctx = context.get('project_config', {})
        
        return f"""PROJECT CONTEXT:
- Project Root: {context.get('project_root', '.')}
- Configuration Files: {len(config_ctx.get('config_files', []))} found
- Quality Score: {config_ctx.get('current_quality_score', 'Unknown')}
"""
    
    def _format_execution_context(self, exec_ctx: Dict[str, Any]) -> str:
        """Formatuje kontekst wykonania"""
        if not exec_ctx:
            return "EXECUTION CONTEXT: No recent execution data"
        
        last_error = exec_ctx.get('last_error')
        if last_error:
            return f"""EXECUTION CONTEXT:
🚨 RECENT ERROR DETECTED:
- Type: {last_error.get('type', 'Unknown')}
- Message: {last_error.get('message', 'No message')}
- File: {last_error.get('file_path', 'Unknown')}
- Line: {last_error.get('line_number', 'Unknown')}

Please ensure your solution addresses this error if relevant.
"""
        
        return "EXECUTION CONTEXT: No recent errors detected"
    
    def _format_todo_context(self, todo_ctx: Dict[str, Any]) -> str:
        """Formatuje kontekst TODO"""
        next_task = todo_ctx.get('next_task')
        stats = todo_ctx.get('stats', {})
        
        if next_task:
            return f"""TODO CONTEXT:
📋 NEXT PRIORITY TASK:
- Title: {next_task['title']}
- Priority: {next_task['priority']}
- Description: {next_task['description']}
- Estimated Effort: {next_task.get('estimated_effort', 'Unknown')}

📊 TODO STATS:
- Total Tasks: {stats.get('total', 0)}
- High Priority: {stats.get('high_priority', 0)}
- Pending: {stats.get('pending', 0)}

Consider addressing the priority task if your code generation can help resolve it.
"""
        
        return f"""TODO CONTEXT:
📊 TODO STATS:
- Total Tasks: {stats.get('total', 0)}
- High Priority: {stats.get('high_priority', 0)}
- Pending: {stats.get('pending', 0)}
"""
    
    def _format_quality_rules(self) -> str:
        """Formatuje reguły jakości"""
        rules = self.config.validation_rules
        
        return f"""QUALITY STANDARDS:
✅ Code Quality Rules:
- Max function lines: {rules.max_function_lines}
- Max file lines: {rules.max_file_lines}
- Max function parameters: {rules.max_function_params}
- Max cyclomatic complexity: {rules.max_cyclomatic_complexity}
- Print statements forbidden: {rules.forbid_print_statements}
- Global variables forbidden: {rules.forbid_global_variables}
- Docstrings required: {rules.require_docstrings}
- Naming convention: {rules.naming_convention}
"""
    
    def _build_iteration_prompt(self, previous_attempt: Dict[str, Any], iteration: int) -> str:
        """Buduje prompt dla iteracji"""
        
        validation_issues = previous_attempt.get('validation_result', {}).get('violations', [])
        
        if validation_issues:
            issues_text = "\n".join([f"- {issue.get('message', 'Unknown issue')}" 
                                   for issue in validation_issues[:5]])
            
            return f"""ITERATION {iteration} - IMPROVEMENT NEEDED:

The previous code had the following issues:
{issues_text}

Please provide an improved version that addresses these specific problems while maintaining functionality.
"""
        
        return f"""ITERATION {iteration}:
The previous attempt was acceptable but please try to improve code quality further if possible.
"""
