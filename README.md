# Curve Profile Editor

A Bezier curve profile editor for Maya with two modes of operation: traditional dialog and ephemeral overlay.

## Features

- **Dual Bezier curves**: Edit horizontal (red) and vertical (blue) cubic Bezier curves independently
- **Interactive editing**: Drag control points with left/right mouse buttons
- **Curve sampling**: Sample curves at any normalized time (0-1) for animation
- **Debug visualization**: Middle mouse button shows real-time curve sampling
- **Two operation modes**: Traditional dialog or ephemeral hotkey-activated overlay

## Installation

1. Place `curveProfileEditor.py` in your Maya scripts directory
2. Import and use in Maya's Script Editor or as part of your toolkit

## Usage

### Ephemeral Mode (Recommended for Workflow Integration)

The ephemeral mode creates a frameless, semi-transparent overlay that appears when you hold a hotkey and disappears when you release it. Perfect for quick curve adjustments without cluttering your workspace.

```python
import curveProfileEditor
from Qt import QtCore

# Activate ephemeral mode with Shift key
curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Shift)

# Now:
# - Hold Shift to show the curve editor
# - Click and drag to adjust the curve
# - Release Shift to hide the editor
```

**Using different hotkeys:**

```python
# Use Ctrl key
curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Control)

# Use Alt key
curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_Alt)

# Use a specific letter key (e.g., 'C')
curveProfileEditor.activate_ephemeral_mode(QtCore.Qt.Key_C)
```

**Deactivate when done:**

```python
curveProfileEditor.deactivate_ephemeral_mode()
```

**Access curve values even when hidden:**

```python
# Sample the curve
if curveProfileEditor._EPHEMERAL_UI:
    value = curveProfileEditor._EPHEMERAL_UI.sample_curve_normalized(0.5)
    print(f"Curve value at t=0.5: {value}")
```

### Traditional Dialog Mode

Creates a standard dialog window that stays visible until manually closed.

```python
import curveProfileEditor

# Open the curve editor
curveProfileEditor.main()

# Sample the curve
time = 0.5  # 50% through the animation
amount = curveProfileEditor._UI.sample_curve_normalized(time, use_lmb=True)
print(f"At time {time}, amount is {amount}")
```

## Mouse Controls

- **Left Mouse Button**: Edit horizontal curve (red)
- **Right Mouse Button**: Edit vertical curve (blue)
- **Middle Mouse Button** (DEBUG mode): Show sampling line and real-time values

## API Reference

### Sampling Functions

```python
# Sample curve at normalized time (0.0 to 1.0)
value = ui.sample_curve_normalized(time, use_lmb=True)

# Sample curve at specific pixel X coordinate
y_value = ui.sample_curve_at_x(x_pixel, use_lmb=True)

# Get control point values (for saving/loading)
curve_data = ui.get_curve_values(use_lmb=True)
# Returns: {'p0': (0.0, 0.0), 'p1': (x1, 0.0), 'p2': (x2, 1.0), 'p3': (1.0, 1.0)}
```

### Animation Example

```python
import maya.cmds as cmds
import curveProfileEditor

# Create the curve editor
curveProfileEditor.main()

# Apply curve to Maya animation
start_frame = 1
end_frame = 100
for frame in range(start_frame, end_frame + 1):
    time = (frame - start_frame) / float(end_frame - start_frame)
    value = curveProfileEditor._UI.sample_curve_normalized(time, use_lmb=True)
    cmds.setKeyframe('pSphere1.translateY', time=frame, value=value * 10)
```

## Configuration

### Debug Mode

Set `DEBUG = True` in the script to enable:
- Logging output
- Middle mouse button sampling visualization
- Hotkey press/release messages

### Window Size

The editor automatically adapts to different window sizes:
- **Traditional mode**: Fixed 400x400 pixels
- **Ephemeral mode**: Larger 600x600 pixels, centered on Maya window

## Requirements

- Maya 2017+ (Python 2.7 or 3.x)
- Qt.py (PySide2/PyQt5 compatibility layer)
- Maya OpenMayaUI module

## License

MIT License - Copyright (c) 2025 Daniel Klug

## Credits

Bezier curve mathematics based on work by Freya Holmer | Neat Corp
https://youtu.be/NzjF1pdlK7Y
