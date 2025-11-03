#!/usr/bin/env python3
"""
RetINaBox Development Setup Installer

This script sets up a development environment for RetINaBox on Raspberry Pi.

Modes:
- Raspberry Pi 400: APT-ONLY mode (no pip, no venv). Installs all deps via apt, runs with system Python.
- Raspberry Pi 500/others: Your original flow (venv inheriting system packages + pip -r requirements.txt).

Rationale:
- Pi 400 often runs 32-bit and hits BLAS soname + pip/locale snags. APT-only mode guarantees compatibility.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import re
import time

# ----------------------------- Utils -----------------------------------------

def print_header(text):
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")

def run_command(command, description=None, exit_on_error=False):
    if description:
        print(f"{description}...")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        if description:
            print(f"ERROR during '{description}':")
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        if exit_on_error:
            print("Installation failed. Exiting.")
            sys.exit(1)
        return False
    return True

def venv_python(venv_dir): return str(Path(venv_dir)/"bin"/"python")
def venv_pip(venv_dir):    return str(Path(venv_dir)/"bin"/"pip")

def create_venv(venv_dir, inherit=False, desc=None, upgrade_pip=True):
    """Create venv; optionally skip pip upgrade."""
    if Path(venv_dir).exists():
        shutil.rmtree(venv_dir)
    flag = "--system-site-packages" if inherit else ""
    run_command(f"python3 -m venv {flag} {venv_dir}",
                desc or f"Creating {'inheriting' if inherit else 'isolated'} virtual environment",
                exit_on_error=True)
    if upgrade_pip:
        run_command(f"{venv_pip(venv_dir)} install --upgrade pip", "Upgrading pip", exit_on_error=True)

# ------------------------- Pi model detection --------------------------------

def detect_pi_model():
    """
    Returns: 'pi400', 'pi500', or 'other'
    Based on /proc/device-tree/model; tolerant to minor wording differences.
    """
    model_text = ""
    try:
        with open("/proc/device-tree/model", "r") as f:
            model_text = f.read().strip()
    except FileNotFoundError:
        return "other"

    mt = model_text.lower()
    if "raspberry pi 400" in mt:
        return "pi400"
    if "raspberry pi 500" in mt or "raspberry pi 5" in mt:
        return "pi500"
    return "other"

def check_raspberry_pi_or_exit():
    if not sys.platform.startswith("linux"):
        print("This installer must be run on a Raspberry Pi.")
        sys.exit(1)
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().strip()
        if "Raspberry Pi" not in model:
            print(f"WARNING: This doesn't appear to be a Raspberry Pi ({model}).")
            resp = input("Continue anyway? (y/n): ")
            if resp.lower() != "y":
                sys.exit(1)
        else:
            print(f"Detected: {model}")
    except FileNotFoundError:
        print("WARNING: Cannot confirm this is a Raspberry Pi.")
        resp = input("Continue anyway? (y/n): ")
        if resp.lower() != "y":
            sys.exit(1)

# ----------------------- Requirements helpers --------------------------------

def filter_requirements_skip(req_path, skip_pkgs=("numpy",)):
    """
    Read requirements.txt and return two lists:
      keep: lines to install
      skipped: lines skipped (e.g., numpy)
    """
    keep, skipped = [], []
    if not os.path.exists(req_path):
        return keep, skipped
    with open(req_path, "r") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            base = re.split(r"[<>=!~\[]", raw, 1)[0].strip().lower()
            if base in {s.lower() for s in skip_pkgs}:
                skipped.append(raw)
            else:
                keep.append(raw)
    return keep, skipped

# --------------------------- Install stacks -----------------------------------

def install_dependencies_base():
    """Base deps common to both paths (safe)."""
    print_header("Installing Base Dependencies")
    run_command("sudo apt-get update", "Updating package lists", exit_on_error=True)
    packages = [
        "python3-pip", "python3-dev", "python3-venv"
    ]
    run_command(f"sudo apt-get install -y {' '.join(packages)}",
                "Installing base system dependencies", exit_on_error=True)

def install_pi400_system_stack():
    """
    APT-ONLY stack for Pi 400 (no pip, no venv):
    Installs the essential packages for RetINaBox compatibility.
    """
    print_header("Pi 400: Installing APT-only Python stack (no pip, no venv)")
    
    # Core packages needed for RetINaBox
    core_pkgs = [
        "python3-numpy", 
        "python3-pyqt5", 
        "python3-pyqt5.qtsvg",  # Essential for QSvgWidget
        "python3-pyqtgraph",    # Essential for graphing
        "python3-rpi.gpio"      # Essential for GPIO
    ]
    
    # Optional packages for additional features
    optional_pkgs = [
        "python3-scipy", 
        "python3-matplotlib", 
        "python3-pil"
    ]
    
    # Install core packages first (with error checking)
    run_command(f"sudo apt-get install -y {' '.join(core_pkgs)}",
                "Installing core RetINaBox packages", exit_on_error=True)
    
    # Install optional packages (without stopping on errors)
    run_command(f"sudo apt-get install -y {' '.join(optional_pkgs)}",
                "Installing optional packages", exit_on_error=False)

def setup_application():
    """Confirm the app entrypoint exists."""
    print_header("Setting up RetINaBox Application")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "GUI", "main.py")
    if not os.path.exists(main_file):
        print(f"ERROR: {main_file} not found!")
        sys.exit(1)
    print("Application setup complete - ready to run from source")

def create_desktop_shortcut(python_path, use_utf8=True):
    """Create a desktop launcher pointing at the chosen Python."""
    print_header("Creating Desktop Shortcut")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_file = os.path.join(script_dir, "GUI", "main.py")
    logo_path = os.path.join(script_dir, "GUI", "Graphics", "Logo_noText.png")

    launcher_script = os.path.join(script_dir, "launch_retina_box.sh")
    with open(launcher_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write(f"cd \"{script_dir}\"\n")
        if use_utf8:
            # Force UTF-8 at runtime to avoid any decode issues in logs, configs, etc.
            f.write("export LANG=C.UTF-8\nexport LC_ALL=C.UTF-8\n")
        f.write(f"\"{python_path}\" \"{main_file}\"\n")
    os.chmod(launcher_script, 0o755)
    print(f"Created launcher script: {launcher_script}")

    desktop_dir = os.path.expanduser("~/Desktop")
    os.makedirs(desktop_dir, exist_ok=True)

    icons_dir = os.path.expanduser("~/.local/share/icons")
    os.makedirs(icons_dir, exist_ok=True)
    icon_path = os.path.join(icons_dir, "retina_box_logo.png")
    if os.path.exists(logo_path):
        shutil.copy2(logo_path, icon_path)

    desktop_file_path = os.path.join(desktop_dir, "RetINaBox.desktop")
    with open(desktop_file_path, "w") as f:
        f.write(f"""[Desktop Entry]
Name=RetINaBox
Exec={launcher_script}
Icon={icon_path}
Type=Application
Terminal=false
Comment=RetINaBox Application
Categories=Utility;Science;
Path={script_dir}
""")
    os.chmod(desktop_file_path, 0o755)
    print(f"Desktop shortcut created at: {desktop_file_path}")
    print("The shortcut will run RetINaBox from source")

# ------------------------------- Main -----------------------------------------

def main():
    print_header("RetINaBox Desktop App Installer")
    check_raspberry_pi_or_exit()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, "venv")
    requirements_path = os.path.join(script_dir, "requirements.txt")

    model = detect_pi_model()
    print(f"Model classification: {model}")

    # Always install base build/runtime deps
    install_dependencies_base()

    if model == "pi400":
        # APT-ONLY mode — no venv, no pip
        install_pi400_system_stack()
        setup_application()

        # Launcher uses system Python (no venv)
        system_python = shutil.which("python3") or "/usr/bin/python3"
        create_desktop_shortcut(system_python, use_utf8=True)

    else:
        # Pi 500 / other: install core system packages first, then use venv + pip
        print_header("Pi 500/Other: Installing core system packages + virtualenv")
        
        # Install the same core packages as Pi 400 to ensure consistency
        core_pkgs = [
            "python3-numpy", 
            "python3-pyqt5", 
            "python3-pyqt5.qtsvg",  # Essential for QSvgWidget
            "python3-pyqtgraph",    # Essential for graphing
            "python3-rpi.gpio"      # Essential for GPIO
        ]
        run_command(f"sudo apt-get install -y {' '.join(core_pkgs)}",
                    "Installing core RetINaBox system packages", exit_on_error=True)
        
        # Create inheriting venv and pip -r
        create_venv(venv_dir, inherit=True,
                    desc="Creating virtual environment with system packages",
                    upgrade_pip=True)

        if os.path.exists(requirements_path):
            run_command(f"{venv_pip(venv_dir)} install -r '{requirements_path}'",
                        "Installing additional Python requirements", exit_on_error=True)

        setup_application()

        # Launcher uses venv’s Python
        create_desktop_shortcut(venv_python(venv_dir), use_utf8=True)

    print_header("Installation Complete!")
    print("RetINaBox is ready. Use the desktop shortcut to launch.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInstallation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
