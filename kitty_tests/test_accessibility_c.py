#!/usr/bin/env python3
"""
Test C-level accessibility functions in Kitty.
"""

import sys
import os

# Add kitty to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitty.fast_data_types import (
    accessibility_get_terminal_text,
    accessibility_insert_text,
    accessibility_get_cursor_position,
    accessibility_notify_text_changed,
    cocoa_set_accessibility_value_impl,
    cocoa_get_accessibility_attributes_impl,
    cocoa_get_accessibility_num_characters_impl,
    cocoa_get_accessibility_visible_range_impl,
    cocoa_get_accessibility_selection_impl,
    cocoa_set_accessibility_selection_impl
)
from kitty.fast_data_types import Screen


def test_c_functions():
    """Test that C accessibility functions are available"""
    print("Testing C-level accessibility functions...")
    
    # Create a test screen
    screen = Screen(None, 24, 80)
    screen.draw("Hello, Voice Control!")
    
    # Test getting terminal text
    try:
        text = accessibility_get_terminal_text(screen)
        print(f"✅ accessibility_get_terminal_text: Got '{text[:50]}...'")
    except Exception as e:
        print(f"❌ accessibility_get_terminal_text failed: {e}")
    
    # Test getting cursor position
    try:
        pos = accessibility_get_cursor_position(screen)
        print(f"✅ accessibility_get_cursor_position: {pos}")
    except Exception as e:
        print(f"❌ accessibility_get_cursor_position failed: {e}")
    
    # Test text insertion (mock)
    try:
        result = accessibility_insert_text(1, "test text")
        print(f"✅ accessibility_insert_text: {result}")
    except Exception as e:
        print(f"❌ accessibility_insert_text failed: {e}")
    
    # Test notification
    try:
        accessibility_notify_text_changed(1)
        print("✅ accessibility_notify_text_changed: Called successfully")
    except Exception as e:
        print(f"❌ accessibility_notify_text_changed failed: {e}")
    
    print("\nTesting Cocoa accessibility functions...")
    
    # Test Cocoa functions
    try:
        # These may not work without a proper window context
        attrs = cocoa_get_accessibility_attributes_impl(0)
        print(f"✅ cocoa_get_accessibility_attributes_impl: {attrs}")
    except Exception as e:
        print(f"⚠️  cocoa_get_accessibility_attributes_impl: {e} (expected without window)")
    
    try:
        num_chars = cocoa_get_accessibility_num_characters_impl(0)
        print(f"✅ cocoa_get_accessibility_num_characters_impl: {num_chars}")
    except Exception as e:
        print(f"⚠️  cocoa_get_accessibility_num_characters_impl: {e} (expected without window)")
    
    print("\nAll C-level accessibility functions are compiled and available!")


if __name__ == '__main__':
    test_c_functions()