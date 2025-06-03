import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from .session_models import GollmSession, CliContext, SessionState
from gollm import __version__ as gollm_current_version

class SessionManager:
    """Manages saving and loading of GoLLM sessions."""

    @staticmethod
    def save_session(session: GollmSession, filepath: Path) -> None:
        """Saves the current session to a JSON file."""
        try:
            session.update_timestamp()
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                # Pydantic's model_dump_json handles datetime serialization correctly
                f.write(session.model_dump_json(indent=2))
            print(f"Session saved to {filepath}")
        except IOError as e:
            print(f"Error saving session to {filepath}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while saving session: {e}")

    @staticmethod
    def load_session(filepath: Path) -> Optional[GollmSession]:
        """Loads a session from a JSON file."""
        if not filepath.exists():
            print(f"Error: Session file not found at {filepath}")
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct the session object using Pydantic model
            # This will also validate the data structure
            session = GollmSession(**data)
            
            # Optional: Check for version compatibility if needed
            if session.gollm_version != gollm_current_version:
                print(f"Warning: Session was saved with GoLLM version {session.gollm_version}, \
current version is {gollm_current_version}. Compatibility issues may arise.")
            
            print(f"Session loaded from {filepath}")
            return session
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from session file {filepath}: {e}")
            return None
        except IOError as e:
            print(f"Error reading session file {filepath}: {e}")
            return None
        except Exception as e: # Catches Pydantic validation errors too
            print(f"An unexpected error occurred while loading session: {e}")
            return None

    @staticmethod
    def create_new_session(request: str, cli_params: dict) -> GollmSession:
        """Creates a new session object from initial request and CLI parameters."""
        # Map cli_params to CliContext model fields
        # Ensure all required fields for CliContext are present or have defaults
        cli_context_data = {
            'request': request,
            'output_path': cli_params.get('output_path'),
            'iterations': cli_params.get('iterations', 6),
            'fast_mode': cli_params.get('fast', False),
            'auto_complete': cli_params.get('auto_complete', True),
            'execute_test': cli_params.get('execute_test', True),
            'auto_fix_execution': cli_params.get('auto_fix_execution', True),
            'max_fix_attempts': cli_params.get('max_fix_attempts', 5),
            'generate_tests': cli_params.get('tests', True),
            'adapter_type': cli_params.get('adapter_type'),
            'model_name': cli_params.get('model_name'),
            'temperature': cli_params.get('temperature'),
            'context_files': cli_params.get('context_files', []),
            'project_name': cli_params.get('project_name'), # This might be derived later
            'main_file_name': cli_params.get('main_file_name') # This might be derived later
        }
        cli_context = CliContext(**cli_context_data)
        
        session_state = SessionState() # Initialize with default empty state
        
        return GollmSession(
            gollm_version=gollm_current_version,
            original_request=request,
            cli_context=cli_context,
            current_state=session_state
        )

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    # Create a dummy session for testing
    example_cli_params = {
        'output_path': 'test_project',
        'iterations': 3,
        'fast_mode': True,
        'context_files': ['file1.py', 'file2.txt']
    }
    new_session = SessionManager.create_new_session(
        request="Create a simple calculator class",
        cli_params=example_cli_params
    )
    
    # Add a dummy generation step
    from .session_models import GenerationStep
    step1 = GenerationStep(
        step_type='initial_code',
        prompt_to_llm='Please generate a calculator class.',
        llm_response_raw='class Calculator:...',
        generated_code_snapshot={'calculator.py': 'class Calculator:\n    pass'}
    )
    new_session.generation_history.append(step1)
    new_session.current_state.current_code_files = {'calculator.py': 'class Calculator:\n    pass'}
    new_session.current_state.current_iteration = 1

    # Save the session
    session_file = Path('./test_gollm_session.json')
    SessionManager.save_session(new_session, session_file)
    
    # Load the session
    loaded_session = SessionManager.load_session(session_file)
    
    if loaded_session:
        print(f"Loaded session ID: {loaded_session.session_id}")
        print(f"Original request: {loaded_session.original_request}")
        print(f"CLI iterations: {loaded_session.cli_context.iterations}")
        print(f"Number of history steps: {len(loaded_session.generation_history)}")
        if loaded_session.generation_history:
            print(f"First step type: {loaded_session.generation_history[0].step_type}")
        print(f"Current iteration in state: {loaded_session.current_state.current_iteration}")

    # Clean up test file
    if session_file.exists():
        session_file.unlink()
        print(f"Cleaned up {session_file}")
