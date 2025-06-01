import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from gollm.llm.orchestrator import LLMOrchestrator, LLMRequest, LLMResponse
from gollm.config.config import GollmConfig

class TestLLMOrchestrator:
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return GollmConfig.default()
    
    @pytest.fixture
    def orchestrator(self, config):
        """Test LLMOrchestrator instance with mocked dependencies"""
        orchestrator = LLMOrchestrator(config)
        
        # Mock dependencies
        orchestrator.context_builder = Mock()
        orchestrator.context_builder.build_context = AsyncMock(return_value={
            "execution_context": {},
            "todo_context": {},
            "project_config": {}
        })
        
        orchestrator.prompt_formatter = Mock()
        orchestrator.prompt_formatter.create_prompt = Mock(return_value="Test prompt")
        
        orchestrator.response_validator = Mock()
        orchestrator.response_validator.validate_response = AsyncMock(return_value={
            "code_extracted": True,
            "extracted_code": "def test(): pass",
            "syntax_valid": True
        })
        
        orchestrator.code_validator = Mock()
        orchestrator.code_validator.validate_content = Mock(return_value={
            "violations": [],
            "quality_score": 95
        })
        
        return orchestrator
    
    def test_llm_request_creation(self):
        """Test LLMRequest dataclass"""
        request = LLMRequest(
            user_request="Create a function",
            context={"test": "context"},
            session_id="test-session",
            max_iterations=3
        )
        
        assert request.user_request == "Create a function"
        assert request.context == {"test": "context"}
        assert request.session_id == "test-session"
        assert request.max_iterations == 3
    
    def test_llm_response_creation(self):
        """Test LLMResponse dataclass"""
        response = LLMResponse(
            generated_code="def test(): pass",
            explanation="Test function",
            validation_result={"violations": []},
            iterations_used=1,
            quality_score=95
        )
        
        assert response.generated_code == "def test(): pass"
        assert response.explanation == "Test function"
        assert response.iterations_used == 1
        assert response.quality_score == 95
    
    @pytest.mark.asyncio
    async def test_handle_code_generation_request(self, orchestrator):
        """Test code generation request handling"""
        # Mock the LLM call
        orchestrator._simulate_llm_call = AsyncMock(return_value='''
Here's a test function:

```python
def test_function():
    """Test function"""
    return "test"
```
''')
        
        result = await orchestrator.handle_code_generation_request(
            "Create a test function",
            {"test": "context"}
        )
        
        assert isinstance(result, LLMResponse)
        assert result.generated_code
        assert result.quality_score > 0

