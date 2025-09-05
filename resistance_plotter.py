#!/usr/bin/env python3
"""
DMM6500 Resistance Measurement Plotter

This script retrieves resistance measurements from a Keithley DMM6500 Digital Multimeter
at configurable intervals and displays them in a real-time plot with autoscaling.
After at least 10 measurements, it shows statistics for the latest 10 measurements.

Usage:
    python3 resistance_plotter.py [--interval SECONDS] [--max-points MAX] [--demo] [--no-gui]

Arguments:
    --interval SECONDS  Measurement interval in seconds (default: 1.0)
    --max-points MAX    Maximum number of points to display (default: 100)
    --demo             Run in demo mode without hardware connection
    --no-gui           Run without GUI (text-only mode)

Example:
    python3 resistance_plotter.py --interval 2.5 --max-points 50
    python3 resistance_plotter.py --demo --no-gui --interval 1
"""

import sys
import time
import argparse
import threading
from collections import deque
import numpy as np
from datetime import datetime

# Handle matplotlib imports gracefully
try:
    import matplotlib
    # Set a non-interactive backend for headless environments
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Running in text-only mode.")

# Add the libs directory to the path for importing DMM6500
sys.path.append('./libs')

try:
    from DMM6500 import DMM6500
except ImportError:
    print("Error: Could not import DMM6500. Make sure the libs directory is accessible.")
    sys.exit(1)


class ResistancePlotter:
    """
    Real-time resistance measurement plotter for DMM6500.
    """
    
    def __init__(self, interval=1.0, max_points=100, demo_mode=False, no_gui=False):
        """
        Initialize the resistance plotter.
        
        Args:
            interval (float): Measurement interval in seconds
            max_points (int): Maximum number of points to display in plot
            demo_mode (bool): Run in demo mode without hardware
            no_gui (bool): Run in text-only mode without GUI
        """
        self.interval = interval
        self.max_points = max_points
        self.demo_mode = demo_mode
        self.no_gui = no_gui or not MATPLOTLIB_AVAILABLE
        
        # Data storage
        self.timestamps = deque(maxlen=max_points)
        self.resistances = deque(maxlen=max_points)
        self.measurement_count = 0
        
        # DMM6500 connection
        self.dmm = None
        self.measuring = False
        self.measurement_thread = None
        
        # Statistics for latest 10 measurements
        self.latest_10_stats = {
            'mean': 0.0,
            'std': 0.0,
            'min': 0.0,
            'max': 0.0
        }
        
        # Setup matplotlib if available and not in no-gui mode
        if not self.no_gui:
            self.setup_plot()
        else:
            print("Running in text-only mode")
            self.fig = None
            self.ax_main = None
            self.ax_stats = None
        
    def setup_plot(self):
        """Setup the matplotlib figure and axes."""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        plt.ion()  # Turn on interactive mode
        self.fig, (self.ax_main, self.ax_stats) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Main plot for resistance vs time
        self.line, = self.ax_main.plot([], [], 'b-', linewidth=2, label='Resistance')
        self.ax_main.set_xlabel('Time (s)')
        self.ax_main.set_ylabel('Resistance (Ω)')
        self.ax_main.set_title('DMM6500 Resistance Measurements - Real Time')
        self.ax_main.grid(True, alpha=0.3)
        self.ax_main.legend()
        
        # Statistics plot (bar chart for latest 10 measurements)
        self.ax_stats.set_title('Statistics for Latest 10 Measurements')
        self.ax_stats.set_ylabel('Resistance (Ω)')
        
        # Text for displaying statistics
        self.stats_text = self.ax_main.text(0.02, 0.98, '', transform=self.ax_main.transAxes,
                                          verticalalignment='top', bbox=dict(boxstyle='round', 
                                          facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
    def connect_dmm(self):
        """Connect to the DMM6500."""
        if self.demo_mode:
            print("Running in demo mode - no hardware connection required")
            return True
            
        try:
            print("Connecting to DMM6500...")
            self.dmm = DMM6500(auto_connect=True)
            if self.dmm.status == "Connected":
                print("Successfully connected to DMM6500")
                return True
            else:
                print("Failed to connect to DMM6500")
                return False
        except Exception as e:
            print(f"Error connecting to DMM6500: {e}")
            return False
    
    def disconnect_dmm(self):
        """Disconnect from the DMM6500."""
        if self.dmm and not self.demo_mode:
            try:
                self.dmm.disconnect()
                print("Disconnected from DMM6500")
            except Exception as e:
                print(f"Error disconnecting from DMM6500: {e}")
    
    def measure_resistance(self):
        """Measure resistance from DMM6500 or generate demo data."""
        if self.demo_mode:
            # Generate realistic demo resistance data with some noise
            base_resistance = 1000.0  # 1kΩ base
            noise = np.random.normal(0, 5)  # ±5Ω noise
            drift = 50 * np.sin(self.measurement_count * 0.1)  # Slow drift
            return base_resistance + noise + drift
        else:
            try:
                return self.dmm.measure_resistance()
            except Exception as e:
                print(f"Error measuring resistance: {e}")
                return None
    
    def calculate_latest_10_stats(self):
        """Calculate statistics for the latest 10 measurements."""
        if len(self.resistances) >= 10:
            latest_10 = list(self.resistances)[-10:]
            self.latest_10_stats = {
                'mean': np.mean(latest_10),
                'std': np.std(latest_10),
                'min': np.min(latest_10),
                'max': np.max(latest_10)
            }
            return True
        return False
    
    def update_stats_display(self):
        """Update the statistics display."""
        stats_available = self.calculate_latest_10_stats()
        
        if stats_available:
            stats_text = (f"Latest 10 measurements:\n"
                         f"Mean: {self.latest_10_stats['mean']:.2f} Ω\n"
                         f"Std Dev: {self.latest_10_stats['std']:.2f} Ω\n"
                         f"Min: {self.latest_10_stats['min']:.2f} Ω\n"
                         f"Max: {self.latest_10_stats['max']:.2f} Ω")
        else:
            remaining = 10 - len(self.resistances)
            stats_text = f"Need {remaining} more measurements\nfor statistics"
        
        # Add measurement info
        stats_text = (f"Measurements: {self.measurement_count}\n"
                     f"Interval: {self.interval:.1f}s\n" + stats_text)
        
        # Update text display (GUI mode)
        if not self.no_gui and hasattr(self, 'stats_text'):
            self.stats_text.set_text(stats_text)
            
            # Update statistics subplot with bar chart of latest 10
            self.ax_stats.clear()
            if stats_available:
                latest_10 = list(self.resistances)[-10:]
                x_pos = range(len(latest_10))
                bars = self.ax_stats.bar(x_pos, latest_10, alpha=0.7)
                self.ax_stats.axhline(y=self.latest_10_stats['mean'], color='red', 
                                    linestyle='--', label=f"Mean: {self.latest_10_stats['mean']:.2f}Ω")
                self.ax_stats.set_xlabel('Measurement Index (latest 10)')
                self.ax_stats.set_ylabel('Resistance (Ω)')
                self.ax_stats.set_title('Latest 10 Measurements')
                self.ax_stats.legend()
                self.ax_stats.grid(True, alpha=0.3)
            else:
                self.ax_stats.text(0.5, 0.5, f'Need {10 - len(self.resistances)} more measurements\nfor statistics',
                                 ha='center', va='center', transform=self.ax_stats.transAxes,
                                 fontsize=12, bbox=dict(boxstyle='round', facecolor='lightgray'))
                self.ax_stats.set_title('Statistics - Waiting for Data')
        
        # Print to console (both GUI and text modes)
        if self.no_gui and stats_available:
            print(f"\n--- Latest 10 Measurements Statistics ---")
            print(f"Mean: {self.latest_10_stats['mean']:.2f} Ω")
            print(f"Std Dev: {self.latest_10_stats['std']:.2f} Ω")
            print(f"Min: {self.latest_10_stats['min']:.2f} Ω")
            print(f"Max: {self.latest_10_stats['max']:.2f} Ω")
            print("-" * 40)
    
    def measurement_loop(self):
        """Main measurement loop running in a separate thread."""
        start_time = time.time()
        
        while self.measuring:
            try:
                # Take measurement
                resistance = self.measure_resistance()
                
                if resistance is not None:
                    # Store data
                    current_time = time.time() - start_time
                    self.timestamps.append(current_time)
                    self.resistances.append(resistance)
                    self.measurement_count += 1
                    
                    print(f"Measurement {self.measurement_count}: {resistance:.2f} Ω "
                          f"(t={current_time:.1f}s)")
                
                # Wait for next measurement
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"Error in measurement loop: {e}")
                time.sleep(self.interval)
    
    def update_plot(self, frame):
        """Update the plot with new data."""
        if self.no_gui:
            return
            
        if len(self.timestamps) > 0 and len(self.resistances) > 0:
            # Update main plot
            self.line.set_data(self.timestamps, self.resistances)
            
            # Auto-scale the plot
            self.ax_main.relim()
            self.ax_main.autoscale_view()
            
            # Update statistics
            self.update_stats_display()
        
        return self.line,
    
    def start_measurements(self):
        """Start the measurement process."""
        if not self.connect_dmm():
            return False
        
        print(f"Starting measurements every {self.interval} seconds...")
        print("Press Ctrl+C to stop")
        
        # Start measurement thread
        self.measuring = True
        self.measurement_thread = threading.Thread(target=self.measurement_loop)
        self.measurement_thread.daemon = True
        self.measurement_thread.start()
        
        # Start animation only in GUI mode
        if not self.no_gui and MATPLOTLIB_AVAILABLE:
            self.ani = animation.FuncAnimation(self.fig, self.update_plot, 
                                             interval=500, blit=False, cache_frame_data=False)
        
        return True
    
    def stop_measurements(self):
        """Stop the measurement process."""
        print("\nStopping measurements...")
        self.measuring = False
        
        if self.measurement_thread:
            self.measurement_thread.join(timeout=2)
        
        self.disconnect_dmm()
    
    def run(self):
        """Run the resistance plotter."""
        try:
            if self.start_measurements():
                if self.no_gui:
                    # Text-only mode - just wait for the measurement thread
                    print("Running in text-only mode. Measurements will be displayed below:")
                    while self.measuring:
                        time.sleep(1)
                        # Update stats display every few seconds in text mode
                        if self.measurement_count % 5 == 0 and self.measurement_count > 0:
                            self.update_stats_display()
                else:
                    # GUI mode
                    plt.show(block=True)
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.stop_measurements()


def main():
    """Main function to parse arguments and run the plotter."""
    parser = argparse.ArgumentParser(description='DMM6500 Resistance Measurement Plotter')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Measurement interval in seconds (default: 1.0)')
    parser.add_argument('--max-points', type=int, default=100,
                       help='Maximum number of points to display (default: 100)')
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode without hardware connection')
    parser.add_argument('--no-gui', action='store_true',
                       help='Run without GUI (text-only mode)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interval <= 0:
        print("Error: Interval must be positive")
        return 1
    
    if args.max_points <= 0:
        print("Error: Max points must be positive")
        return 1
    
    print("DMM6500 Resistance Measurement Plotter")
    print("=" * 40)
    print(f"Measurement interval: {args.interval} seconds")
    print(f"Maximum plot points: {args.max_points}")
    print(f"Demo mode: {'Yes' if args.demo else 'No'}")
    print(f"GUI mode: {'No' if args.no_gui else 'Yes'}")
    print()
    
    # Create and run plotter
    plotter = ResistancePlotter(
        interval=args.interval,
        max_points=args.max_points,
        demo_mode=args.demo,
        no_gui=args.no_gui
    )
    
    return plotter.run()


if __name__ == "__main__":
    sys.exit(main() or 0)