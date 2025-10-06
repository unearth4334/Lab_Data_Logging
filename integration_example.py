#!/usr/bin/env python3
"""
Integration example showing how to use DMM6500 resistance measurements 
with the existing data_logger infrastructure alongside the standalone resistance_plotter.

This example demonstrates:
1. Using data_logger for structured logging to file
2. Using resistance_plotter for real-time visualization
3. Coordinating both approaches for comprehensive data acquisition

Usage:
    python3 integration_example.py [--demo] [--duration SECONDS]
"""

import sys
import time
import argparse
import threading
from datetime import datetime

# Import existing data_logger
from data_logger import data_logger

# Import our resistance plotter (for demo mode)
from resistance_plotter import ResistancePlotter


class IntegratedDMM6500Logger:
    """
    Integration example that combines structured logging with real-time plotting.
    """
    
    def __init__(self, demo_mode=False, duration=60):
        self.demo_mode = demo_mode
        self.duration = duration
        self.logger = None
        self.dmm = None
        self.plotter = None
        self.running = False
        
    def setup_data_logger(self):
        """Setup the data_logger for structured file output."""
        try:
            print("Setting up data logger...")
            self.logger = data_logger()
            
            # Create a timestamped filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"dmm6500_resistance_log_{timestamp}.txt"
            self.logger.new_file(filename)
            
            # Connect to DMM6500
            self.dmm = self.logger.connect("dmm6500")
            
            # Add resistance measurement to logger
            self.logger.add("Resistance", self.dmm, "resistance")
            # Add timestamp
            self.logger.add("Timestamp", time, "current")
            
            print(f"Data logger setup complete. Output file: {filename}")
            return True
            
        except Exception as e:
            print(f"Error setting up data logger: {e}")
            if self.demo_mode:
                print("Continuing in demo mode...")
                return True
            return False
    
    def setup_plotter(self):
        """Setup the resistance plotter for real-time visualization."""
        try:
            print("Setting up real-time plotter...")
            self.plotter = ResistancePlotter(
                interval=2.0,  # Take measurements every 2 seconds
                max_points=50,  # Show last 50 points
                demo_mode=self.demo_mode,
                no_gui=True  # Use text mode for this example
            )
            return True
            
        except Exception as e:
            print(f"Error setting up plotter: {e}")
            return False
    
    def data_logging_thread(self):
        """Thread for structured data logging."""
        print("Starting data logging thread...")
        start_time = time.time()
        measurement_count = 0
        
        while self.running and (time.time() - start_time) < self.duration:
            try:
                if not self.demo_mode and self.logger:
                    # Use data_logger for structured logging
                    self.logger.get_data(print_to_terminal=False)
                    measurement_count += 1
                    print(f"Data logged (measurement #{measurement_count})")
                else:
                    # Demo mode - just print a message
                    measurement_count += 1
                    print(f"Demo data logging (measurement #{measurement_count})")
                
                time.sleep(2.0)  # Log every 2 seconds
                
            except Exception as e:
                print(f"Error in data logging: {e}")
                time.sleep(2.0)
        
        print(f"Data logging completed. Total measurements: {measurement_count}")
    
    def plotting_thread(self):
        """Thread for real-time plotting visualization."""
        print("Starting plotting thread...")
        start_time = time.time()
        
        while self.running and (time.time() - start_time) < self.duration:
            try:
                # Simulate taking a measurement for plotting
                resistance = self.plotter.measure_resistance()
                current_time = time.time() - start_time
                
                # Store data in plotter
                self.plotter.timestamps.append(current_time)
                self.plotter.resistances.append(resistance)
                self.plotter.measurement_count += 1
                
                print(f"Plot data: {resistance:.2f} Ω (t={current_time:.1f}s)")
                
                # Update statistics display every 5 measurements
                if self.plotter.measurement_count % 5 == 0:
                    self.plotter.update_stats_display()
                
                time.sleep(1.5)  # Plot updates every 1.5 seconds
                
            except Exception as e:
                print(f"Error in plotting: {e}")
                time.sleep(1.5)
        
        print("Real-time plotting completed.")
    
    def run(self):
        """Run the integrated logging and plotting system."""
        print("DMM6500 Integrated Logger & Plotter")
        print("=" * 40)
        print(f"Demo mode: {'Yes' if self.demo_mode else 'No'}")
        print(f"Duration: {self.duration} seconds")
        print()
        
        # Setup components
        if not self.setup_data_logger():
            print("Failed to setup data logger")
            return False
        
        if not self.setup_plotter():
            print("Failed to setup plotter")
            return False
        
        print(f"Starting integrated measurement for {self.duration} seconds...")
        print("The system will log structured data to file while providing real-time visualization.")
        print("Press Ctrl+C to stop early.\n")
        
        # Start both threads
        self.running = True
        
        logging_thread = threading.Thread(target=self.data_logging_thread)
        plotting_thread = threading.Thread(target=self.plotting_thread)
        
        logging_thread.daemon = True
        plotting_thread.daemon = True
        
        try:
            logging_thread.start()
            plotting_thread.start()
            
            # Wait for completion
            time.sleep(self.duration)
            
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        
        finally:
            print("\nStopping integrated system...")
            self.running = False
            
            # Wait for threads to finish
            logging_thread.join(timeout=2)
            plotting_thread.join(timeout=2)
            
            # Cleanup
            if self.logger and not self.demo_mode:
                try:
                    self.logger.close_file()
                except Exception as e:
                    print(f"Error closing data logger: {e}")
            
            print("Integration example completed.")
        
        return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='DMM6500 Integration Example')
    parser.add_argument('--demo', action='store_true',
                       help='Run in demo mode without hardware')
    parser.add_argument('--duration', type=int, default=30,
                       help='Duration to run in seconds (default: 30)')
    
    args = parser.parse_args()
    
    if args.duration <= 0:
        print("Error: Duration must be positive")
        return 1
    
    # Create and run integrated logger
    integrated_logger = IntegratedDMM6500Logger(
        demo_mode=args.demo,
        duration=args.duration
    )
    
    success = integrated_logger.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())