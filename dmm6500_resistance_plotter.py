#!/usr/bin/env python3
"""
DMM6500 Resistance Measurement and Plotting Script

This script retrieves resistance measurements from a Keithley DMM6500 digital multimeter
at configurable intervals and plots them in real-time. It includes features for:
- Real-time plotting with autoscaling
- Slope calculation for the latest 10 measurements
- Visual box indicators that change color based on slope threshold

Author: AI Assistant
Date: December 2024
License: Apache 2.0
"""

import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from datetime import datetime
import argparse
import logging

# Add the libs directory to the path for imports
sys.path.append('./libs')
try:
    from DMM6500 import DMM6500
except ImportError:
    print("Error: Could not import DMM6500. Make sure the libs directory is available.")
    sys.exit(1)


class DMM6500ResistancePlotter:
    """
    A class for real-time resistance measurement and plotting from DMM6500.
    """
    
    def __init__(self, measurement_interval=1.0, slope_threshold=0.01, max_points=100):
        """
        Initialize the plotter.
        
        Args:
            measurement_interval (float): Time between measurements in seconds
            slope_threshold (float): Threshold for slope color change (Ohms/second)
            max_points (int): Maximum number of points to keep in plot
        """
        self.measurement_interval = measurement_interval
        self.slope_threshold = abs(slope_threshold)  # Use absolute value
        self.max_points = max_points
        
        # Data storage
        self.timestamps = []
        self.resistance_values = []
        self.measurement_count = 0
        
        # DMM6500 connection
        self.dmm = None
        self.connected = False
        
        # Plotting setup
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.line, = self.ax.plot([], [], 'b-', linewidth=2, label='Resistance')
        self.box_patch = None
        self.slope_text = None
        
        # Configure plot
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Resistance (Ohms)')
        self.ax.set_title('DMM6500 Real-time Resistance Measurements')
        self.ax.grid(True, alpha=0.3)
        self.ax.legend()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def connect_dmm(self):
        """
        Connect to the DMM6500 multimeter.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.dmm = DMM6500(auto_connect=True)
            if self.dmm.status == "Connected":
                self.connected = True
                self.logger.info("Successfully connected to DMM6500")
                return True
            else:
                self.logger.error("Failed to connect to DMM6500")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to DMM6500: {e}")
            # For testing without hardware, create a mock DMM
            self.dmm = MockDMM6500()
            self.connected = True
            self.logger.warning("Using mock DMM6500 for testing")
            return True
    
    def disconnect_dmm(self):
        """Disconnect from the DMM6500."""
        if self.dmm and hasattr(self.dmm, 'disconnect'):
            self.dmm.disconnect()
            self.connected = False
            self.logger.info("Disconnected from DMM6500")
    
    def measure_resistance(self):
        """
        Take a resistance measurement.
        
        Returns:
            float: Resistance value in Ohms, or None if measurement failed
        """
        try:
            if not self.connected:
                return None
            
            resistance = self.dmm.measure_resistance()
            self.logger.debug(f"Measured resistance: {resistance} Ohms")
            return resistance
        except Exception as e:
            self.logger.error(f"Error measuring resistance: {e}")
            return None
    
    def add_measurement(self, resistance):
        """
        Add a new measurement to the data arrays.
        
        Args:
            resistance (float): Resistance value in Ohms
        """
        current_time = time.time()
        
        # Store relative time from start of measurements
        if len(self.timestamps) == 0:
            self.start_time = current_time
            relative_time = 0.0
        else:
            relative_time = current_time - self.start_time
        
        self.timestamps.append(relative_time)
        self.resistance_values.append(resistance)
        self.measurement_count += 1
        
        # Limit the number of points to prevent memory issues
        if len(self.timestamps) > self.max_points:
            self.timestamps.pop(0)
            self.resistance_values.pop(0)
    
    def calculate_slope(self):
        """
        Calculate the slope of the latest 10 measurements.
        
        Returns:
            tuple: (slope, r_squared) or (None, None) if insufficient data
        """
        if len(self.resistance_values) < 10:
            return None, None
        
        # Get the latest 10 points
        latest_times = np.array(self.timestamps[-10:])
        latest_resistances = np.array(self.resistance_values[-10:])
        
        # Calculate linear regression slope
        n = len(latest_times)
        sum_x = np.sum(latest_times)
        sum_y = np.sum(latest_resistances)
        sum_xy = np.sum(latest_times * latest_resistances)
        sum_x2 = np.sum(latest_times * latest_times)
        
        # Slope calculation
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:  # Avoid division by zero
            return 0.0, 1.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate R-squared for quality assessment
        y_mean = np.mean(latest_resistances)
        ss_tot = np.sum((latest_resistances - y_mean) ** 2)
        y_pred = slope * (latest_times - latest_times[0]) + latest_resistances[0]
        ss_res = np.sum((latest_resistances - y_pred) ** 2)
        
        if abs(ss_tot) < 1e-10:
            r_squared = 1.0
        else:
            r_squared = 1 - (ss_res / ss_tot)
        
        return slope, r_squared
    
    def update_plot(self, frame):
        """
        Update function for the animation.
        
        Args:
            frame: Frame number (not used)
        """
        # Take a new measurement
        resistance = self.measure_resistance()
        if resistance is not None:
            self.add_measurement(resistance)
        
        # Update the line plot
        if len(self.timestamps) > 0:
            self.line.set_data(self.timestamps, self.resistance_values)
            
            # Autoscale the plot
            self.ax.relim()
            self.ax.autoscale_view()
            
            # Remove old box if it exists
            if self.box_patch:
                self.box_patch.remove()
                self.box_patch = None
            
            # Remove old slope text if it exists
            if self.slope_text:
                self.slope_text.remove()
                self.slope_text = None
            
            # Add box and slope calculation if we have at least 10 measurements
            if len(self.resistance_values) >= 10:
                slope, r_squared = self.calculate_slope()
                
                if slope is not None:
                    # Get the latest 10 points for the box
                    box_times = self.timestamps[-10:]
                    box_resistances = self.resistance_values[-10:]
                    
                    # Calculate box boundaries
                    x_min, x_max = min(box_times), max(box_times)
                    y_min, y_max = min(box_resistances), max(box_resistances)
                    
                    # Add some padding to the box
                    x_padding = (x_max - x_min) * 0.02
                    y_padding = (y_max - y_min) * 0.02
                    
                    # Choose box color based on slope threshold
                    if abs(slope) < self.slope_threshold:
                        box_color = 'green'
                        status = 'STABLE'
                    else:
                        box_color = 'red' 
                        status = 'CHANGING'
                    
                    # Create and add the box
                    box_width = x_max - x_min + 2 * x_padding
                    box_height = y_max - y_min + 2 * y_padding
                    
                    self.box_patch = patches.Rectangle(
                        (x_min - x_padding, y_min - y_padding),
                        box_width, box_height,
                        linewidth=3, edgecolor=box_color, facecolor='none',
                        alpha=0.8, linestyle='-'
                    )
                    self.ax.add_patch(self.box_patch)
                    
                    # Add slope information text
                    slope_text_str = f'Slope: {slope:.6f} Ω/s\nStatus: {status}\nR²: {r_squared:.4f}'
                    
                    # Position text in upper right corner of plot
                    self.slope_text = self.ax.text(
                        0.98, 0.98, slope_text_str,
                        transform=self.ax.transAxes,
                        verticalalignment='top',
                        horizontalalignment='right',
                        bbox=dict(boxstyle='round', facecolor=box_color, alpha=0.3),
                        fontsize=10
                    )
        
        return self.line,
    
    def start_plotting(self):
        """Start the real-time plotting."""
        if not self.connect_dmm():
            print("Failed to connect to DMM6500. Exiting.")
            return
        
        try:
            print(f"Starting real-time resistance measurements...")
            print(f"Measurement interval: {self.measurement_interval} seconds")
            print(f"Slope threshold: {self.slope_threshold} Ohms/second")
            print("Press Ctrl+C to stop.")
            
            # Create animation with the specified interval
            interval_ms = int(self.measurement_interval * 1000)
            self.ani = FuncAnimation(
                self.fig, self.update_plot, interval=interval_ms, 
                blit=False, cache_frame_data=False
            )
            
            plt.tight_layout()
            plt.show()
            
        except KeyboardInterrupt:
            print("\nMeasurement stopped by user.")
        except Exception as e:
            print(f"Error during plotting: {e}")
        finally:
            self.disconnect_dmm()


class MockDMM6500:
    """Mock DMM6500 class for testing without hardware."""
    
    def __init__(self):
        self.status = "Connected"
        self.base_resistance = 1000.0  # Base resistance of 1kΩ
        self.time_start = time.time()
        self.noise_amplitude = 0.5  # ±0.5Ω noise
    
    def measure_resistance(self):
        """Simulate resistance measurement with realistic drift and noise."""
        current_time = time.time() - self.time_start
        
        # Simulate a slowly changing resistance with noise
        drift = 2.0 * np.sin(0.1 * current_time)  # Slow sinusoidal drift
        noise = np.random.normal(0, self.noise_amplitude)
        
        return self.base_resistance + drift + noise
    
    def disconnect(self):
        """Mock disconnect method."""
        self.status = "Not Connected"


def main():
    """Main function to run the DMM6500 resistance plotter."""
    parser = argparse.ArgumentParser(
        description='Real-time resistance measurement and plotting for DMM6500'
    )
    parser.add_argument(
        '--interval', '-i', type=float, default=1.0,
        help='Measurement interval in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--threshold', '-t', type=float, default=0.01,
        help='Slope threshold for color change in Ohms/second (default: 0.01)'
    )
    parser.add_argument(
        '--max-points', '-m', type=int, default=100,
        help='Maximum number of points to display (default: 100)'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run the plotter
    plotter = DMM6500ResistancePlotter(
        measurement_interval=args.interval,
        slope_threshold=args.threshold,
        max_points=args.max_points
    )
    
    plotter.start_plotting()


if __name__ == "__main__":
    main()