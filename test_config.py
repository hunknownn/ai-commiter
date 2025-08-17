#!/usr/bin/env python3
"""Test script for multi-section configuration system."""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import set_config_value, get_config_value, list_config, unset_config_value
    print("✅ Successfully imported config functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_multi_section_config():
    """Test the multi-section configuration system."""
    print("🧪 Testing Multi-Section Configuration System\n")
    
    # Test 1: Set core section values
    print("1. Testing core section configuration:")
    set_config_value('core.lang', 'ko')
    set_config_value('core.model', 'gpt-4')
    set_config_value('core.commit', 'true')
    
    # Test 2: Set additional core section values
    print("\n2. Testing additional core section configuration:")
    set_config_value('core.split', 'false')
    set_config_value('core.prompt', '/path/to/custom.txt')
    
    # Test 3: Test backward compatibility
    print("\n3. Testing backward compatibility:")
    set_config_value('split', 'true')  # Should go to core section
    
    # Test 4: List all configurations
    print("\n4. Current configuration:")
    list_config()
    
    # Test 5: Get specific values
    print("\n5. Testing get operations:")
    print(f"core.lang = {get_config_value('core.lang')}")
    print(f"core.model = {get_config_value('core.model')}")
    print(f"split (backward compat) = {get_config_value('split')}")
    
    # Test 6: Test invalid section/key
    print("\n6. Testing validation:")
    set_config_value('invalid.key', 'value')
    set_config_value('core.invalid', 'value')
    set_config_value('core.lang', 'invalid-lang')
    
    # Test 7: Unset values
    print("\n7. Testing unset operations:")
    unset_config_value('core.prompt')
    unset_config_value('split')
    
    print("\n8. Final configuration:")
    list_config()
    
    print("\n✅ Multi-section configuration test completed!")

if __name__ == "__main__":
    test_multi_section_config()
