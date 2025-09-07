#!/usr/bin/env python
# License: GPL v3 Copyright: 2024, Kovid Goyal <kovid at kovidgoyal.net>

"""
macOS Voice Control accessibility support for Kitty terminal.

This module provides the bridge between Kitty's terminal buffer
and macOS accessibility APIs, enabling Voice Control dictation.
"""

import sys
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from kitty.window import Window

_plat = sys.platform.lower()
is_macos = 'darwin' in _plat

# Try to import C bridge functions
try:
    from kitty.fast_data_types import (
        accessibility_get_terminal_text,
        accessibility_get_cursor_text_position,
        accessibility_insert_text_at_cursor,
        accessibility_set_cursor_position,
        accessibility_get_number_of_characters,
        accessibility_get_visible_character_range,
        accessibility_post_notification,
    )
    c_bridge_available = True
except ImportError:
    c_bridge_available = False


class NotificationDebouncer:
    """Debounces accessibility notifications to avoid overwhelming Voice Control."""
    
    def __init__(self, delay: float = 0.1) -> None:
        """Initialize the notification debouncer.
        
        Args:
            delay: Minimum time between notifications in seconds
        """
        self.delay = delay
        self.last_sent: dict[str, float] = {}
    
    def should_post(self, notification_type: str) -> bool:
        """Check if a notification should be posted.
        
        Args:
            notification_type: Type of notification to check
            
        Returns:
            True if enough time has passed since the last notification
        """
        current_time = time.time()
        last_time = self.last_sent.get(notification_type, 0)
        
        if current_time - last_time > self.delay:
            self.last_sent[notification_type] = current_time
            return True
        return False


class AccessibilityManager:
    """Manages accessibility features for macOS Voice Control support."""
    
    def __init__(self, window: Optional['Window'] = None) -> None:
        """Initialize the accessibility manager.
        
        Args:
            window: The Kitty window to manage accessibility for
        """
        self.window = window
        self.enabled = is_macos and c_bridge_available
        self._debouncer = NotificationDebouncer()
        self._last_content_hash: Optional[int] = None
        self._last_cursor_pos: Optional[int] = None
    
    def get_terminal_text(self) -> str:
        """Get the full terminal buffer as text.
        
        Returns:
            The terminal buffer contents as a string
        """
        if c_bridge_available and self.window:
            return accessibility_get_terminal_text(self.window.id)
        return ""  # Fallback when C bridge not available
    
    def get_cursor_text_position(self) -> int:
        """Get the cursor position as a character offset.
        
        Returns:
            Character offset of cursor in terminal text
        """
        if c_bridge_available and self.window:
            return accessibility_get_cursor_text_position(self.window.id)
        return 0
    
    def insert_text_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position.
        
        Args:
            text: Text to insert (from Voice Control dictation)
        """
        if c_bridge_available and self.window and text:
            accessibility_insert_text_at_cursor(self.window.id, text)
    
    def set_cursor_position(self, position: int) -> None:
        """Set the cursor to a specific character position.
        
        Args:
            position: Character offset to move cursor to
        """
        if c_bridge_available and self.window:
            accessibility_set_cursor_position(self.window.id, position)
    
    def get_number_of_characters(self) -> int:
        """Get total number of characters in terminal buffer.
        
        Returns:
            Total character count
        """
        if c_bridge_available and self.window:
            return accessibility_get_number_of_characters(self.window.id)
        return 0
    
    def get_visible_character_range(self) -> tuple[int, int]:
        """Get the range of currently visible characters.
        
        Returns:
            Tuple of (start_offset, length) for visible text
        """
        if c_bridge_available and self.window:
            return accessibility_get_visible_character_range(self.window.id)
        return (0, 0)
    
    def notify_text_changed(self) -> None:
        """Post NSAccessibilityValueChangedNotification."""
        if not self.enabled or not self.window:
            return
            
        # Debounce notifications to avoid overwhelming Voice Control
        if self._debouncer.should_post("value_changed"):
            accessibility_post_notification(self.window.id, "value_changed")
    
    def notify_selection_changed(self) -> None:
        """Post NSAccessibilitySelectedTextChangedNotification."""
        if not self.enabled or not self.window:
            return
            
        # Debounce notifications to avoid overwhelming Voice Control
        if self._debouncer.should_post("selection_changed"):
            accessibility_post_notification(self.window.id, "selection_changed")
    
    def notify_focus_changed(self) -> None:
        """Post NSAccessibilityFocusedUIElementChangedNotification."""
        if not self.enabled or not self.window:
            return
            
        # Focus notifications don't need as much debouncing
        accessibility_post_notification(self.window.id, "focus_changed")
    
    def on_screen_update(self) -> None:
        """Called when screen content changes. Implements smart change detection."""
        if not self.enabled or not self.window:
            return
        
        # Check if content actually changed
        current_text = self.get_terminal_text()
        current_hash = hash(current_text) if current_text else None
        
        if current_hash != self._last_content_hash:
            self._last_content_hash = current_hash
            self.notify_text_changed()
        
        # Check cursor position changes
        current_cursor_pos = self.get_cursor_text_position()
        if current_cursor_pos != self._last_cursor_pos:
            self._last_cursor_pos = current_cursor_pos
            self.notify_selection_changed()

