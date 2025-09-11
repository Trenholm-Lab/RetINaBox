Welcome to RetINaBox! 

### Step 1: Download a ZIP of the repository

### Step 2: Navigate into the un-zipped directory (in terminal)
cd RetINaBox

### Step 3: Make the installer script executable (in terminal)
chmod +x install_RetINaBox.py

### Step 4: Run the installer script (in terminal)
python3 install_RetINaBox.py

This will:
- Install system dependencies
- Create a virtual environment with Raspberry Pi system packages
- Install Python requirements
- Set up GPIO services
- Create a desktop shortcut with the RetINaBox logo

After installation, you can launch RetINaBox by:
- Double-clicking the desktop shortcut, OR
- Running manually: `./venv/bin/python GUI/main.py`