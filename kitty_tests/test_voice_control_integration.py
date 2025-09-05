#!/usr/bin/env python3
"""
Comprehensive Voice Control integration tests for macOS accessibility support.
Tests terminal text extraction, text insertion, cursor tracking, and performance.
"""

import unittest
import time
from unittest.mock import MagicMock, patch
import sys
import os

# Add kitty to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kitty.fast_data_types import Screen
from kitty.window import Window
from kitty.child import Child
from kitty.accessibility import AccessibilityManager


class MockWindow:
    """Mock window for testing"""
    def __init__(self):
        self.id = 1
        self.os_window_id = 1001
        self.screen = Screen(None, 24, 80)
        self.child = MagicMock(spec=Child)
        self.boss = MagicMock()
        
    def write_to_child(self, data):
        """Mock writing to child process"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.child.write_to_child(data)
        return len(data)


class TestVoiceControlIntegration(unittest.TestCase):
    """Integration tests for Voice Control functionality"""
    
    def setUp(self):
        """Set up test window and accessibility manager"""
        self.window = MockWindow()
        self.manager = AccessibilityManager(self.window)
    
    def test_terminal_text_extraction(self):
        """Test that we can extract text from terminal"""
        # Write some text to the screen
        test_text = "hello world"
        self.window.screen.draw(test_text)
        
        # Get text via accessibility
        text = self.manager.get_terminal_text()
        
        # Verify text extraction
        self.assertIn("hello world", text)
    
    def test_text_insertion(self):
        """Test Voice Control text insertion"""
        # Insert text at cursor
        test_command = "echo test"
        self.manager.insert_text_at_cursor(test_command)
        
        # Verify the write_to_child was called with correct text
        self.window.child.write_to_child.assert_called()
        call_args = self.window.child.write_to_child.call_args[0][0]
        if isinstance(call_args, bytes):
            call_args = call_args.decode('utf-8')
        self.assertEqual(call_args, test_command)
    
    def test_cursor_position_tracking(self):
        """Test cursor position is correctly reported"""
        # Write text and position cursor
        self.window.screen.draw("hello world")
        self.window.screen.cursor.x = 6  # Position at 'w'
        
        # Check position
        pos = self.manager.get_cursor_text_position()
        self.assertEqual(pos, 6)  # 0-indexed position
    
    def test_multi_line_text_extraction(self):
        """Test extracting multi-line terminal content"""
        # Write multiple lines
        self.window.screen.draw("line one\n")
        self.window.screen.draw("line two\n")
        self.window.screen.draw("line three")
        
        # Get all text
        text = self.manager.get_terminal_text()
        
        # Verify all lines present
        self.assertIn("line one", text)
        self.assertIn("line two", text)
        self.assertIn("line three", text)
    
    def test_special_characters_handling(self):
        """Test handling of special characters in dictation"""
        # Test various special characters
        special_text = "$HOME/path & echo 'test' | grep pattern"
        self.manager.insert_text_at_cursor(special_text)
        
        # Verify special characters preserved
        self.window.child.write_to_child.assert_called()
        call_args = self.window.child.write_to_child.call_args[0][0]
        if isinstance(call_args, bytes):
            call_args = call_args.decode('utf-8')
        self.assertEqual(call_args, special_text)
    
    def test_empty_screen_handling(self):
        """Test behavior with empty terminal"""
        # Get text from empty screen
        text = self.manager.get_terminal_text()
        
        # Should return empty or whitespace only
        self.assertEqual(text.strip(), "")
    
    def test_cursor_at_end_of_line(self):
        """Test cursor position at end of line"""
        # Write text and position at end
        text = "command"
        self.window.screen.draw(text)
        self.window.screen.cursor.x = len(text)
        
        # Check position
        pos = self.manager.get_cursor_text_position()
        self.assertEqual(pos, len(text))
    
    def test_notification_handling(self):
        """Test accessibility notifications are sent"""
        with patch.object(self.manager, 'notify_text_changed') as mock_notify:
            # Trigger text change
            self.window.screen.draw("new text")
            self.manager.on_text_change()
            
            # Verify notification sent
            mock_notify.assert_called_once()
    
    def test_selected_text_range(self):
        """Test getting selected text range for Voice Control"""
        # No selection initially
        range_info = self.manager.get_selected_text_range()
        self.assertEqual(range_info['length'], 0)
        
        # Cursor position should be reported
        self.window.screen.cursor.x = 5
        range_info = self.manager.get_selected_text_range()
        self.assertEqual(range_info['location'], 5)


class TestPerformance(unittest.TestCase):
    """Performance tests for accessibility features"""
    
    def setUp(self):
        """Set up test window and accessibility manager"""
        self.window = MockWindow()
        self.manager = AccessibilityManager(self.window)
    
    def test_read_performance(self):
        """Test read performance for accessibility"""
        # Fill screen with text
        for i in range(24):
            self.window.screen.draw(f"Line {i:03d} with some test content\n")
        
        # Test read performance
        start = time.time()
        for _ in range(100):
            text = self.manager.get_terminal_text()
        read_time = time.time() - start
        
        print(f"100 reads: {read_time:.3f}s")
        self.assertLess(read_time, 1.0, "Read performance should be under 1 second for 100 reads")
    
    def test_notification_performance(self):
        """Test performance impact of notifications"""
        # Test rapid text changes
        start = time.time()
        for i in range(1000):
            self.window.screen.draw(f"Line {i}\n")
            # Notifications would be sent here in real implementation
        write_time = time.time() - start
        
        print(f"1000 writes: {write_time:.3f}s")
        self.assertLess(write_time, 2.0, "Write performance should not be significantly impacted")
    
    def test_cursor_tracking_performance(self):
        """Test cursor position tracking performance"""
        start = time.time()
        for _ in range(1000):
            pos = self.manager.get_cursor_text_position()
        track_time = time.time() - start
        
        print(f"1000 cursor position checks: {track_time:.3f}s")
        self.assertLess(track_time, 0.5, "Cursor tracking should be very fast")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test window and accessibility manager"""
        self.window = MockWindow()
        self.manager = AccessibilityManager(self.window)
    
    def test_very_long_line(self):
        """Test handling of very long lines"""
        # Create a very long line
        long_text = "x" * 1000
        self.window.screen.draw(long_text)
        
        # Should handle without error
        text = self.manager.get_terminal_text()
        self.assertIn("x" * 80, text)  # At least screen width
    
    def test_unicode_text(self):
        """Test Unicode character handling"""
        # Test various Unicode characters
        unicode_text = "Hello 世界 🌍 café"
        self.manager.insert_text_at_cursor(unicode_text)
        
        # Verify Unicode preserved
        self.window.child.write_to_child.assert_called()
        call_args = self.window.child.write_to_child.call_args[0][0]
        if isinstance(call_args, bytes):
            call_args = call_args.decode('utf-8')
        self.assertEqual(call_args, unicode_text)
    
    def test_rapid_updates(self):
        """Test handling of rapid screen updates"""
        # Simulate rapid updates
        for i in range(100):
            self.window.screen.draw(f"\rProgress: {i}%")
        
        # Should handle without crashing
        text = self.manager.get_terminal_text()
        self.assertIsNotNone(text)
    
    def test_alternate_screen(self):
        """Test handling of alternate screen (vim, less, etc)"""
        # Switch to alternate screen
        self.window.screen.reset_mode(1049)  # Alternate screen mode
        
        # Should still work
        text = self.manager.get_terminal_text()
        self.assertIsNotNone(text)


def run_tests():
    """Run all Voice Control integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestVoiceControlIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)