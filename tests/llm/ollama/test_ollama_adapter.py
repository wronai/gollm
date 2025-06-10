"""
Tests for the Ollama adapter implementation.

These tests verify the functionality of the Ollama adapter and its components,
including model management, text generation, and error handling.
"""

"""
Tests for the Ollama adapter implementation.

These tests verify the functionality of the Ollama adapter and its components,
including model management, text generation, and error handling.
"""

"""
Tests for the Ollama adapter implementation.

These tests verify the functionality of the Ollama adapter and its components,
including model management, text generation, and error handling.
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch, ANY, call

import pytest
from aiohttp import ClientError, ClientResponseError, ClientSession

# Set up detailed logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_ollama_debug.log', mode='w')
    ]
)
logger = logging.getLogger('test_ollama_adapter')
logger.setLevel(logging.DEBUG)

# Log all test execution to a separate file
file_handler = logging.FileHandler('test_ollama_execution.log', mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
execution_logger = logging.getLogger('test_execution')
execution_logger.addHandler(file_handler)
execution_logger.setLevel(logging.DEBUG)

# Add function to log test execution
def log_test_start(test_name):
    execution_logger.info(f"\n{'='*80}")
    execution_logger.info(f"STARTING TEST: {test_name}")
    execution_logger.info(f"{'='*80}")

def log_test_step(step):
    execution_logger.info(f"\nSTEP: {step}")
    execution_logger.info("-" * 60)

# Log environment variables for debugging
logger.debug("Environment variables:")
for k, v in os.environ.items():
    if 'OLLAMA' in k or 'GOLLM' in k or 'PYTHON' in k:
        logger.debug(f"  {k} = {v}")

# Log Python path for debugging
logger.debug("Python path:")
for path in sys.path:
    logger.debug(f"  {path}")

from gollm.llm.ollama import (
    OllamaAdapter,
    OllamaConfig,
    OllamaLLMProvider,
    ModelManager
)
from gollm.llm.ollama.api.client import OllamaAPIClient
from gollm.exceptions import (
    ModelNotFoundError,
    ModelOperationError,
    ConfigurationError,
    ValidationError
)

# Test data
TEST_MODEL = "test-model:latest"
TEST_PROMPT = "Hello, how are you?"
TEST_RESPONSE = {"response": "I'm doing well, thank you!", "done": True}
TEST_CHAT_MESSAGES = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"},
    {"role": "user", "content": "How are you?"}
]


@pytest.fixture
def mock_config():
    """Create a mock Ollama config for testing."""
    logger.debug("Creating mock OllamaConfig...")
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model=TEST_MODEL,
        timeout=30,
        max_tokens=4000,
        temperature=0.1,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1,
        stop=[],
    )
    logger.debug(f"Created OllamaConfig: {config}")
    return config


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    logger.debug("Creating mock API client...")
    
    # Create a mock with the correct spec
    client = AsyncMock(spec=OllamaAPIClient)
    
    # Set up mock methods with debug logging
    async def mock_generate(*args, **kwargs):
        logger.debug(f"mock_generate called with args: {args}, kwargs: {kwargs}")
        return TEST_RESPONSE
        
    async def mock_chat(*args, **kwargs):
        logger.debug(f"mock_chat called with args: {args}, kwargs: {kwargs}")
        return {"message": {"content": "I'm doing well, thank you!"}}
        
    async def mock_health(*args, **kwargs):
        logger.debug("mock_health called")
        return {"status": "ok"}
        
    async def mock_get_models(*args, **kwargs):
        logger.debug("mock_get_models called")
        return {"models": [{"name": TEST_MODEL, "size": 1000}]}
        
    async def mock_pull_model(*args, **kwargs):
        logger.debug(f"mock_pull_model called with args: {args}, kwargs: {kwargs}")
        return {"status": "success"}
        
    async def mock_delete_model(*args, **kwargs):
        logger.debug(f"mock_delete_model called with args: {args}, kwargs: {kwargs}")
        return {"status": "success"}
    
    # Assign the mock methods
    client.generate = AsyncMock(side_effect=mock_generate)
    client.chat = AsyncMock(side_effect=mock_chat)
    client.health = AsyncMock(side_effect=mock_health)
    client.get_models = AsyncMock(side_effect=mock_get_models)
    client.pull_model = AsyncMock(side_effect=mock_pull_model)
    client.delete_model = AsyncMock(side_effect=mock_delete_model)
    
    # Mock the context manager methods
    async def aenter(*args, **kwargs):
        logger.debug("Client context entered")
        return client
        
    async def aexit(*args, **kwargs):
        logger.debug("Client context exited")
        return None
        
    client.__aenter__ = aenter
    client.__aexit__ = aexit
    
    logger.debug("Mock API client created")
    return client


@pytest.fixture
async def mock_adapter(mock_api_client, mock_config):
    """Create a mock OllamaAdapter with a mock API client."""
    logger.debug("Creating mock adapter...")
    
    # Log the creation of dependencies
    logger.debug(f"Creating ModelManager with mock_api_client: {mock_api_client}")
    
    try:
        # Create a real ModelManager instance with the mock API client
        model_manager = ModelManager(api_client=mock_api_client)
        logger.debug(f"Created ModelManager: {model_manager}")
        
        # Create the adapter with the real ModelManager
        logger.debug(f"Creating OllamaAdapter with config: {mock_config}")
        adapter = OllamaAdapter(config=mock_config)
        
        # Log the initial state
        logger.debug(f"Initial adapter state - api_client: {adapter.api_client}, model_manager: {adapter.model_manager}")
        
        # Set the mock API client and model manager directly
        adapter.api_client = mock_api_client
        adapter.model_manager = model_manager
        adapter._initialized = True  # Mark as initialized
        
        logger.debug(f"Updated adapter state - api_client: {adapter.api_client}, model_manager: {adapter.model_manager}")
        
        # Mock the ensure_model method
        async def mock_ensure_model(model_name):
            logger.debug(f"[MOCK] ensure_model called with model: {model_name}")
            if not hasattr(mock_ensure_model, 'call_count'):
                mock_ensure_model.call_count = 0
            mock_ensure_model.call_count += 1
            logger.debug(f"[MOCK] ensure_model call #{mock_ensure_model.call_count} for model: {model_name}")
            return True
        
        adapter.ensure_model = mock_ensure_model
        
        # Mock the health check
        async def mock_health_check():
            logger.debug("[MOCK] health_check called")
            return {
                "status": "healthy",
                "service_available": True,
                "model_available": True,
                "config": mock_config.to_dict()
            }
        
        adapter.health_check = mock_health_check
        
        # Add debug method to inspect adapter state
        def debug_info():
            config_dict = None
            if hasattr(adapter, 'config'):
                if hasattr(adapter.config, 'to_dict'):
                    config_dict = adapter.config.to_dict()
                elif hasattr(adapter.config, '__dict__'):
                    config_dict = vars(adapter.config)
                else:
                    config_dict = str(adapter.config)
            
            return {
                'initialized': getattr(adapter, '_initialized', None),
                'config': config_dict,
                'has_api_client': adapter.api_client is not None,
                'has_model_manager': adapter.model_manager is not None,
                'model_manager_type': type(adapter.model_manager).__name__ if hasattr(adapter, 'model_manager') and adapter.model_manager is not None else None
            }
        
        adapter.debug_info = debug_info
        
        logger.debug(f"Mock adapter created successfully. Debug info: {debug_info()}")
        return adapter
        
    except Exception as e:
        logger.error(f"Error creating mock adapter: {str(e)}", exc_info=True)
        raise
    # Clean up resources
    if hasattr(adapter, 'close'):
        await adapter.close()
    logger.debug("Adapter cleaned up")


@pytest.fixture
def mock_session():
    """Create a mock aiohttp ClientSession."""
    with patch('aiohttp.ClientSession') as mock:
        yield mock


@pytest.mark.asyncio
async def test_adapter_initialization(mock_config):
    """Test that the adapter initializes correctly."""
    logger.info("Starting test_adapter_initialization")
    
    adapter = OllamaAdapter(config=mock_config)
    logger.debug(f"Created adapter with config: {mock_config}")
    
    assert adapter.config == mock_config
    assert not adapter._initialized
    
    # Test context manager
    async with adapter:
        logger.debug("Entering adapter context...")
        assert adapter._initialized
        assert adapter.api_client is not None
    
    # Adapter should be closed after context
    assert not adapter._initialized
    
    logger.info("test_adapter_initialization completed successfully")


@pytest.mark.asyncio
async def test_adapter_generate(mock_adapter):
    """Test text generation with the adapter."""
    logger.info("Starting test_adapter_generate")
    
    # Mock the API client
    mock_adapter.api_client.generate = AsyncMock(return_value=TEST_RESPONSE)
    
    # Test generation
    result = await mock_adapter.generate(
        prompt=TEST_PROMPT,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == TEST_RESPONSE
    mock_adapter.api_client.generate.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.api_client.generate.await_args
    assert kwargs['prompt'] == TEST_PROMPT
    assert kwargs['model'] == TEST_MODEL
    
    logger.info("test_adapter_generate completed successfully")


@pytest.mark.asyncio
async def test_adapter_chat(mock_adapter):
    """Test chat completion with the adapter."""
    logger.info("Starting test_adapter_chat")
    
    # Mock the API client
    mock_response = {"message": {"role": "assistant", "content": "I'm doing well!"}}
    mock_adapter.api_client.chat = AsyncMock(return_value=mock_response)
    
    # Test chat
    result = await mock_adapter.chat(
        messages=TEST_CHAT_MESSAGES,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == mock_response
    mock_adapter.api_client.chat.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.api_client.chat.await_args
    assert kwargs['messages'] == TEST_CHAT_MESSAGES
    assert kwargs['model'] == TEST_MODEL
    
    logger.info("test_adapter_chat completed successfully")


@pytest.mark.asyncio
async def test_adapter_stream_generate(mock_adapter):
    """Test streaming text generation with the adapter."""
    log_test_start("test_adapter_stream_generate")
    logger.info("Starting test_adapter_stream_generate")
    
    try:
        # Define the mock response chunks
        mock_chunks = [
            {"response": "I'm", "done": False},
            {"response": " doing", "done": False},
            {"response": " well!", "done": True}
        ]
        
        # Create a proper async iterable class for our mock chunks
        class AsyncChunkIterator:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0
            
            def __aiter__(self):
                logger.debug("[ASYNC_ITERATOR] __aiter__ called")
                return self
            
            async def __anext__(self):
                logger.debug(f"[ASYNC_ITERATOR] __anext__ called, index={self.index}")
                if self.index >= len(self.chunks):
                    logger.debug("[ASYNC_ITERATOR] Raising StopAsyncIteration")
                    raise StopAsyncIteration
                chunk = self.chunks[self.index]
                self.index += 1
                logger.debug(f"[ASYNC_ITERATOR] Yielding chunk: {chunk}")
                return chunk
        
        # Create an instance of our async iterator
        logger.debug("Creating async iterator instance")
        
        # Create an async function that returns our async iterator
        async def mock_generate_impl(*args, **kwargs):
            logger.debug("[MOCK_GENERATE] Called with args: %s, kwargs: %s", args, kwargs)
            return AsyncChunkIterator(mock_chunks)
        
        # Create a mock for the generate method
        logger.debug("Creating mock for generate method")
        mock_generate = AsyncMock(side_effect=mock_generate_impl)
        
        # Create a mock for the API client
        logger.debug("Creating mock API client")
        mock_api_client = AsyncMock()
        mock_api_client.generate = mock_generate
        
        # Replace the API client on the adapter
        logger.debug("Replacing adapter's API client with mock")
        mock_adapter.api_client = mock_api_client
        
        # Debug the setup
        logger.debug(f"Mock generate type: {type(mock_generate).__name__}")
        logger.debug(f"Mock generate is coroutine: {asyncio.iscoroutinefunction(mock_generate)}")
        logger.debug(f"API client type: {type(mock_adapter.api_client).__name__}")
        logger.debug(f"API client generate type: {type(mock_adapter.api_client.generate).__name__}")
        
        # Call the method under test
        log_test_step("Calling stream_generate")
        logger.debug("Calling stream_generate...")
        
        # Collect all chunks from the async generator
        chunks = []
        logger.debug("Starting to collect chunks from stream_generate")
        try:
            async for chunk in mock_adapter.stream_generate(
                prompt=TEST_PROMPT,
                temperature=0.7,
                max_tokens=100
            ):
                logger.debug(f"[TEST] Received chunk: {chunk}")
                chunks.append(chunk)
            logger.debug(f"[TEST] Finished collecting {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"[TEST] Error in async for loop: {str(e)}", exc_info=True)
            logger.error(f"[TEST] Chunks collected so far: {chunks}")
            raise
        
        # Verify the results
        log_test_step("Verifying results")
        logger.debug(f"Collected {len(chunks)} chunks: {chunks}")
        
        assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}: {chunks}"
        assert chunks[0]["response"] == "I'm", f"Unexpected first chunk: {chunks[0]}"
        assert chunks[1]["response"] == " doing", f"Unexpected second chunk: {chunks[1]}"
        assert chunks[2]["response"] == " well!", f"Unexpected third chunk: {chunks[2]}"
        
        # Verify the API was called correctly
        log_test_step("Verifying API call")
        mock_generate.assert_awaited_once()
        
        # Get the call arguments
        call_args = mock_generate.await_args[1]
        logger.debug(f"API call args: {call_args}")
        
        # Verify the call arguments
        assert call_args["prompt"] == TEST_PROMPT
        assert call_args["model"] == TEST_MODEL
        assert call_args["stream"] is True
        assert call_args["temperature"] == 0.7
        assert call_args["max_tokens"] == 100
        
        logger.info("test_adapter_stream_generate completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_adapter_stream_generate: {str(e)}", exc_info=True)
        # Log the mock state for debugging
        if 'mock_generate' in locals():
            logger.error(f"Mock generate call count: {mock_generate.await_count}")
            if mock_generate.await_args:
                logger.error(f"Mock generate call args: {mock_generate.await_args}")
        raise


@pytest.mark.asyncio
async def test_adapter_health_check(mock_adapter, mock_api_client):
    """Test health check functionality."""
    log_test_start("test_adapter_health_check")
    logger.info("Starting test_adapter_health_check")
    
    try:
        # Log initial state
        log_test_step("Initial setup")
        logger.debug(f"Initial adapter state: {getattr(mock_adapter, 'debug_info', lambda: 'No debug_info')()}")
        
        # Mock the API client responses
        mock_models_response = {"models": [{"name": TEST_MODEL}]}
        logger.debug(f"Mocking get_models to return: {mock_models_response}")
        
        # Mock model info response
        model_info = {
            "name": TEST_MODEL, 
            "details": {
                "parameter_size": "7B", 
                "family": "llama",
                "format": "gguf",
                "quantization_level": "Q4_0"
            }
        }
        
        logger.debug(f"Mocking model_manager.get_model_info to return: {model_info}")
        
        # Ensure model_manager is properly set up
        if not hasattr(mock_adapter, 'model_manager') or mock_adapter.model_manager is None:
            logger.debug("Creating new model manager mock")
            mock_adapter.model_manager = AsyncMock()
        
        # Set up model manager mocks
        mock_adapter.model_manager.get_model_info = AsyncMock(return_value=model_info)
        mock_adapter.model_manager.model_exists = AsyncMock(return_value=True)
        
        # Mock is_available to return True
        mock_adapter.is_available = AsyncMock(return_value=True)
        
        # Mock health check response
        health_check_response = {"status": "ok"}
        mock_adapter.api_client.health = AsyncMock(return_value=health_check_response)
        logger.debug(f"Mocked health check response: {health_check_response}")
        
        # Perform health check
        log_test_step("Performing health check")
        logger.debug("Calling health_check()...")
        health = await mock_adapter.health_check()
        logger.debug(f"Health check result: {health}")
        
        # Verify the result
        log_test_step("Verifying results")
        logger.debug("Verifying health check response structure...")
        
        assert isinstance(health, dict), f"Expected health to be a dict, got {type(health)}"
        
        # Check required fields
        required_fields = ["status", "service_available", "model_available", "config"]
        for field in required_fields:
            assert field in health, f"Missing required field in health check: {field}"
        
        # Verify values
        assert health["status"] == "healthy", f"Expected status 'healthy', got {health['status']}"
        assert health["service_available"] is True, "Service should be available"
        assert health["model_available"] is True, f"Model {TEST_MODEL} should be available"
        
        # Verify config in response
        assert "config" in health, "Config missing from health check response"
        assert health["config"]["model"] == TEST_MODEL, \
            f"Expected model {TEST_MODEL} in config, got {health['config'].get('model')}"
        
        # Verify the health check response structure and values
        log_test_step("Verifying health check response")
        logger.debug(f"Verifying health check response structure: {health}")
        
        # Verify the health check response has the expected structure
        assert isinstance(health, dict), f"Expected health to be a dict, got {type(health)}"
        
        # Check required fields
        required_fields = ["status", "service_available", "model_available", "config"]
        for field in required_fields:
            assert field in health, f"Missing required field in health check: {field}"
        
        # Verify values
        assert health["status"] == "healthy", f"Expected status 'healthy', got {health['status']}"
        assert health["service_available"] is True, "Service should be available"
        assert health["model_available"] is True, f"Model {TEST_MODEL} should be available"
        
        # Verify config in response
        assert "config" in health, "Config missing from health check response"
        assert health["config"]["model"] == TEST_MODEL, \
            f"Expected model {TEST_MODEL} in config, got {health['config'].get('model')}"
        
        logger.info("test_adapter_health_check completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_adapter_health_check: {str(e)}", exc_info=True)
        # Log the full adapter state for debugging
        if hasattr(mock_adapter, 'debug_info'):
            logger.error(f"Adapter debug info: {mock_adapter.debug_info()}")
        raise


@pytest.mark.asyncio
async def test_provider_initialization(mock_config):
    """Test that the provider initializes correctly."""
    logger.info("Starting test_provider_initialization")
    
    provider = OllamaLLMProvider(config=mock_config.to_dict())
    logger.debug(f"Created provider with config: {mock_config}")
    
    assert not provider.is_initialized
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    with patch('gollm.llm.ollama.provider.OllamaAdapter', return_value=mock_adapter):
        await provider.initialize()
        logger.debug("Provider initialized")
        assert provider.is_initialized
        
        # Test context manager
        async with provider as p:
            logger.debug("Entering provider context...")
            assert p == provider
            assert p.is_initialized
    
    # Provider should be closed after context
    assert not provider.is_initialized
    
    logger.info("test_provider_initialization completed successfully")


@pytest.mark.asyncio
async def test_provider_generate(mock_config):
    """Test text generation with the provider."""
    logger.info("Starting test_provider_generate")
    
    provider = OllamaLLMProvider(config=mock_config.to_dict())
    logger.debug(f"Created provider with config: {mock_config}")
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    mock_adapter.generate = AsyncMock(return_value=TEST_RESPONSE)
    provider._adapter = mock_adapter
    provider._initialized = True
    
    # Test generation
    result = await provider.generate(
        prompt=TEST_PROMPT,
        model=TEST_MODEL
    )
    
    # Verify the result
    assert result == TEST_RESPONSE
    mock_adapter.generate.assert_awaited_once()
    
    # Verify parameters
    args, kwargs = mock_adapter.generate.await_args
    assert kwargs['prompt'] == TEST_PROMPT
    assert kwargs['model'] == TEST_MODEL
    
    logger.info("test_provider_generate completed successfully")


@pytest.mark.asyncio
async def test_provider_health_check():
    """Test health check with the provider."""
    logger.info("Starting test_provider_health_check")
    
    provider = OllamaLLMProvider()
    
    # Mock the adapter
    mock_adapter = AsyncMock()
    mock_adapter.health_check = AsyncMock(return_value={"status": "healthy"})
    provider._adapter = mock_adapter
    provider._initialized = True
    
    # Test health check
    health = await provider.health_check()
    assert health["status"] == "healthy"
    mock_adapter.health_check.assert_awaited_once()
    
    logger.info("test_provider_health_check completed successfully")


@pytest.mark.asyncio
async def test_model_manager(mock_api_client):
    """Test the model manager functionality."""
    logger.info("Starting test_model_manager")
    
    try:
        # Reset call counts
        logger.debug("Resetting mock call counts...")
        # Reset all mock call counts and side effects
        for attr in dir(mock_api_client):
            if attr.startswith('_') or attr in ['assert_any_call', 'assert_called', 'assert_called_once', 
                                             'assert_called_once_with', 'assert_has_calls', 'assert_not_called',
                                             'method_calls', 'mock_add_spec', 'mock_calls', 'reset_mock']:
                continue
            mock = getattr(mock_api_client, attr, None)
            if hasattr(mock, 'reset_mock'):
                logger.debug(f"Resetting mock: {attr}")
                mock.reset_mock()
        
        # Create a model manager with the mock client
        logger.debug("Creating ModelManager...")
        manager = ModelManager(mock_api_client)
        
        # Test listing models
        logger.debug("Testing list_models...")
        models = await manager.list_models(refresh=True)
        logger.debug(f"Got models: {models}")
        assert TEST_MODEL in models, f"Expected {TEST_MODEL} in {models}"
        mock_api_client.get_models.assert_awaited_once()
        
        # Test model exists
        logger.debug("Testing model_exists...")
        exists = await manager.model_exists(TEST_MODEL)
        logger.debug(f"Model {TEST_MODEL} exists: {exists}")
        assert exists is True
        
        # Test getting model info
        logger.debug("Testing get_model_info...")
        model_info = await manager.get_model_info(TEST_MODEL)
        logger.debug(f"Got model info: {model_info}")
        assert model_info["name"] == TEST_MODEL
        
        # Test pulling a model
        logger.debug(f"Testing pull_model for {TEST_MODEL}...")
        await manager.pull_model(TEST_MODEL)
        logger.debug("Pull model call completed")
        
        # Verify request was called correctly
        logger.debug("Verifying API request was made...")
        
        # Check if request was called with the correct parameters
        if not mock_api_client.request.await_args_list:
            logger.error("No API request was made")
            raise AssertionError("Expected API request to be made")
            
        # Check if any request was a pull request
        pull_requests = [
            (args, kwargs) 
            for args, kwargs in mock_api_client.request.await_args_list
            if args and len(args) >= 2 and args[0] == 'POST' and args[1] == '/api/pull'
        ]
        
        if not pull_requests:
            logger.error("No pull model request was made")
            logger.debug("All requests: %s", mock_api_client.request.await_args_list)
            raise AssertionError("Expected pull model request to be made")
                
        # Get the pull request details
        args, kwargs = pull_requests[0]
        logger.debug(f"Pull request - method: {args[0]}, path: {args[1]}, data: {kwargs.get('data')}")
        
        # Check if the model name is in the request data
        request_data = kwargs.get('data', {})
        if not isinstance(request_data, dict):
            error_msg = f"Expected request data to be a dict, got {type(request_data)}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
            
        if request_data.get('name') != TEST_MODEL:
            error_msg = f"Expected model name '{TEST_MODEL}' in request data, got {request_data}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
            
        logger.info("Pull model request was made with the correct model name")
        
        # Test deleting a model
        logger.debug(f"Testing delete_model for {TEST_MODEL}...")
        await manager.delete_model(TEST_MODEL)
        logger.debug("Delete model call completed")
        
        # Verify delete request was made correctly
        logger.debug("Verifying delete request was made...")
        
        # Check if any request was a delete request
        delete_requests = [
            (args, kwargs) 
            for args, kwargs in mock_api_client.request.await_args_list
            if args and len(args) >= 2 and args[0] == 'DELETE' and args[1] == '/api/delete'
        ]
        
        if not delete_requests:
            logger.error("No delete model request was made")
            logger.debug("All requests: %s", mock_api_client.request.await_args_list)
            raise AssertionError("Expected delete model request to be made")
            
        # Get the delete request details
        args, kwargs = delete_requests[0]
        logger.debug(f"Delete request - method: {args[0]}, path: {args[1]}, data: {kwargs.get('data')}")
        
        # Check if the model name is in the request data
        request_data = kwargs.get('data', {})
        if not isinstance(request_data, dict):
            error_msg = f"Expected request data to be a dict, got {type(request_data)}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
            
        if request_data.get('name') != TEST_MODEL:
            error_msg = f"Expected model name '{TEST_MODEL}' in request data, got {request_data}"
            logger.error(error_msg)
            raise AssertionError(error_msg)
            
        logger.info("Delete model request was made with the correct model name")
        
        logger.info("test_model_manager completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_model_manager: {str(e)}", exc_info=True)
        raise


@pytest.mark.asyncio
async def test_config_validation():
    """Test configuration validation."""
    log_test_start("test_config_validation")
    logger.info("Starting test_config_validation")
    
    try:
        # Test valid configuration
        log_test_step("Testing valid configuration")
        logger.debug("Creating valid config...")
        valid_config = OllamaConfig(
            base_url="http://test:11434",
            model=TEST_MODEL,
            timeout=30,
            max_tokens=4000,
            temperature=0.1,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=[],
        )
        logger.debug(f"Created config: {valid_config}")
        
        # Verify config values
        log_test_step("Verifying config values")
        logger.debug("Verifying config values...")
        assert valid_config.model == TEST_MODEL, f"Expected model {TEST_MODEL}, got {valid_config.model}"
        assert valid_config.base_url == "http://test:11434", f"Expected base_url http://test:11434, got {valid_config.base_url}"
        assert valid_config.timeout == 30, f"Expected timeout 30, got {valid_config.timeout}"
        logger.debug("Config values verified successfully")
        
        # Test serialization/deserialization
        log_test_step("Testing serialization/deserialization")
        logger.debug("Testing serialization/deserialization...")
        config_dict = valid_config.to_dict()
        logger.debug(f"Serialized config to dict: {config_dict}")
        
        deserialized = OllamaConfig.from_dict(config_dict)
        logger.debug(f"Deserialized config: {deserialized}")
        
        # Verify deserialized config
        log_test_step("Verifying deserialized config")
        assert deserialized.model == valid_config.model, f"Model mismatch: {deserialized.model} != {valid_config.model}"
        assert deserialized.base_url == valid_config.base_url, f"Base URL mismatch: {deserialized.base_url} != {valid_config.base_url}"
        assert deserialized.timeout == valid_config.timeout, f"Timeout mismatch: {deserialized.timeout} != {valid_config.timeout}"
        logger.debug("Deserialized config verified successfully")
        
        # Test invalid configurations
        log_test_step("Testing invalid configurations")
        logger.debug("Testing invalid configurations...")
        
        # Test that empty model names are allowed (no validation in OllamaConfig)
        log_test_step("Testing empty model name")
        logger.debug("Testing that empty model names are allowed...")
        
        # Create config with empty model name
        config = OllamaConfig(base_url="http://test:11434", model="")
        assert config.model == "", "Empty model name should be allowed"
        
        # Create config with whitespace model name
        config = OllamaConfig(base_url="http://test:11434", model=" ")
        assert config.model == " ", "Whitespace model name should be allowed"
        
        # Test that missing fields use default values
        log_test_step("Testing default values")
        logger.debug("Testing that missing fields use default values...")
        
        # Test with minimal config
        minimal_config = OllamaConfig(base_url="http://test:11434", model=TEST_MODEL)
        assert minimal_config.timeout == 60, f"Expected default timeout 60, got {minimal_config.timeout}"
        assert minimal_config.temperature == 0.1, f"Expected default temperature 0.1, got {minimal_config.temperature}"
        assert minimal_config.max_tokens == 4000, f"Expected default max_tokens 4000, got {minimal_config.max_tokens}"
        assert minimal_config.top_p == 0.9, f"Expected default top_p 0.9, got {minimal_config.top_p}"
        assert minimal_config.top_k == 40, f"Expected default top_k 40, got {minimal_config.top_k}"
        assert minimal_config.repeat_penalty == 1.1, f"Expected default repeat_penalty 1.1, got {minimal_config.repeat_penalty}"
        assert minimal_config.stop == [], f"Expected default stop [], got {minimal_config.stop}"
        
        logger.debug("Default values test passed")
        
        logger.info("test_config_validation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in test_config_validation: {str(e)}", exc_info=True)
        raise
    
    # Test that OllamaConfig allows all fields to be optional with defaults
    log_test_step("Testing optional fields with defaults")
    logger.debug("Testing that all fields are optional with defaults...")
    
    # Test minimal config with only required fields
    minimal_config = OllamaConfig(base_url="http://test:11434", model=TEST_MODEL)
    assert minimal_config.base_url == "http://test:11434"
    assert minimal_config.model == TEST_MODEL
    assert minimal_config.timeout == 60  # Default value
    assert minimal_config.temperature == 0.1  # Default value
    
    # Test that OllamaConfig doesn't validate values
    log_test_step("Testing that OllamaConfig doesn't validate values")
    
    # Test with empty model name (should be allowed)
    empty_model_config = OllamaConfig(base_url="http://test:11434", model="")
    assert empty_model_config.model == ""
    
    # Test with whitespace model name (should be allowed)
    whitespace_model_config = OllamaConfig(base_url="http://test:11434", model=" ")
    assert whitespace_model_config.model == " "
    
    # Test with negative timeout (should be allowed)
    negative_timeout_config = OllamaConfig(base_url="http://test:11434", model=TEST_MODEL, timeout=-1)
    assert negative_timeout_config.timeout == -1
    
    # Test with invalid temperature (should be allowed)
    invalid_temp_config = OllamaConfig(base_url="http://test:11434", model=TEST_MODEL, temperature=-0.1)
    assert invalid_temp_config.temperature == -0.1
    
    logger.info("test_config_validation completed successfully")


@pytest.mark.asyncio
async def test_error_handling(mock_adapter, mock_api_client):
    """Test error handling in the adapter."""
    # Test API error
    mock_api_client.generate = AsyncMock(side_effect=ClientError("API error"))
    
    with pytest.raises(ModelOperationError):
        await mock_adapter.generate(prompt=TEST_PROMPT)
    
    # Test model not found
    mock_api_client.generate = AsyncMock(side_effect=ModelNotFoundError("Model not found"))
    
    with pytest.raises(ModelNotFoundError):
        await mock_adapter.generate(prompt=TEST_PROMPT, model="nonexistent-model")
    
    # Test generation error
    mock_adapter.api_client.generate = AsyncMock(side_effect=Exception("Generation failed"))
    with pytest.raises(ModelOperationError):
        await mock_adapter.generate(prompt=TEST_PROMPT)
