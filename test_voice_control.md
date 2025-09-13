# Testing Voice Control Dictation in Kitty

## Setup
1. Make sure Voice Control is enabled: System Settings > Accessibility > Voice Control
2. Set Voice Control to "Dictation Mode" (say "Dictation mode")
3. Launch the built kitty: `kitty/launcher/kitty`

## Test Steps

### Basic Dictation Test
1. Focus on the kitty terminal window
2. Say "Dictation mode" to enable dictation
3. Try dictating simple text like "Hello world"
4. Check if text appears in the terminal

### Debug Output
Watch Console.app for debug messages with "[Voice Control Debug]" prefix to see:
- Which accessibility methods are being called
- What text is being received
- How the text is being processed

### Expected Flow
1. Voice Control calls either:
   - `setAccessibilityValue:` with the dictated text
   - `accessibilityInsertText:` with the dictated text
   - `insertText:replacementRange:` directly

2. The text should be inserted via `insertText:replacementRange:` which:
   - Processes the text through the normal keyboard input pipeline
   - Respects terminal modes
   - Appears at the cursor position

## Debugging Commands
- Check Console.app: `log stream --predicate 'eventMessage contains "Voice Control Debug"'`
- Or in Terminal: `log show --predicate 'eventMessage contains "Voice Control Debug"' --last 5m`

## Known Issues Fixed
- Text insertion now uses proper NSTextInputClient protocol
- Added support for multiple accessibility text insertion methods
- Debug logging added to trace the flow