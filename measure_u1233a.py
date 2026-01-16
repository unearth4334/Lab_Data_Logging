#!/usr/bin/env python3
"""
Script to retrieve measurements from U1233A multimeter with real-time plotting.

This script:
- Connects to U1233A multimeter via serial port
- Continuously retrieves measurements 
- Displays data in a real-time scaling plot
- Saves data to CSV file with date-formatted filename (yyyy-mm-dd)

Usage:
    python measure_u1233a.py [--samples N] [--interval SECONDS]
    
Options:
    --samples N         Number of samples to collect (default: continuous until Ctrl+C)
    --interval SECONDS  Time between measurements in seconds (default: 0.5)
"""

import sys
import os
import time
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import argparse

# Add libs directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

try:
    from U1233A import U1233A
except ImportError:
    from libs.U1233A import U1233A


class U1233ADataLogger:
    """Real-time data logging and plotting for U1233A multimeter."""
    
    def __init__(self, max_points=100, interval=0.5):
        """
        Initialize the data logger.
        
        Args:
            max_points (int): Maximum number of points to display on plot
            interval (float): Time between measurements in seconds
        """
        self.max_points = max_points
        self.interval = interval
        self.multimeter = None
        self.csv_file = None
        self.csv_writer = None
        
        # Data storage
        self.timestamps = deque(maxlen=max_points)
        self.measurements = deque(maxlen=max_points)
        self.start_time = None
        self.measurement_count = 0
        
        # Plot setup
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2)
        self.ax.set_xlabel('Time (seconds)', fontsize=12)
        self.ax.set_ylabel('Measurement Value', fontsize=12)
        self.ax.set_title('U1233A Real-Time Measurements', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        
    def connect(self):
        """Connect to the U1233A multimeter."""
        print("Connecting to U1233A multimeter...")
        try:
            self.multimeter = U1233A()
            print(f"Successfully connected to {self.multimeter.identity}")
            return True
        except Exception as e:
            print(f"Error connecting to U1233A: {e}")
            return False
    
    def open_csv_file(self):
        """Open CSV file with date-formatted filename."""
        # Create filename with format: yyyy-mm-dd_u1233a_measurements.csv
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}_u1233a_measurements.csv"
        
        try:
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            # Write header
            self.csv_writer.writerow(['Timestamp', 'Elapsed_Time_s', 'Measurement', 'Error'])
            print(f"Saving data to: {filename}")
            return filename
        except Exception as e:
            print(f"Error opening CSV file: {e}")
            return None
    
    def close_csv_file(self):
        """Close the CSV file."""
        if self.csv_file:
            self.csv_file.close()
            print("CSV file closed.")
    
    def get_measurement(self):
        """Get a single measurement from the multimeter."""
        try:
            measurement, error = self.multimeter.measure()
            return measurement, error
        except Exception as e:
            print(f"Error getting measurement: {e}")
            return None, None
    
    def update_plot(self, frame):
        """Update function for animation - called periodically."""
        # Get measurement
        measurement, error = self.get_measurement()
        
        if measurement is not None:
            # Calculate elapsed time
            if self.start_time is None:
                self.start_time = time.time()
                elapsed = 0.0
            else:
                elapsed = time.time() - self.start_time
            
            # Store data
            self.timestamps.append(elapsed)
            self.measurements.append(measurement)
            self.measurement_count += 1
            
            # Write to CSV
            if self.csv_writer:
                timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                self.csv_writer.writerow([timestamp_str, f"{elapsed:.3f}", 
                                         f"{measurement:.6f}", f"{error:.6f}"])
                self.csv_file.flush()  # Ensure data is written immediately
            
            # Update plot
            self.line.set_data(list(self.timestamps), list(self.measurements))
            
            # Auto-scale axes
            if len(self.timestamps) > 0:
                self.ax.set_xlim(min(self.timestamps), max(self.timestamps) + 1)
                
                if len(self.measurements) > 0:
                    y_min = min(self.measurements)
                    y_max = max(self.measurements)
                    y_range = y_max - y_min
                    if y_range < 1e-6:  # Handle case where all values are the same
                        y_range = abs(y_max) * 0.1 if y_max != 0 else 1
                    margin = y_range * 0.1
                    self.ax.set_ylim(y_min - margin, y_max + margin)
            
            # Update title with current measurement
            self.ax.set_title(
                f'U1233A Real-Time Measurements (Count: {self.measurement_count}, Current: {measurement:.6f})',
                fontsize=14, fontweight='bold'
            )
            
            # Print to console
            print(f"[{self.measurement_count}] Time: {elapsed:.2f}s, Value: {measurement:.6f} ± {error:.6f}")
        
        return self.line,
    
    def start_logging(self, max_samples=None):
        """
        Start continuous logging with real-time plot.
        
        Args:
            max_samples (int): Maximum number of samples to collect, or None for continuous
        """
        if not self.connect():
            return
        
        filename = self.open_csv_file()
        if not filename:
            return
        
        print(f"\nStarting measurement logging...")
        print(f"Update interval: {self.interval} seconds")
        if max_samples:
            print(f"Will collect {max_samples} samples")
        else:
            print("Continuous mode - Press Ctrl+C to stop")
        print("\n" + "="*60)
        
        try:
            # Create animation
            # Convert interval from seconds to milliseconds
            ani = animation.FuncAnimation(
                self.fig, 
                self.update_plot,
                interval=int(self.interval * 1000),
                blit=True,
                cache_frame_data=False
            )
            
            plt.tight_layout()
            plt.show()
            
        except KeyboardInterrupt:
            print("\n\nMeasurement stopped by user (Ctrl+C)")
        except Exception as e:
            print(f"\nError during measurement: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("\nCleaning up...")
        self.close_csv_file()
        
        if self.multimeter:
            try:
                self.multimeter.disconnect()
            except:
                pass
        
        print(f"Total measurements collected: {self.measurement_count}")
        print("Done.")


def main():
    """Main function to parse arguments and start logging."""
    parser = argparse.ArgumentParser(
        description='Retrieve measurements from U1233A multimeter with real-time plotting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python measure_u1233a.py                    # Continuous mode
  python measure_u1233a.py --samples 100      # Collect 100 samples
  python measure_u1233a.py --interval 1.0     # 1 second between samples
        """
    )
    
    parser.add_argument(
        '--samples', 
        type=int, 
        default=None,
        help='Number of samples to collect (default: continuous until Ctrl+C)'
    )
    
    parser.add_argument(
        '--interval', 
        type=float, 
        default=0.5,
        help='Time between measurements in seconds (default: 0.5)'
    )
    
    parser.add_argument(
        '--max-points',
        type=int,
        default=100,
        help='Maximum number of points to display on plot (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interval <= 0:
        print("Error: Interval must be positive")
        sys.exit(1)
    
    if args.samples is not None and args.samples <= 0:
        print("Error: Number of samples must be positive")
        sys.exit(1)
    
    if args.max_points <= 0:
        print("Error: Max points must be positive")
        sys.exit(1)
    
    # Create logger and start
    logger = U1233ADataLogger(max_points=args.max_points, interval=args.interval)
    logger.start_logging(max_samples=args.samples)


if __name__ == "__main__":
    main()
