import pytest
import tempfile
import os
from datetime import datetime

from gollm.project_management.changelog_manager import ChangelogManager
from gollm.config.config import GollmConfig

class TestChangelogManager:
    
    @pytest.fixture
    def config(self):
        """Test configuration with temporary CHANGELOG file"""
        config = GollmConfig.default()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            config.project_management.changelog_file = f.name
        return config
    
    @pytest.fixture
    def changelog_manager(self, config):
        """Test ChangelogManager instance"""
        return ChangelogManager(config)
    
    def test_record_change(self, changelog_manager):
        """Test recording a change entry"""
        change_entry = changelog_manager.record_change(
            "code_quality_fix",
            {
                "description": "Fixed function complexity",
                "files": ["test.py"],
                "violations_fixed": ["high_complexity"],
                "quality_delta": 5
            }
        )
        
        assert change_entry is not None
        assert change_entry["type"] == "code_quality_fix"
        assert change_entry["section"] == "Fixed"
        assert "Fixed function complexity" in change_entry["description"]
    
    def test_get_recent_changes_count(self, changelog_manager):
        """Test getting recent changes count"""
        # Record some changes
        changelog_manager.record_change(
            "feature_added",
            {"description": "Added new feature", "files": ["feature.py"]}
        )
        
        count = changelog_manager.get_recent_changes_count()
        assert isinstance(count, int)
        assert count >= 0
