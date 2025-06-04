import os
from unittest.mock import MagicMock, patch

import pytest
from tests.conftest import llm_test


from gollm.llm.orchestrator import LLMRequest
from gollm.main import GollmCore


@pytest.mark.e2e
class TestFastMode:
    """End-to-end tests for the fast mode feature."""

    @pytest.fixture
    def mock_llm_response(self):
        return "```python\ndef add(a, b):\n    return a + b\n```"

    @pytest.fixture
    def mock_orchestrator(self, mock_llm_response):
        with patch("gollm.llm.orchestrator.LLMOrchestrator") as mock_orch:
            orchestrator_instance = mock_orch.return_value
            orchestrator_instance.handle_code_generation_request.return_value = {
                "code": "def add(a, b):\n    return a + b\n",
                "quality_score": 85,
                "iterations": 1,
                "validation_results": {"valid": True, "messages": []},
            }
            yield orchestrator_instance

    @llm_test(timeout=30)
    def test_fast_mode_flag_propagation(self, mock_orchestrator):
        """Test that the fast mode flag is properly propagated to the orchestrator."""
        core = GollmCore(config_path=None)
        core._llm_orchestrator = mock_orchestrator

        # Call with fast mode enabled
        core.handle_code_generation(
            prompt="Create a simple addition function",
            output_path=None,
            critical=False,
            create_todo=True,
            fast_mode=True,
            iterations=1,
        )

        # Check that the orchestrator was called with fast_mode=True
        call_args = mock_orchestrator.handle_code_generation_request.call_args[0][0]
        assert isinstance(call_args, LLMRequest)
        assert call_args.fast_mode is True
        assert call_args.max_iterations == 1

    @llm_test(timeout=30)
    def test_fast_mode_uses_single_iteration(self, mock_orchestrator):
        """Test that fast mode uses only a single iteration."""
        core = GollmCore(config_path=None)
        core._llm_orchestrator = mock_orchestrator

        # Call with fast mode enabled but iterations > 1
        # The system should override and use only 1 iteration
        core.handle_code_generation(
            prompt="Create a simple addition function",
            output_path=None,
            critical=False,
            create_todo=True,
            fast_mode=True,
            iterations=3,  # This should be ignored in fast mode
        )

        # Check that max_iterations was forced to 1
        call_args = mock_orchestrator.handle_code_generation_request.call_args[0][0]
        assert call_args.max_iterations == 1


@pytest.mark.integration
class TestFastModeIntegration:
    """Integration tests for fast mode that require a running Ollama service."""

    @pytest.mark.skipif("not os.environ.get('GOLLM_TEST_INTEGRATION')")
    def test_fast_mode_performance(self):
        """Test that fast mode is faster than standard mode."""
        import time

        core = GollmCore(config_path=None)

        # Time the standard mode
        start_time = time.time()
        standard_result = core.handle_code_generation(
            prompt="Create a simple function to add two numbers",
            output_path=None,
            critical=False,
            create_todo=False,
            fast_mode=False,
            iterations=3,
        )
        standard_time = time.time() - start_time

        # Time the fast mode
        start_time = time.time()
        fast_result = core.handle_code_generation(
            prompt="Create a simple function to add two numbers",
            output_path=None,
            critical=False,
            create_todo=False,
            fast_mode=True,
            iterations=1,
        )
        fast_time = time.time() - start_time

        # Check that fast mode produced valid code
        assert fast_result and "code" in fast_result
        assert len(fast_result["code"]) > 0

        # Check that fast mode was actually faster
        # We expect at least a 30% speed improvement
        assert (
            fast_time < standard_time * 0.7
        ), f"Fast mode ({fast_time:.2f}s) should be at least 30% faster than standard mode ({standard_time:.2f}s)"
