#!/usr/bin/env python3
"""
Live accessibility testing script for manual validation with Voice Control.
This script runs an interactive Kitty session with accessibility features enabled
and provides real-time feedback for testing Voice Control integration.
"""

import sys
import os
import time
import subprocess
import signal
from datetime import datetime

# Add kitty to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class LiveAccessibilityTester:
    """Interactive tester for Voice Control integration"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.kitty_process = None
    
    def print_header(self):
        """Print test header"""
        print("\n" + "="*70)
        print("KITTY VOICE CONTROL LIVE TESTING")
        print("="*70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Platform: macOS {subprocess.getoutput('sw_vers -productVersion')}")
        print("="*70 + "\n")
    
    def check_prerequisites(self):
        """Check if prerequisites are met"""
        print("Checking prerequisites...")
        
        # Check if Kitty is built
        if not os.path.exists("kitty/launcher/kitty"):
            print("❌ Kitty not built. Run: ./dev.sh build --debug")
            return False
        
        # Check if running on macOS
        if sys.platform != 'darwin':
            print("❌ This test requires macOS")
            return False
        
        # Check Voice Control status
        vc_status = subprocess.getoutput("defaults read com.apple.preference.speech 'VoiceControl Enabled' 2>/dev/null")
        if vc_status != "1":
            print("⚠️  Voice Control appears to be disabled")
            print("   Enable it: System Settings → Accessibility → Voice Control")
        
        print("✅ Prerequisites checked")
        return True
    
    def start_kitty(self):
        """Start Kitty with accessibility enabled"""
        print("\nStarting Kitty with accessibility features...")
        
        env = os.environ.copy()
        env['KITTY_ENABLE_ACCESSIBILITY'] = '1'
        env['KITTY_DEBUG_ACCESSIBILITY'] = '1'
        
        # Start Kitty in a subprocess
        self.kitty_process = subprocess.Popen(
            ['./kitty/launcher/kitty', '--debug-keyboard'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        time.sleep(2)  # Give Kitty time to start
        
        if self.kitty_process.poll() is not None:
            print("❌ Failed to start Kitty")
            return False
        
        print("✅ Kitty started with PID:", self.kitty_process.pid)
        return True
    
    def run_test_scenario(self, name, instructions, expected):
        """Run a single test scenario"""
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{'='*60}")
        print(f"\nInstructions:")
        for i, instruction in enumerate(instructions, 1):
            print(f"  {i}. {instruction}")
        
        print(f"\nExpected Result:")
        print(f"  {expected}")
        
        print("\nPress Enter when ready to start test...")
        input()
        
        print("Testing... (press Enter when complete)")
        input()
        
        result = input("Did the test pass? (y/n): ").lower().strip() == 'y'
        
        self.test_results.append({
            'name': name,
            'passed': result,
            'timestamp': datetime.now().isoformat()
        })
        
        if result:
            print("✅ Test PASSED")
        else:
            print("❌ Test FAILED")
            notes = input("Enter failure notes (optional): ")
            if notes:
                self.test_results[-1]['notes'] = notes
        
        return result
    
    def run_all_tests(self):
        """Run all Voice Control test scenarios"""
        print("\n" + "="*70)
        print("STARTING TEST SCENARIOS")
        print("="*70)
        
        all_passed = True
        
        # Test 1: Basic Dictation
        all_passed &= self.run_test_scenario(
            "Basic Dictation",
            [
                "Activate Voice Control if not already active",
                "Click on the Kitty window to focus it",
                "Say: 'Type hello world'"
            ],
            "The text 'hello world' should appear at the cursor position"
        )
        
        # Test 2: Command Execution
        all_passed &= self.run_test_scenario(
            "Command Execution",
            [
                "Say: 'Type ls'",
                "Say: 'Press return'"
            ],
            "The ls command should execute and show directory listing"
        )
        
        # Test 3: Multi-line Input
        all_passed &= self.run_test_scenario(
            "Multi-line Input",
            [
                "Say: 'Type echo line one'",
                "Say: 'New line'",
                "Say: 'Type echo line two'"
            ],
            "Two lines of text should be visible, each on its own line"
        )
        
        # Test 4: Special Characters
        all_passed &= self.run_test_scenario(
            "Special Characters",
            [
                "Say: 'Type dollar sign HOME'"
            ],
            "The text '$HOME' should appear"
        )
        
        # Test 5: Navigation Commands
        all_passed &= self.run_test_scenario(
            "Navigation Commands",
            [
                "Say: 'Type pwd'",
                "Say: 'Move to beginning of line'",
                "Say: 'Type sudo space'"
            ],
            "The command should now read 'sudo pwd'"
        )
        
        # Test 6: Deletion
        all_passed &= self.run_test_scenario(
            "Text Deletion",
            [
                "Say: 'Type test text'",
                "Say: 'Delete word'"
            ],
            "The word 'text' should be deleted, leaving 'test'"
        )
        
        # Test 7: Complex Command
        all_passed &= self.run_test_scenario(
            "Complex Command",
            [
                "Say: 'Type git status dash dash porcelain'"
            ],
            "The text 'git status --porcelain' should appear"
        )
        
        return all_passed
    
    def test_with_accessibility_inspector(self):
        """Guide user through Accessibility Inspector testing"""
        print("\n" + "="*70)
        print("ACCESSIBILITY INSPECTOR VALIDATION")
        print("="*70)
        
        print("\nInstructions for Accessibility Inspector testing:")
        print("1. Open Xcode")
        print("2. Go to: Xcode → Open Developer Tool → Accessibility Inspector")
        print("3. Click the target button in Accessibility Inspector")
        print("4. Select the Kitty window")
        print("\nVerify the following attributes:")
        print("  - Role: AXTextArea")
        print("  - Value: [should show terminal content]")
        print("  - Number of Characters: [should match content length]")
        print("  - Selected Text Range: [should show cursor position]")
        print("\nPress Enter when ready to continue...")
        input()
        
        passed = input("Did Accessibility Inspector show correct attributes? (y/n): ").lower().strip() == 'y'
        
        self.test_results.append({
            'name': 'Accessibility Inspector Validation',
            'passed': passed,
            'timestamp': datetime.now().isoformat()
        })
        
        return passed
    
    def cleanup(self):
        """Clean up test environment"""
        print("\nCleaning up...")
        
        if self.kitty_process:
            print(f"Terminating Kitty (PID: {self.kitty_process.pid})")
            self.kitty_process.terminate()
            time.sleep(1)
            if self.kitty_process.poll() is None:
                self.kitty_process.kill()
        
        print("✅ Cleanup complete")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        
        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['name']}")
                    if 'notes' in result:
                        print(f"    Notes: {result['notes']}")
        
        # Save results
        results_file = ".claude/test-results/voice-control-live-test.txt"
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        with open(results_file, 'w') as f:
            f.write(f"Voice Control Live Test Results\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write(f"Total: {total}, Passed: {passed}, Failed: {failed}\n\n")
            
            for result in self.test_results:
                status = "PASS" if result['passed'] else "FAIL"
                f.write(f"{status}: {result['name']}\n")
                if 'notes' in result:
                    f.write(f"  Notes: {result['notes']}\n")
        
        print(f"\nResults saved to: {results_file}")
        
        return failed == 0
    
    def run(self):
        """Run the complete live testing session"""
        self.print_header()
        
        if not self.check_prerequisites():
            return False
        
        try:
            if not self.start_kitty():
                return False
            
            print("\n" + "="*70)
            print("IMPORTANT: Voice Control Setup")
            print("="*70)
            print("1. Enable Voice Control:")
            print("   System Settings → Accessibility → Voice Control → Enable")
            print("2. Set language to English")
            print("3. Enable 'Show commands' overlay for debugging")
            print("4. Make sure Kitty window is focused during tests")
            print("\nPress Enter when Voice Control is ready...")
            input()
            
            # Run test scenarios
            self.run_all_tests()
            
            # Test with Accessibility Inspector
            self.test_with_accessibility_inspector()
            
            # Print summary
            return self.print_summary()
            
        except KeyboardInterrupt:
            print("\n\nTest interrupted by user")
            return False
        
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    tester = LiveAccessibilityTester()
    
    print("This script will guide you through manual Voice Control testing.")
    print("Make sure you have Voice Control available on your system.")
    print("\nPress Enter to start or Ctrl+C to cancel...")
    input()
    
    success = tester.run()
    
    if success:
        print("\n✅ All tests passed successfully!")
    else:
        print("\n❌ Some tests failed. Please review the results.")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()