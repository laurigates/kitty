#!/usr/bin/env python3
"""
Performance testing for macOS Voice Control accessibility implementation.
Measures the performance impact of accessibility features on terminal operations.
"""

import time
import sys
import os
import json
from typing import Dict, List, Any

# Add kitty to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kitty.fast_data_types import Screen
from kitty.window import Window
from kitty.accessibility import AccessibilityManager


class PerformanceTester:
    """Performance testing for accessibility features"""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
        self.window = self._create_test_window()
        self.manager = AccessibilityManager(self.window)
    
    def _create_test_window(self):
        """Create a test window for benchmarking"""
        class MockChild:
            def write_to_child(self, data):
                return len(data)
        
        class MockBoss:
            pass
        
        class TestWindow:
            def __init__(self):
                self.id = 1
                self.os_window_id = 1001
                self.screen = Screen(None, 24, 80)
                self.child = MockChild()
                self.boss = MockBoss()
                
            def write_to_child(self, data):
                if isinstance(data, str):
                    data = data.encode('utf-8')
                return self.child.write_to_child(data)
        
        return TestWindow()
    
    def benchmark_text_extraction(self, iterations: int = 100):
        """Benchmark terminal text extraction performance"""
        print(f"Benchmarking text extraction ({iterations} iterations)...")
        
        # Fill screen with test content
        for i in range(24):
            self.window.screen.draw(f"Line {i:03d}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.\n")
        
        # Benchmark extraction
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            text = self.manager.get_terminal_text()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results['text_extraction'] = {
            'iterations': iterations,
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'total_s': sum(times)
        }
        
        print(f"  Average: {avg_time * 1000:.3f}ms")
        print(f"  Min: {min_time * 1000:.3f}ms")
        print(f"  Max: {max_time * 1000:.3f}ms")
        
        return avg_time < 0.010  # Should be under 10ms
    
    def benchmark_text_insertion(self, iterations: int = 100):
        """Benchmark text insertion performance"""
        print(f"Benchmarking text insertion ({iterations} iterations)...")
        
        test_strings = [
            "echo test",
            "ls -la /usr/local/bin",
            "git status --porcelain",
            "python3 -m venv .venv",
            "npm install --save-dev"
        ]
        
        times = []
        for i in range(iterations):
            test_text = test_strings[i % len(test_strings)]
            start = time.perf_counter()
            self.manager.insert_text_at_cursor(test_text)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results['text_insertion'] = {
            'iterations': iterations,
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'total_s': sum(times)
        }
        
        print(f"  Average: {avg_time * 1000:.3f}ms")
        print(f"  Min: {min_time * 1000:.3f}ms")
        print(f"  Max: {max_time * 1000:.3f}ms")
        
        return avg_time < 0.005  # Should be under 5ms
    
    def benchmark_cursor_tracking(self, iterations: int = 1000):
        """Benchmark cursor position tracking"""
        print(f"Benchmarking cursor tracking ({iterations} iterations)...")
        
        times = []
        for i in range(iterations):
            # Move cursor to different positions
            self.window.screen.cursor.x = i % 80
            self.window.screen.cursor.y = (i // 80) % 24
            
            start = time.perf_counter()
            pos = self.manager.get_cursor_text_position()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        self.results['cursor_tracking'] = {
            'iterations': iterations,
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'total_s': sum(times)
        }
        
        print(f"  Average: {avg_time * 1000:.3f}ms")
        print(f"  Min: {min_time * 1000:.3f}ms")
        print(f"  Max: {max_time * 1000:.3f}ms")
        
        return avg_time < 0.001  # Should be under 1ms
    
    def benchmark_notification_overhead(self, iterations: int = 1000):
        """Benchmark the overhead of accessibility notifications"""
        print(f"Benchmarking notification overhead ({iterations} iterations)...")
        
        # Test without notifications
        start = time.perf_counter()
        for i in range(iterations):
            self.window.screen.draw(f"Line {i}\n")
        time_without = time.perf_counter() - start
        
        # Test with notifications enabled
        self.manager.notifications_enabled = True
        start = time.perf_counter()
        for i in range(iterations):
            self.window.screen.draw(f"Line {i}\n")
            self.manager.on_text_change()
        time_with = time.perf_counter() - start
        
        overhead = ((time_with - time_without) / time_without) * 100 if time_without > 0 else 0
        
        self.results['notification_overhead'] = {
            'iterations': iterations,
            'without_notifications_s': time_without,
            'with_notifications_s': time_with,
            'overhead_percent': overhead
        }
        
        print(f"  Without notifications: {time_without:.3f}s")
        print(f"  With notifications: {time_with:.3f}s")
        print(f"  Overhead: {overhead:.1f}%")
        
        return overhead < 5.0  # Should be less than 5% overhead
    
    def benchmark_memory_usage(self, iterations: int = 10000):
        """Benchmark memory usage of accessibility features"""
        print(f"Benchmarking memory usage ({iterations} operations)...")
        
        import tracemalloc
        tracemalloc.start()
        
        # Baseline memory
        snapshot1 = tracemalloc.take_snapshot()
        
        # Perform many operations
        for i in range(iterations):
            if i % 100 == 0:
                # Extract text
                text = self.manager.get_terminal_text()
            if i % 50 == 0:
                # Insert text
                self.manager.insert_text_at_cursor(f"test {i}")
            # Track cursor
            pos = self.manager.get_cursor_text_position()
        
        # Final memory
        snapshot2 = tracemalloc.take_snapshot()
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        total_diff = sum(stat.size_diff for stat in top_stats)
        
        self.results['memory_usage'] = {
            'iterations': iterations,
            'memory_increase_kb': total_diff / 1024
        }
        
        print(f"  Memory increase: {total_diff / 1024:.2f} KB")
        
        tracemalloc.stop()
        
        return total_diff < 1024 * 1024  # Should be less than 1MB increase
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("\n" + "="*60)
        print("Running Accessibility Performance Benchmarks")
        print("="*60 + "\n")
        
        all_passed = True
        
        # Run benchmarks
        all_passed &= self.benchmark_text_extraction()
        print()
        all_passed &= self.benchmark_text_insertion()
        print()
        all_passed &= self.benchmark_cursor_tracking()
        print()
        all_passed &= self.benchmark_notification_overhead()
        print()
        all_passed &= self.benchmark_memory_usage()
        
        # Save results
        self.save_results()
        
        # Print summary
        print("\n" + "="*60)
        print("Performance Summary")
        print("="*60)
        
        if all_passed:
            print("✅ All performance benchmarks PASSED")
        else:
            print("❌ Some performance benchmarks FAILED")
        
        print("\nKey Metrics:")
        print(f"  Text extraction: {self.results['text_extraction']['average_ms']:.3f}ms avg")
        print(f"  Text insertion: {self.results['text_insertion']['average_ms']:.3f}ms avg")
        print(f"  Cursor tracking: {self.results['cursor_tracking']['average_ms']:.3f}ms avg")
        print(f"  Notification overhead: {self.results['notification_overhead']['overhead_percent']:.1f}%")
        print(f"  Memory increase: {self.results['memory_usage']['memory_increase_kb']:.2f} KB")
        
        return all_passed
    
    def save_results(self):
        """Save performance results to file"""
        results_dir = ".claude"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
        
        filepath = os.path.join(results_dir, "performance-metrics.json")
        
        # Add metadata
        self.results['metadata'] = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'platform': sys.platform,
            'python_version': sys.version
        }
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nResults saved to: {filepath}")


def main():
    """Main entry point for performance testing"""
    tester = PerformanceTester()
    success = tester.run_all_benchmarks()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()