import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from gollm.llm.direct_api import DirectLLMClient


@pytest.mark.e2e
class TestDirectAPI:
    """End-to-end tests for the DirectLLMClient."""

    @pytest.fixture
    def mock_response(self):
        mock = MagicMock()
        mock.status = 200
        mock.json.return_value = {
            "model": "codellama:7b",
            "created_at": "2023-11-04T12:34:56Z",
            "response": "def hello_world():\n    print('Hello, World!')\n",
            "done": True
        }
        return mock

    @pytest.fixture
    def mock_session(self, mock_response):
        with patch('aiohttp.ClientSession') as mock_session:
            session_instance = mock_session.return_value
            session_instance.__aenter__.return_value = session_instance
            session_instance.__aexit__.return_value = None
            session_instance.post.return_value.__aenter__.return_value = mock_response
            yield session_instance

    @pytest.mark.asyncio
    async def test_generate(self, mock_session):
        """Test the generate method of DirectLLMClient."""
        client = DirectLLMClient(api_url="http://localhost:11434")
        response = await client.generate(
            prompt="Write a hello world function",
            model="codellama:7b",
            temperature=0.7,
            max_tokens=100
        )
        
        assert "hello_world" in response
        assert mock_session.post.called
        assert mock_session.post.call_args[0][0] == "http://localhost:11434/api/generate"

    @pytest.mark.asyncio
    async def test_chat_completion(self, mock_session):
        """Test the chat_completion method of DirectLLMClient."""
        client = DirectLLMClient(api_url="http://localhost:11434")
        response = await client.chat_completion(
            messages=[{"role": "user", "content": "Write a hello world function"}],
            model="codellama:7b",
            temperature=0.7,
            max_tokens=100
        )
        
        assert "hello_world" in response
        assert mock_session.post.called
        assert mock_session.post.call_args[0][0] == "http://localhost:11434/api/chat"

    @pytest.mark.asyncio
    async def test_save_to_file(self, mock_session):
        """Test saving the response to a file."""
        client = DirectLLMClient(api_url="http://localhost:11434")
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
            
        try:
            await client.generate(
                prompt="Write a hello world function",
                model="codellama:7b",
                output_file=temp_path
            )
            
            with open(temp_path, 'r') as f:
                content = f.read()
                
            assert "hello_world" in content
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


@pytest.mark.integration
class TestDirectAPIIntegration:
    """Integration tests that require a running Ollama service."""

    @pytest.mark.asyncio
    @pytest.mark.skipif("not os.environ.get('GOLLM_TEST_INTEGRATION')")
    async def test_real_generate(self):
        """Test with a real Ollama service."""
        client = DirectLLMClient(api_url="http://localhost:11434")
        response = await client.generate(
            prompt="Write a simple hello world function in Python",
            model="codellama:7b",
            temperature=0.7,
            max_tokens=100
        )
        
        assert response and len(response) > 0
        # Simple check that we got something that looks like Python code
        assert "def" in response.lower() or "print" in response.lower()
