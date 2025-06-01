import pytest
import tempfile
import json
import os
from pathlib import Path

from gollm.config.aggregator import ProjectConfigAggregator

class TestProjectConfigAggregator:
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with config files"""
        temp_dir = tempfile.mkdtemp()
        
        # Create sample gollm.json
        gollm_config = {
            "validation_rules": {
                "max_function_lines": 50,
                "forbid_print_statements": True
            }
        }
        
        with open(Path(temp_dir) / "gollm.json", 'w') as f:
            json.dump(gollm_config, f)
        
        # Create sample .flake8
        flake8_config = """[flake8]
max-line-length = 88
ignore = E203,W503
max-complexity = 10
"""
        with open(Path(temp_dir) / ".flake8", 'w') as f:
            f.write(flake8_config)
        
        yield temp_dir
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
    
    def test_config_discovery(self, temp_project_dir):
        """Test configuration file discovery"""
        aggregator = ProjectConfigAggregator(temp_project_dir)
        
        assert "gollm.json" in aggregator.config_files
        assert ".flake8" in aggregator.config_files
    
    def test_config_aggregation(self, temp_project_dir):
        """Test configuration aggregation"""
        aggregator = ProjectConfigAggregator(temp_project_dir)
        config = aggregator.get_aggregated_config()
        
        assert "gollm_rules" in config
        assert "linting_rules" in config
        assert config["gollm_rules"]["validation_rules"]["max_function_lines"] == 50
    
    def test_llm_config_summary(self, temp_project_dir):
        """Test LLM configuration summary generation"""
        aggregator = ProjectConfigAggregator(temp_project_dir)
        summary = aggregator.get_llm_config_summary()
        
        assert isinstance(summary, str)
        assert "PROJECT CONFIGURATION SUMMARY" in summary
