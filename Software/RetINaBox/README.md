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
sudo apt install -y python3-numpy python3-pyqt5 python3-pyqt5.qtsvg python3-pyqtgraph python3-rpi.gpio python3-lgpio
```

**Note**: 
- The `python3-pyqt5.qtsvg` package is essential for displaying SVG graphics in RetINaBox.
- Both `python3-rpi.gpio` (Pi 1-4) and `python3-lgpio` (Pi 5) are installed for maximum compatibility.

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

**Issue 4: Images/logos not displaying (FileNotFoundError)**
If you get errors about missing .svg or .png files, make sure you're running from the correct directory:
```bash
# Make sure you're in the RetINaBox project root
cd /path/to/RetINaBox  # Replace with your actual path
python3 GUI/main.py
```

This ensures all image and resource files are found with the correct relative paths.

**Issue 5: GPIO errors on Raspberry Pi 5 ("Cannot determine SOC peripheral base address")**
Raspberry Pi 5 uses different GPIO hardware that requires the lgpio library instead of RPi.GPIO:
```bash
sudo apt install -y python3-lgpio
```

### Running with System Python

After manual installation, you can run RetINaBox directly with the system Python (no virtual environment needed):

```bash
cd RetINaBox
python3 GUI/main.py
```

**Important**: Always run from the project root directory (`RetINaBox`) to ensure proper file paths for images and resources.