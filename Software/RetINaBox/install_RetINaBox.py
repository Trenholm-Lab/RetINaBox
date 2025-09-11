#!/usr/bin/env python3
"""
RetINaBox Development Setup Installer

This script sets up a development environment for RetINaBox on Raspberry Pi.
It creates a virtual environment with system package inheritance and a desktop shortcut
that runs the application directly from source code.

Run this script after downloading the RetINaBox GitHub repository.

Requirements:
- Raspberry Pi running Raspberry Pi OS
- Internet connection for downloading dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import time


def print_header(text):
    """Print a header with formatting"""
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")

def run_command(command, description=None, exit_on_error=False):
    """Run a shell command and handle errors"""
    if description:
        print(f"{description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        if exit_on_error:
            print("Installation failed. Exiting.")
            sys.exit(1)
        return False
    return True

def check_raspberry_pi():
    """Check if we're running on a Raspberry Pi"""
    # Check for ARM architecture and Linux
    if not sys.platform.startswith("linux"):
        print("This installer must be run on a Raspberry Pi.")
        sys.exit(1)
    
    # Check for Raspberry Pi model
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read()
            if "Raspberry Pi" not in model:
                print(f"WARNING: This doesn't appear to be a Raspberry Pi ({model})." )
                response = input("Continue anyway? (y/n): ")
                if response.lower() != 'y':
                    sys.exit(1)
            else:
                print(f"Detected: {model}")
    except FileNotFoundError:
        print("WARNING: Cannot confirm this is a Raspberry Pi." )
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
            
    # Check if GPIO access is possible
    try:
        # Try to import RPi.GPIO as a test
        import importlib.util
        if importlib.util.find_spec("RPi.GPIO") is None:
            print("WARNING: RPi.GPIO module not found. Installing..." )
            run_command("sudo apt-get install -y python3-rpi.gpio", "Installing RPi.GPIO", exit_on_error=False)
    except Exception as e:
        print(f"WARNING: Could not verify GPIO access: {str(e)}" )

def install_dependencies():
    """Install required system and Python packages"""
    print_header("Installing Dependencies")
    
    # Update package lists
    run_command("sudo apt-get update", "Updating package lists", exit_on_error=True)
    
    # Install required system packages
    packages = [
        "python3-pip",
        "python3-dev",
        "python3-venv",
        # Core system libraries that may be needed
        "libatlas-base-dev",  # For numpy
        "libopenjp2-7-dev",   # For PIL
    ]
    
    run_command(f"sudo apt-get install -y {' '.join(packages)}", 
              "Installing system dependencies", 
              exit_on_error=True)
    
    # Create a virtual environment that inherits system packages for development
    print("Creating development environment..." )
    requirements_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    
    # Create a virtual environment that inherits system packages
    run_command("python3 -m venv --system-site-packages venv", "Creating virtual environment with system packages", exit_on_error=True)
    
    # Install only requirements.txt packages (system packages are inherited)
    run_command(f"./venv/bin/pip install -r {requirements_path}", 
              "Installing Python requirements", 
              exit_on_error=True)

def setup_application():
    """Setup the RetINaBox application for development"""
    print_header("Setting up RetINaBox Application")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "GUI", "main.py")
    
    # Verify main.py exists
    if not os.path.exists(main_file):
        print(f"ERROR: {main_file} not found!")
        sys.exit(1)
    
    print("Application setup complete - ready to run from source")

def create_desktop_shortcut():
    """Create a desktop shortcut for the application"""
    print_header("Creating Desktop Shortcut")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, "venv", "bin", "python")
    main_file = os.path.join(script_dir, "GUI", "main.py")
    logo_path = os.path.join(script_dir, "GUI", "Graphics", "Logo_noText.png")
    
    # Create a simple launcher script
    launcher_script = os.path.join(script_dir, "launch_retina_box.sh")
    with open(launcher_script, "w") as f:
        f.write(f"""#!/bin/bash
cd "{script_dir}"
"{venv_python}" "{main_file}"
""")
    
    # Make the launcher script executable
    os.chmod(launcher_script, 0o755)
    print(f"Created launcher script: {launcher_script}")
    
    # Create destination directories if they don't exist
    desktop_dir = os.path.expanduser("~/Desktop")
    os.makedirs(desktop_dir, exist_ok=True)
    
    # Copy the logo to a common location
    icons_dir = os.path.expanduser("~/.local/share/icons")
    os.makedirs(icons_dir, exist_ok=True)
    icon_path = os.path.join(icons_dir, "retina_box_logo.png")
    shutil.copy2(logo_path, icon_path)
    
    # Create the desktop file to run the launcher script
    desktop_file_path = os.path.join(desktop_dir, "RetINaBox.desktop")
    with open(desktop_file_path, "w") as f:
        f.write(f"""[Desktop Entry]
Name=RetINaBox
Exec={launcher_script}
Icon={icon_path}
Type=Application
Terminal=false
Comment=RetINaBox Application (Development Mode)
Categories=Utility;Science;
Path={script_dir}
""")
    
    # Make the desktop file executable
    os.chmod(desktop_file_path, 0o755)
    print(f"Desktop shortcut created at: {desktop_file_path}")
    print("The shortcut will run RetINaBox from source using the virtual environment")



def main():
    """Main installation function"""
    print_header("RetINaBox Desktop App Installer")
    
    # Check if running on Raspberry Pi
    check_raspberry_pi()
    
    # Install dependencies
    install_dependencies()
    
    # Setup application
    setup_application()
    
    # Enable and start pigpio service for GPIO access
    print_header("Setting up Raspberry Pi GPIO Services")
    run_command("sudo systemctl enable pigpiod", "Enabling pigpio daemon", exit_on_error=False)
    run_command("sudo systemctl start pigpiod", "Starting pigpio daemon", exit_on_error=False)
    print("GPIO services configured")
    
    # Create desktop shortcut
    create_desktop_shortcut()
    
    
    print_header("Installation Complete!")
    print("The RetINaBox application has been installed successfully!")
    print("You can now launch it from the desktop shortcut.")
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
