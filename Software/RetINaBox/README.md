Welcome to RetINaBox! 

### Step 1: Download a ZIP of the repository

### Step 2: Navigate into the un-zipped directory (in terminal)
```bash
cd RetINaBox
```

### Step 3: Make the installer script executable (in terminal)
```bash
chmod +x install_RetINaBox.py
```

### Step 4: Run the installer script (in terminal)
```bash
python3 install_RetINaBox.py
```

This will:
- Install system dependencies
- Create a virtual environment with Raspberry Pi system packages
- Install Python requirements
- Set up GPIO services
- Create a desktop shortcut with the RetINaBox logo

After installation, you can launch RetINaBox by:
- Double-clicking the desktop shortcut, OR
- Running manually: pi500: `./venv/bin/python GUI/main.py`, pi400: `python3 GUI/main.py`

## Troubleshooting: Manual Installation

If you're having issues with the automatic installer, you can manually install the required packages using the system package manager and run RetINaBox with the Raspberry Pi's built-in Python.

### Manual Package Installation

First, update your package lists:
```bash
sudo apt update
```

```bash
sudo apt install -y python3-numpy python3-pyqt5 python3-pyqt5.qtsvg python3-pyqtgraph python3-rpi.gpio
```

**Note**: The `python3-pyqt5.qtsvg` package is essential for displaying SVG graphics in RetINaBox.

### Common Installation Issues

**Issue 1: PyQtGraph not found**
If you get errors about pyqtgraph not being available, try installing it explicitly:
```bash
sudo apt install -y python3-pyqtgraph
```

**Issue 2: SVG graphics not displaying (PyQt5.QtSvg errors)**
If you see errors related to QSvgWidget or SVG files not displaying:
```bash
sudo apt install -y python3-pyqt5.qtsvg
```

**Issue 3: Package not found on your Pi model**
Some packages may have different names on different Raspberry Pi OS versions:
```bash
# Try alternative package names if the above fail:
sudo apt install -y python3-pyqt5-dev python3-pyqt5.qtsvg-dev
```

### Running with System Python

After manual installation, you can run RetINaBox directly with the system Python (no virtual environment needed):

```bash
cd RetINaBox
python3 GUI/main.py
```

### Verify Installation

To check if all required packages are properly installed, run this test:
```bash
python3 -c "
import numpy as np
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSvg import QSvgWidget
import pyqtgraph as pg
try:
    import RPi.GPIO as GPIO
    print('✓ All packages installed successfully!')
except ImportError:
    print('✓ All GUI packages installed (GPIO will work on Raspberry Pi)')
"
```

If you see any import errors, install the missing packages using the commands above.

This approach uses only the system's Python packages and avoids potential compatibility issues with pip installations on older Raspberry Pi models.