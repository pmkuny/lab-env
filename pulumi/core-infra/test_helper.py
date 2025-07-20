import unittest
from unittest.mock import patch, MagicMock
import pulumi
from helper import get_global_tags, merge_tags


class TestHelperFunctions(unittest.TestCase):
    """Test suite for helper module functions."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_global_tags = {
            "Environment": "test",
            "Project": "homelab",
            "Owner": "infrastructure-team"
        }
    
    @patch('pulumi.Config')
    def test_get_global_tags_with_config(self, mock_config):
        """Test get_global_tags returns configured tags."""
        # Mock config to return sample tags
        mock_config_instance = MagicMock()
        mock_config_instance.get_object.return_value = self.sample_global_tags
        mock_config.return_value = mock_config_instance
        
        result = get_global_tags()
        
        self.assertEqual(result, self.sample_global_tags)
        mock_config_instance.get_object.assert_called_once_with("globalTags")
    
    @patch('pulumi.Config')
    def test_get_global_tags_no_config(self, mock_config):
        """Test get_global_tags returns empty dict when no config."""
        # Mock config to return None
        mock_config_instance = MagicMock()
        mock_config_instance.get_object.return_value = None
        mock_config.return_value = mock_config_instance
        
        result = get_global_tags()
        
        self.assertEqual(result, {})
        mock_config_instance.get_object.assert_called_once_with("globalTags")
    
    @patch('helper.get_global_tags')
    def test_merge_tags_basic_functionality(self, mock_get_global_tags):
        """Test merge_tags combines global tags with resource name."""
        mock_get_global_tags.return_value = self.sample_global_tags
        
        result = merge_tags("test-resource")
        
        expected = {
            **self.sample_global_tags,
            "Name": "test-resource"
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_with_additional_tags(self, mock_get_global_tags):
        """Test merge_tags includes additional tags."""
        mock_get_global_tags.return_value = self.sample_global_tags
        
        additional_tags = {
            "Type": "networking",
            "Backup": "daily"
        }
        
        result = merge_tags("vpc-resource", additional_tags)
        
        expected = {
            **self.sample_global_tags,
            "Name": "vpc-resource",
            "Type": "networking",
            "Backup": "daily"
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_additional_overrides_global(self, mock_get_global_tags):
        """Test that additional tags override global tags with same key."""
        mock_get_global_tags.return_value = {
            "Environment": "production",
            "Project": "homelab"
        }
        
        additional_tags = {
            "Environment": "staging",  # This should override global
            "Type": "compute"
        }
        
        result = merge_tags("override-test", additional_tags)
        
        expected = {
            "Environment": "staging",  # Overridden value
            "Project": "homelab",      # Global value preserved
            "Name": "override-test",   # Resource name
            "Type": "compute"          # Additional tag
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_name_override(self, mock_get_global_tags):
        """Test that additional tags can override the Name tag."""
        mock_get_global_tags.return_value = {"Project": "homelab"}
        
        additional_tags = {
            "Name": "custom-name"  # Override default name
        }
        
        result = merge_tags("default-name", additional_tags)
        
        expected = {
            "Project": "homelab",
            "Name": "custom-name"  # Should be overridden
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_empty_additional(self, mock_get_global_tags):
        """Test merge_tags with empty additional tags."""
        mock_get_global_tags.return_value = self.sample_global_tags
        
        result = merge_tags("simple-resource", {})
        
        expected = {
            **self.sample_global_tags,
            "Name": "simple-resource"
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_none_additional(self, mock_get_global_tags):
        """Test merge_tags with None additional tags."""
        mock_get_global_tags.return_value = self.sample_global_tags
        
        result = merge_tags("none-additional", None)
        
        expected = {
            **self.sample_global_tags,
            "Name": "none-additional"
        }
        
        self.assertEqual(result, expected)
    
    @patch('helper.get_global_tags')
    def test_merge_tags_no_global_tags(self, mock_get_global_tags):
        """Test merge_tags when no global tags are configured."""
        mock_get_global_tags.return_value = {}
        
        additional_tags = {"Type": "storage"}
        
        result = merge_tags("storage-resource", additional_tags)
        
        expected = {
            "Name": "storage-resource",
            "Type": "storage"
        }
        
        self.assertEqual(result, expected)
    
    def test_merge_tags_special_characters_in_name(self):
        """Test merge_tags handles special characters in resource names."""
        with patch('helper.get_global_tags', return_value={}):
            result = merge_tags("test-resource_with.special-chars")
            
            expected = {
                "Name": "test-resource_with.special-chars"
            }
            
            self.assertEqual(result, expected)
    
    def test_merge_tags_unicode_characters(self):
        """Test merge_tags handles unicode characters properly."""
        with patch('helper.get_global_tags', return_value={}):
            additional_tags = {"Description": "测试资源"}
            
            result = merge_tags("unicode-test", additional_tags)
            
            expected = {
                "Name": "unicode-test",
                "Description": "测试资源"
            }
            
            self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
