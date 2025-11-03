
import json
from PyQt5.QtWidgets import QToolButton, QMenu, QAction, QFileDialog, QMessageBox
from PyQt5.QtCore import QSize, Qt, QThread, QTimer, QSettings
import os

from styles import MENU_STYLES



"""
Presets will take the form of JSON files so that users can easily read and modify them
the JSON file preset will modify the two RGC connectivities but not any other elements
these other elements will be reset when a preset is implemented
- either set all LEDs to on or to a specific pattern based on the preset 
- modify the graphing settings as well ? 
"""

def _check_custom_presets():
    """Ensure the custom presets directory exists and contains the default preset files."""
    if os.path.exists('custom_presets'):
        pass
    else:
        # create the directory if it does not exist
        os.makedirs('custom_presets')
    return 0

class PresetOpenButton(QToolButton):
    """Separate Open button for presets"""
    def __init__(self, data_manager):
        super().__init__()
        _check_custom_presets()
        self.data_manager = data_manager
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setMinimumWidth(60)
        self.setText("Open")
        
        # Connect button click directly to file dialog
        self.clicked.connect(self.open_preset_file_dialog)

        # Still track recent files for potential future use
        self.settings = QSettings("RetINaBOX", "Presets")
        self.max_recent_files = 3

    def add_recent_file(self, file_path):
        """Add a file to the recent files list"""
        recent_files = self.settings.value("recent_files", [])
        
        # Remove if already exists (to move to top)
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning of list
        recent_files.insert(0, file_path)
        
        # Limit to max number of files
        recent_files = recent_files[:self.max_recent_files]
        
        # Save back to settings
        self.settings.setValue("recent_files", recent_files)

    def open_preset_file_dialog(self):
        # Allow user to choose a file 
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Preset Configuration",
            "custom_presets",  # Default directory
            "JSON Files (*.json)"
        )
        
        if file_path:
            self.load_custom_preset(file_path)

    def load_custom_preset(self, file_path):
        if not file_path:
            return 
        try:
            with open(file_path, 'r') as f:
                connectivity_data = json.load(f)
            
            # Update data_manager with loaded data
            self.data_manager.neuron_connectivity_data = connectivity_data
            self.data_manager.neuron_connectivity_updated.emit()
            
            print(f"Loaded preset from: {file_path}")
            
            # Add to recent files
            self.add_recent_file(file_path)
            
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            QMessageBox.critical(self, "Error", f"File not found:\n{file_path}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON format: {e}")
            QMessageBox.critical(self, "Error", f"Invalid JSON format:\n{str(e)}")
        except Exception as e:
            print(f"Error loading preset: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load preset:\n{str(e)}")

class PresetSaveButton(QToolButton):
    """Separate Save button for presets"""
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setMinimumWidth(60)
        self.setText("Save")
        self.clicked.connect(self.save_current_configuration)

    def save_current_configuration(self):
        connectivity_data = self.data_manager.neuron_connectivity_data 
        # Open file dialog to let user choose save location
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Preset Configuration", 
            "",  # Default directory
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Ensure the file has .json extension
                if not file_path.endswith('.json'):
                    file_path += '.json'
                
                # Save dictionary to JSON file
                with open(file_path, 'w') as f:
                    json.dump(connectivity_data, f, indent=4)
                                
                QMessageBox.information(self, "Success", f"Preset saved successfully to:\n{file_path}")
                
            except Exception as e:
                print(f"Error saving preset: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save preset:\n{str(e)}")
        return 0