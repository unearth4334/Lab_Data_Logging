#!/usr/bin/env python3
"""
Simple test to check if Plotly plots are rendering correctly
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.offline as pyo

# Create simple test data
import numpy as np
t = np.linspace(0, 1, 1000)
y = np.sin(2 * np.pi * 5 * t)  # 5 Hz sine wave

# Create figure
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=t,
    y=y,
    mode='lines',
    name='Test Sine Wave',
    line=dict(color='#1f77b4', width=2)
))

fig.update_layout(
    title="Test Plot - Sine Wave",
    xaxis_title="Time (s)",
    yaxis_title="Amplitude",
    template='plotly_white',
    height=400
)

# Generate HTML
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Plot Test</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Plot Test</h1>
    {pyo.plot(fig, output_type='div', include_plotlyjs=False)}
</body>
</html>
"""

with open('plot_test.html', 'w') as f:
    f.write(html_content)

print("Created plot_test.html - check if this simple plot works")