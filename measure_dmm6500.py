#!/usr/bin/env python3
"""
Script to retrieve measurements from DMM6500 multimeter with CSV logging.

This script:
- Connects to Keithley DMM6500 multimeter via VISA
- Continuously retrieves measurements 
- Saves data to CSV file with date-formatted filename (yyyy-mm-dd)
- Optionally displays data in a real-time scaling plot (--live-plot)

Usage:
    python measure_dmm6500.py [--samples N] [--interval SECONDS] [--measurement TYPE] [--live-plot]
    
Options:
    --samples N         Number of samples to collect (default: continuous until Ctrl+C)
    --interval SECONDS  Time between measurements in seconds (default: 0.5)
    --measurement TYPE  Measurement type: voltage, current, resistance, temperature (default: temperature)
    --max-points N      Maximum number of points to display on plot (default: 100)
    --live-plot         Enable live plotting (default: disabled)
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
    from DMM6500 import DMM6500
except ImportError as e:
    print(f"Error: Could not import DMM6500 module. Make sure libs/DMM6500.py exists.")
    print(f"Import error: {e}")
    sys.exit(1)


class DMM6500DataLogger:
    """Real-time data logging and plotting for DMM6500 multimeter."""
    
    def __init__(self, max_points=100, interval=0.5, measurement_type='temperature', enable_plot=False):
        """
        Initialize the data logger.
        
        Args:
            max_points (int): Maximum number of points to display on plot
            interval (float): Time between measurements in seconds
            measurement_type (str): Type of measurement (voltage, current, resistance, temperature)
            enable_plot (bool): Whether to show live plotting
        """
        self.max_points = max_points
        self.interval = interval
        self.measurement_type = measurement_type.lower()
        self.enable_plot = enable_plot
        self.multimeter = None
        self.csv_file = None
        self.csv_writer = None
        self.max_samples = None
        self.animation = None
        
        # Data storage
        self.timestamps = deque(maxlen=max_points)
        self.measurements = deque(maxlen=max_points)
        self.start_time = None
        self.measurement_count = 0
        
        # Plot setup (only if plotting is enabled)
        if self.enable_plot:
            self.fig, self.ax = plt.subplots(figsize=(10, 6))
            self.line, = self.ax.plot([], [], 'b-', linewidth=2)
            self.ax.set_xlabel('Time (seconds)', fontsize=12)
            
            # Set appropriate Y-axis label based on measurement type
            ylabel_map = {
                'voltage': 'Voltage (V)',
                'current': 'Current (A)',
                'resistance': 'Resistance (Ω)',
                'temperature': 'Temperature (°C)'
            }
            self.ax.set_ylabel(ylabel_map.get(self.measurement_type, 'Measurement Value'), fontsize=12)
            
            title = f'DMM6500 Real-Time {self.measurement_type.capitalize()} Measurements'
            self.ax.set_title(title, fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3)
        else:
            self.fig = None
            self.ax = None
            self.line = None
        
    def connect(self):
        """Connect to the DMM6500 multimeter."""
        print("Connecting to DMM6500 multimeter...")
        try:
            self.multimeter = DMM6500()
            print(f"Successfully connected to DMM6500")
            return True
        except Exception as e:
            print(f"Error connecting to DMM6500: {e}")
            return False
    
    def open_csv_file(self):
        """Open CSV file with date-formatted filename."""
        # Create filename with format: yyyy-mm-dd_dmm6500_<measurement-type>_measurements.csv
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}_dmm6500_{self.measurement_type}_measurements.csv"
        
        try:
            self.csv_file = open(filename, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            # Write header
            self.csv_writer.writerow(['Timestamp', 'Elapsed_Time_s', 'Measurement'])
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
            if self.measurement_type == 'voltage':
                measurement = self.multimeter.measure_voltage()
            elif self.measurement_type == 'current':
                measurement = self.multimeter.measure_current()
            elif self.measurement_type == 'resistance':
                measurement = self.multimeter.measure_resistance()
            elif self.measurement_type == 'temperature':
                measurement = self.multimeter.measure_temperature()
            else:
                print(f"Unknown measurement type: {self.measurement_type}")
                return None
            return measurement
        except Exception as e:
            print(f"Error getting measurement: {e}")
            return None
    
    def update_plot(self, frame):
        """Update function for animation - called periodically."""
        # Check if we've reached the sample limit
        if self.max_samples is not None and self.measurement_count >= self.max_samples:
            print(f"\nReached maximum sample count: {self.max_samples}")
            self.cleanup()
            if self.enable_plot:
                plt.close(self.fig)
                return (self.line,)
            return None
        
        # Get measurement
        measurement = self.get_measurement()
        
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
                                         f"{measurement:.6f}"])
                self.csv_file.flush()  # Ensure data is written immediately
            
            # Update plot (only if plotting is enabled)
            if self.enable_plot:
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
                title = f'DMM6500 Real-Time {self.measurement_type.capitalize()} Measurements (Count: {self.measurement_count}, Current: {measurement:.6f})'
                self.ax.set_title(title, fontsize=14, fontweight='bold')
            
            # Print to console
            print(f"[{self.measurement_count}] Time: {elapsed:.2f}s, {self.measurement_type.capitalize()}: {measurement:.6f}")
        
        if self.enable_plot:
            return (self.line,)
        return None
    
    def start_logging(self, max_samples=None):
        """
        Start continuous logging with or without real-time plot.
        
        Args:
            max_samples (int): Maximum number of samples to collect, or None for continuous
        """
        if not self.connect():
            return
        
        filename = self.open_csv_file()
        if not filename:
            return
        
        self.max_samples = max_samples
        
        print(f"\nStarting measurement logging...")
        print(f"Measurement type: {self.measurement_type}")
        print(f"Update interval: {self.interval} seconds")
        print(f"Live plot: {'enabled' if self.enable_plot else 'disabled'}")
        if max_samples:
            print(f"Will collect {max_samples} samples")
        else:
            print("Continuous mode - Press Ctrl+C to stop")
        print("\n" + "="*60)
        
        try:
            if self.enable_plot:
                # Create animation for live plotting
                # Convert interval from seconds to milliseconds
                self.animation = animation.FuncAnimation(
                    self.fig, 
                    self.update_plot,
                    interval=int(self.interval * 1000),
                    blit=True,
                    cache_frame_data=False
                )
                
                plt.tight_layout()
                plt.show()
            else:
                # No plotting - just collect data in a loop
                while True:
                    if self.max_samples is not None and self.measurement_count >= self.max_samples:
                        print(f"\nReached maximum sample count: {self.max_samples}")
                        break
                    
                    # Get measurement
                    measurement = self.get_measurement()
                    
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
                                                     f"{measurement:.6f}"])
                            self.csv_file.flush()  # Ensure data is written immediately
                        
                        # Print to console
                        print(f"[{self.measurement_count}] Time: {elapsed:.2f}s, {self.measurement_type.capitalize()}: {measurement:.6f}")
                    
                    # Wait for next measurement
                    time.sleep(self.interval)
            
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
            except Exception as e:
                print(f"Warning: Error disconnecting multimeter: {e}")
        
        print(f"Total measurements collected: {self.measurement_count}")
        print("Done.")


def main():
    """Main function to parse arguments and start logging."""
    parser = argparse.ArgumentParser(
        description='Retrieve measurements from DMM6500 multimeter with CSV logging',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python measure_dmm6500.py                           # Temperature, continuous mode (no plot)
  python measure_dmm6500.py --live-plot               # Temperature with live plot
  python measure_dmm6500.py --measurement voltage     # Voltage measurement
  python measure_dmm6500.py --samples 100             # Collect 100 samples
  python measure_dmm6500.py --interval 1.0            # 1 second between samples
  python measure_dmm6500.py --measurement resistance  # Resistance measurement
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
    
    parser.add_argument(
        '--measurement',
        type=str,
        default='temperature',
        choices=['voltage', 'current', 'resistance', 'temperature'],
        help='Type of measurement to perform (default: temperature)'
    )
    
    parser.add_argument(
        '--live-plot',
        action='store_true',
        help='Enable live plotting (default: disabled)'
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
    logger = DMM6500DataLogger(
        max_points=args.max_points, 
        interval=args.interval,
        measurement_type=args.measurement,
        enable_plot=args.live_plot
    )
    logger.start_logging(max_samples=args.samples)


if __name__ == "__main__":
    main()
