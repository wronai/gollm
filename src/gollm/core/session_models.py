from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class CliContext(BaseModel):
    """Stores the CLI parameters used for the session."""
    request: str
    output_path: Optional[str] = None
    iterations: int = 6
    fast_mode: bool = False
    auto_complete: bool = True
    execute_test: bool = True
    auto_fix_execution: bool = True
    max_fix_attempts: int = 5
    generate_tests: bool = True
    adapter_type: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    context_files: List[str] = Field(default_factory=list)
    project_name: Optional[str] = None # Derived name for the project directory
    main_file_name: Optional[str] = None # Derived name for the main generated file

class GenerationStep(BaseModel):
    """Represents a single step in the generation or refinement process."""
    step_type: str # e.g., 'initial_code', 'test_generation', 'fix_attempt', 'refinement'
    prompt_to_llm: Optional[str] = None
    llm_response_raw: Optional[str] = None
    generated_code_snapshot: Optional[Dict[str, str]] = None # {filepath: code_content}
    validation_results: Optional[Dict] = None # e.g., syntax errors, linter issues
    execution_results: Optional[Dict] = None # e.g., success, stdout, stderr
    feedback_provided: Optional[str] = None # Feedback given to LLM for next step
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SessionState(BaseModel):
    """Represents the current snapshot of the generation process."""
    current_code_files: Dict[str, str] = Field(default_factory=dict) # {filepath: code_content}
    current_test_files: Dict[str, str] = Field(default_factory=dict) # {filepath: code_content}
    current_iteration: int = 0
    current_fix_attempt: int = 0
    last_error_context: Optional[str] = None
    is_complete: bool = False # True if generation met criteria or max iterations

class GollmSession(BaseModel):
    """Main model for storing the entire session context."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    gollm_version: str # To track compatibility
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    original_request: str
    cli_context: CliContext
    generation_history: List[GenerationStep] = Field(default_factory=list)
    current_state: SessionState

    def update_timestamp(self):
        self.updated_at = datetime.utcnow()
