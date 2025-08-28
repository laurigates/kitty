#!/usr/bin/env python
# License: GPL v3 Copyright: 2024, Kovid Goyal <kovid at kovidgoyal.net>

"""Test accessibility integration in Window class"""

import sys
import unittest
from unittest.mock import MagicMock, patch

_plat = sys.platform.lower()
is_macos = 'darwin' in _plat


@unittest.skipUnless(is_macos, 'Accessibility integration tests are macOS specific')
class TestAccessibilityIntegration(unittest.TestCase):
    """Test that AccessibilityManager is properly integrated into Window"""
    
    def test_window_has_accessibility_manager(self):
        """Test that Window class has accessibility_manager attribute on macOS"""
        # Mock the necessary components to create a Window
        mock_tab = MagicMock()
        mock_tab.id = 1
        mock_tab.os_window_id = 1
        
        mock_child = MagicMock()
        mock_child.argv = ['test']
        
        mock_args = MagicMock()
        
        # Import after mocking to ensure proper setup
        with patch('kitty.window.add_window', return_value=1):
            with patch('kitty.window.cell_size_for_window', return_value=(10, 20)):
                with patch('kitty.window.get_options') as mock_opts:
                    mock_opts.return_value.scrollback_lines = 100
                    
                    from kitty.window import Window
                    
                    # Create a Window instance
                    window = Window(mock_tab, mock_child, mock_args)
                    
                    # Check that accessibility_manager exists
                    self.assertTrue(hasattr(window, 'accessibility_manager'))
                    
                    # On macOS, it should be initialized
                    if is_macos:
                        from kitty.accessibility import AccessibilityManager
                        self.assertIsNotNone(window.accessibility_manager)
                        self.assertIsInstance(window.accessibility_manager, AccessibilityManager)
                        # Check that the manager has a reference to the window
                        self.assertEqual(window.accessibility_manager.window, window)
    
    def test_accessibility_manager_can_access_screen(self):
        """Test that AccessibilityManager can access the window's screen"""
        with patch('kitty.window.add_window', return_value=1):
            with patch('kitty.window.cell_size_for_window', return_value=(10, 20)):
                with patch('kitty.window.get_options') as mock_opts:
                    mock_opts.return_value.scrollback_lines = 100
                    
                    from kitty.window import Window
                    
                    mock_tab = MagicMock()
                    mock_tab.id = 1
                    mock_tab.os_window_id = 1
                    
                    mock_child = MagicMock()
                    mock_child.argv = ['test']
                    
                    mock_args = MagicMock()
                    
                    window = Window(mock_tab, mock_child, mock_args)
                    
                    if window.accessibility_manager:
                        # The manager should be able to access the screen through its window reference
                        self.assertIsNotNone(window.accessibility_manager.window.screen)
                        self.assertTrue(hasattr(window.accessibility_manager.window.screen, 'linebuf'))
                        self.assertTrue(hasattr(window.accessibility_manager.window.screen, 'cursor'))


if __name__ == '__main__':
    unittest.main()