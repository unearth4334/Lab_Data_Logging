#!/usr/bin/env python3
"""
Demo screenshot generator for DMM6500 resistance plotter.
Creates a sample plot showing the functionality.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime

# Add the current directory to the path
sys.path.append('.')

def create_demo_plot():
    """Create a demo plot showing the DMM6500 resistance plotter functionality."""
    
    # Generate sample data
    np.random.seed(42)  # For reproducible results
    time_points = np.linspace(0, 30, 100)  # 30 seconds of data
    
    # Simulate resistance measurements with drift and noise
    base_resistance = 1000.0
    drift = 3.0 * np.sin(0.2 * time_points) + 1.5 * np.cos(0.1 * time_points)
    noise = np.random.normal(0, 0.3, len(time_points))
    resistance_values = base_resistance + drift + noise
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot the full data
    line = ax.plot(time_points, resistance_values, 'b-', linewidth=2, label='Resistance Measurements')
    
    # Highlight the latest 10 points (simulate the box feature)
    latest_times = time_points[-10:]
    latest_resistances = resistance_values[-10:]
    
    # Calculate slope for the latest 10 points
    n = len(latest_times)
    sum_x = np.sum(latest_times)
    sum_y = np.sum(latest_resistances)
    sum_xy = np.sum(latest_times * latest_resistances)
    sum_x2 = np.sum(latest_times * latest_times)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    
    # Calculate box boundaries
    x_min, x_max = min(latest_times), max(latest_times)
    y_min, y_max = min(latest_resistances), max(latest_resistances)
    
    x_padding = (x_max - x_min) * 0.02
    y_padding = (y_max - y_min) * 0.02
    
    # Choose box color based on slope threshold (0.01 Ω/s)
    slope_threshold = 0.01
    if abs(slope) < slope_threshold:
        box_color = 'green'
        status = 'STABLE'
    else:
        box_color = 'red'
        status = 'CHANGING'
    
    # Create and add the box
    box_width = x_max - x_min + 2 * x_padding
    box_height = y_max - y_min + 2 * y_padding
    
    box_patch = patches.Rectangle(
        (x_min - x_padding, y_min - y_padding),
        box_width, box_height,
        linewidth=3, edgecolor=box_color, facecolor='none',
        alpha=0.8, linestyle='-'
    )
    ax.add_patch(box_patch)
    
    # Add slope information text
    r_squared = 0.95  # Simulated R-squared value
    slope_text_str = f'Slope: {slope:.6f} Ω/s\nStatus: {status}\nR²: {r_squared:.4f}'
    
    # Position text in upper right corner
    slope_text = ax.text(
        0.98, 0.98, slope_text_str,
        transform=ax.transAxes,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor=box_color, alpha=0.3),
        fontsize=12
    )
    
    # Customize the plot
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Resistance (Ohms)', fontsize=12)
    ax.set_title('DMM6500 Real-time Resistance Measurements - Demo', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)
    
    # Add some annotations
    ax.annotate('Latest 10 measurements\n(slope analysis)', 
                xy=(x_max, y_max), xytext=(x_max - 5, y_max + 1.5),
                arrowprops=dict(arrowstyle='->', color=box_color, lw=2),
                fontsize=10, ha='center',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Add feature callouts
    ax.text(0.02, 0.98, 'Features:\n• Real-time plotting\n• Autoscaling\n• Slope analysis\n• Color-coded status', 
            transform=ax.transAxes, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
            fontsize=10)
    
    plt.tight_layout()
    
    # Save the plot
    filename = 'dmm6500_plotter_demo.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Demo plot saved as: {filename}")
    
    return filename

if __name__ == "__main__":
    create_demo_plot()