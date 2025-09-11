
from PyQt5.QtCore import QSize, Qt, QUrl, QTimer, QTime, QThread, QPointF, QRectF
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QDesktopServices, QPainter, QBrush, QColor, QPen  # Add this import
import pyqtgraph as pg
import numpy as np
from data_manager import *
from PyQt5.QtSvg import QSvgWidget
from graphing_manager import *
from presets_manager import * 
from styles import *
import os 
import json


class DiscoveryLegendCircle(QWidget):
    def __init__(self, circle_type="gray", parent=None):
        super().__init__(parent)
        self.circle_type = circle_type
        self.original_type = circle_type 
        self.is_grayed = False
        self.setFixedSize(20, 20)
    
    def set_grayed(self, grayed):
        """Set whether the circle should appear grayed out"""
        self.is_grayed = grayed
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define circle parameters
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 2  # Leave small margin
        
        # Choose color based on type and grayed state
        if self.is_grayed:
            # Use a light gray for all grayed circles
            color = QColor("#c0c0c0")
        else:
            if self.circle_type == "red":
                color = QColor("red")
            elif self.circle_type == "blue":
                color = QColor("blue")
            elif self.circle_type == "delay":
                color = QColor("transparent")
            else:  # gray
                color = QColor("gray")
        
        # Draw circle
        if self.circle_type == "delay":
            # Clear circle with gray outline
            if self.is_grayed:
                painter.setBrush(QBrush(Qt.transparent))
                painter.setPen(QPen(QColor("#d0d0d0"), 1))
            else:
                painter.setBrush(QBrush(Qt.transparent))
                painter.setPen(QPen(QColor(128, 128, 128), 1))
        else:
            # Solid colored circle
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
        
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Draw triangle for delay type
        if self.circle_type == "delay":
            if self.is_grayed:
                painter.setPen(QColor("#d0d0d0"))
            else:
                painter.setPen(QColor("black"))
            font = painter.font()
            font.setPointSizeF(radius * 1.5 )  # Size relative to circle radius
            painter.setFont(font)
            
            # Center triangle character
            triangle_char = "▲"
            rect = QRectF(center_x - radius, center_y - radius, 2*radius, 2*radius)
            painter.drawText(rect, Qt.AlignCenter, triangle_char)


class UserNeuronWidget(QWidget):
    """User version of NeuronWidget for connectivity configuration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(225, 200)
        self.is_grayed_out = False  # Add grayed out state
        
        # Initialize user's connectivity state (3x3 grid)
        self.user_connectivity = []
        for row in range(3):
            row_data = []
            for col in range(3):
                row_data.append({"state": "off", "delay": "None"})
            self.user_connectivity.append(row_data)
        
        # Circle positions matching NeuronWidget format
        self.circle_positions = [
            (37, 48),  # top left
            (152, 48),  # top center
            (266, 48),  # top right
            (88, 115),  # middle left
            (201, 115),  # middle center
            (317, 115),  # middle right
            (142, 184),  # bottom left
            (261, 184),  # bottom center
            (369, 184)   # bottom right
        ]

    def set_grayed_out(self, grayed):
        """Set whether the widget should appear grayed out"""
        self.is_grayed_out = grayed
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw RGC SVG background
        from PyQt5.QtSvg import QSvgRenderer
        renderer = QSvgRenderer(os.path.join("GUI","Graphics", "RGC_M.svg"))
        bounds = QRectF(self.rect())
        renderer.render(painter, bounds)

        # Draw the mini 3x3 grid of circles over the neuron
        viewBox = renderer.viewBoxF()
        painter.setWindow(viewBox.toRect())
        painter.setViewport(self.rect())
        cell_w = 35
        cell_h = 35

        # Draw each cell as a colored circle
        counter = 0
        for i in range(3):
            for j in range(3):
                cell_data = self.user_connectivity[i][j]
                state = cell_data["state"]
                delay = cell_data["delay"]

                # Choose color based on state and grayed out status
                if self.is_grayed_out:
                    # Use light gray for all circles when grayed out
                    color = QColor("#c0c0c0")
                else:
                    if state == "excitatory":
                        color = QColor("red")
                    elif state == "inhibitory":
                        color = QColor("blue")
                    else:
                        color = QColor("gray")

                x, y = self.circle_positions[counter]
                radius = min(cell_w, cell_h) / 2

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), radius, radius)

                # Draw delay triangle if applicable
                if delay != "None":
                    if self.is_grayed_out:
                        painter.setPen(QColor("#d0d0d0"))
                    else:
                        painter.setPen(QColor("black"))
                    font = painter.font()
                    font.setPointSizeF(radius * 0.8)
                    painter.setFont(font)
                    
                    triangle_char = "▲"
                    rect = QRectF(x - radius, y - radius, 2*radius, 2*radius)
                    painter.drawText(rect, Qt.AlignCenter, triangle_char)

                counter += 1
        
        # Reset coordinate system for overlay
        painter.resetTransform()
        
        # Draw grayed-out overlay if needed (after resetting coordinates)
        if self.is_grayed_out:
            painter.fillRect(self.rect(), QColor(240, 240, 240, 120))  # Semi-transparent gray overlay

    def mousePressEvent(self, event):
        # Don't allow interaction when grayed out
        if not self.is_grayed_out:
            self.show_popup_grid()

    def show_popup_grid(self):
        dialog = UserConnectivityDialog(self)
        dialog.exec_()
        self.update()  # Refresh the display
        
    def get_connectivity(self):
        """Get the current user connectivity state"""
        return self.user_connectivity
    
    def reset_connectivity(self):
        """Reset connectivity to default off state"""
        for row in range(3):
            for col in range(3):
                self.user_connectivity[row][col] = {"state": "off", "delay": "None"}
        self.update()

class UserConnectivityDialog(QDialog):
    """Dialog for editing user connectivity without affecting data_manager"""
    def __init__(self, connectivity_widget, parent=None):
        super().__init__(parent)
        self.connectivity_widget = connectivity_widget
        self.setWindowTitle("Configure RGC Connectivity")
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Configure RGC Connectivity"), alignment=Qt.AlignCenter)
        
        grid_layout = QGridLayout()
        self.cell_widgets = []
        
        for row in range(3):
            row_widgets = []
            for col in range(3):
                cell = UserConnectivityCell(connectivity_widget, row, col)
                row_widgets.append(cell)
                grid_layout.addWidget(cell, row, col)
            self.cell_widgets.append(row_widgets)

        layout.addLayout(grid_layout)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)


class UserConnectivityCell(QWidget):
    """Individual cell for user connectivity editing - matches original ConnectivityUnit styling"""
    def __init__(self, connectivity_widget, row, col):
        super().__init__()
        self.connectivity_widget = connectivity_widget
        self.row = row
        self.col = col
        
        self.polarity_btn = UserPlusMinusButton()
        self.polarity_btn.clicked.connect(self.update_state)
        
        # Get current state from connectivity widget
        current_data = connectivity_widget.user_connectivity[row][col]
        self.polarity_btn.state = current_data["state"]
        self.polarity_btn.update_style()

        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_map_str_int = {
            "None": 0,
            "short": 1,
            "medium": 2,
            "long": 3
        }
        self.delay_map_int_str = {
            0: "None",
            1: "short",
            2: "medium",
            3: "long"
        }
        
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(3)
        self.delay_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_slider.setTickInterval(1)
        self.delay_slider.setSingleStep(1)
        self.delay_slider.setPageStep(1)
        self.delay_slider.setValue(self.delay_map_str_int[current_data["delay"]])
        self.delay_slider.valueChanged.connect(self.update_connectivity)

        # Layouts - match original structure
        toggle_btns_layout = QHBoxLayout()
        toggle_btns_layout.addWidget(self.polarity_btn)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay:"))
        delay_layout.addWidget(self.delay_slider)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(toggle_btns_layout)
        layout.addLayout(delay_layout)

        self.setLayout(layout)

        # Configure initial state
        self.update_state()
    
    def update_state(self):
        """Update state and enable/disable delay slider"""
        state = self.polarity_btn.state
        if state == "off":
            self.delay_slider.setValue(0)
            self.delay_slider.setEnabled(False)
        else:
            self.delay_slider.setEnabled(True)
        
        self.update_connectivity()

    def update_connectivity(self):
        """Update the connectivity state in the widget"""
        state = self.polarity_btn.state
        delay = self.delay_map_int_str[self.delay_slider.value()]
        self.connectivity_widget.user_connectivity[self.row][self.col] = {
            "state": state,
            "delay": delay
        }


class UserPlusMinusButton(QPushButton):
    """User version of PlusMinusButton with same styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "off"  # can be 'off', 'excitatory', or 'inhibitory'
        self.update_style()

        self.setFixedSize(30, 30)
        self.clicked.connect(self.toggle_state)

    def toggle_state(self):
        if self.state == "off":
            self.state = "excitatory"
        elif self.state == "excitatory":
            self.state = "inhibitory"
        else:
            self.state = "off"
        self.update_style()

    def update_style(self):
        if self.state == "off":
            self.setText("")
            self.setStyleSheet(BUTTON_STYLES['stim_off'])
        elif self.state == "excitatory":
            self.setText("+")
            self.setStyleSheet(BUTTON_STYLES['stim_excitatory'])
        else:
            self.setText("−")
            self.setStyleSheet(BUTTON_STYLES['stim_inhibitory'])

class DiscoveryModeWidget(QWidget):
    """Discovery Mode as a widget for tab integration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        
        # Initialize data manager from parent or create new one
        self.data_manager = parent.data_manager
        
        # Initialize game state
        self.starting_points = 100  # Starting number of points
        self.current_points = self.starting_points
        
        # Challenge system
        self.current_challenge = None
        self.key_index = 0  # Track which solution was matched in Phase 1 for multi-solution challenges
        self.challenge_timer = QTimer()
        self.challenge_start_time = QTime()
        self.challenge_times = {}  # Store completion times for each challenge
        
        # Live graphing system
        self.live_graph_worker = None
        self.live_graph_thread = None
        self.setup_live_graphing()
        
        # Start in experiment mode to keep connectivity hidden throughout Discovery Mode
        # Clear any existing connectivity to ensure clean state for Discovery Mode
        self.data_manager.set_mode("experiment")
        
        # Initialize with empty DM_connectivity data
        empty_connectivity = []
        for i in range(9):
            empty_connectivity.append({"state": "off", "delay": "None"})
        self.data_manager.load_challenge_connectivity(
            empty_connectivity,
            1  # Default threshold
        )
        
        # Clear buffers to start fresh
        self.data_manager.reset_graphing_buffers()

        
        # Use parent's GPIO system (main lab application manages GPIO)
        self.gpio_interface = parent.gpio_interface
        self.gpio_worker = parent.gpio_worker
        self.gpio_thread = parent.gpio_thread
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI with all components"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top challenge controls panel (lives, timer, start/stop buttons)
        challenge_panel = self.create_challenge_controls_panel()
        main_layout.addWidget(challenge_panel)
        
        # Instructions and RGC graph side by side
        top_container = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left: Instructions panel
        instructions_panel = self.create_instructions_panel()
        top_layout.addWidget(instructions_panel, stretch=1)
        
        # Right: RGC graph panel
        rgc_panel = self.create_bottom_rgc_panel()
        top_layout.addWidget(rgc_panel, stretch=1)
        
        top_container.setLayout(top_layout)
        main_layout.addWidget(top_container)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #bdc3c7; }")
        main_layout.addWidget(separator)
        
        # Central panels container - two panels side by side
        central_container = QWidget()
        central_layout = QHBoxLayout()
        central_layout.setSpacing(15)
        central_layout.setContentsMargins(0, 0, 0, 0)
        
        # Left panel: Stimulus selection
        self.stimulus_panel = self.create_stimulus_panel()
        central_layout.addWidget(self.stimulus_panel, stretch=1)
        
        # Right panel: Connectivity configuration
        self.connectivity_panel = self.create_connectivity_panel()
        central_layout.addWidget(self.connectivity_panel, stretch=1)
        
        central_container.setLayout(central_layout)
        main_layout.addWidget(central_container, stretch=1)

        # upon initialization, both phase 1 and phase 2 cannot be accessed before the challenge is started. 
        self.stimulus_panel.setEnabled(False)
        self.connectivity_panel.setEnabled(False)
        
        # Apply visual grayed-out styling to connectivity panel
        self.set_connectivity_panel_visual_state(False)

        self.setLayout(main_layout)

    def create_challenge_controls_panel(self):
        """Create the challenge controls panel with lives, timer, and challenge selection"""
        panel = QWidget()
        panel.setFixedHeight(55)
        panel.setStyleSheet(GROUP_BOX_STYLES['discovery_controls_panel'])
        
        layout = QHBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(15, 10, 15, 10)

        # Challenge selection
        challenge_container = QWidget()
        challenge_layout = QHBoxLayout()
        challenge_layout.setContentsMargins(0, 0, 0, 0)
        
        challenge_label = QLabel("Current Challenge: ")
        challenge_label.setAlignment(Qt.AlignCenter)
        challenge_label.setStyleSheet(LEGEND_STYLES['discovery_controls_title'])
        challenge_layout.addWidget(challenge_label)
        
        # Challenge dropdown
        self.challenge_combo = QComboBox()
        self.challenge_combo.setFixedSize(180, 25) 
        # Load challenges from JSON file
        challenge_items = []
        json_path = os.path.join("GUI", ".default_code", ".default_discoveryMode_challenges.json")
        with open(json_path, 'r') as f:
            self.challenges_data = json.load(f)
        # Add challenges in the order they appear in the JSON
        for challenge_name in self.challenges_data.keys():
            challenge_items.append(challenge_name)
 
        
        self.challenge_combo.addItems(challenge_items)
        self.challenge_combo.setStyleSheet(DROPDOWN_STYLES['dark_panel'])
        self.challenge_combo.currentTextChanged.connect(self.on_challenge_selected)
        challenge_layout.addWidget(self.challenge_combo)
        
        challenge_container.setLayout(challenge_layout)
        layout.addWidget(challenge_container)
        
        self.start_challenge_button = QPushButton("Start Challenge")
        self.start_challenge_button.setStyleSheet(BUTTON_STYLES['discovery_test'])
        self.start_challenge_button.clicked.connect(self.start_current_challenge)
        
        # Initialize with first challenge selected and enable start button
        if challenge_items:
            self.selected_challenge_id = challenge_items[0]
            self.start_challenge_button.setEnabled(True)
        else:
            self.selected_challenge_id = None
            self.start_challenge_button.setEnabled(False)
        
        layout.addWidget(self.start_challenge_button)
        
        # Lives display
        lives_container = QWidget()
        lives_layout = QHBoxLayout()
        lives_layout.setContentsMargins(0, 0, 0, 0)
        
        lives_label = QLabel("Points: ")
        lives_label.setAlignment(Qt.AlignCenter)
        lives_label.setStyleSheet(LEGEND_STYLES['discovery_controls_title'])
        lives_layout.addWidget(lives_label)
        
        self.lives_toolbar_label = QLabel(f"{self.current_points}")
        self.lives_toolbar_label.setAlignment(Qt.AlignCenter)
        self.lives_toolbar_label.setStyleSheet(LEGEND_STYLES['toolbar_lives_white'])
        lives_layout.addWidget(self.lives_toolbar_label)
        
        lives_container.setLayout(lives_layout)
        layout.addWidget(lives_container)
        
        # Timer display
        timer_container = QWidget()
        timer_layout = QHBoxLayout()
        timer_layout.setContentsMargins(0, 0, 0, 0)
        
        timer_label = QLabel("Timer: ")
        timer_label.setAlignment(Qt.AlignCenter)
        timer_label.setStyleSheet(LEGEND_STYLES['discovery_controls_title'])
        timer_layout.addWidget(timer_label)
        
        self.timer_toolbar_display = QLabel("00:00")
        self.timer_toolbar_display.setAlignment(Qt.AlignCenter)
        self.timer_toolbar_display.setStyleSheet(LEGEND_STYLES['toolbar_lives_white'])
        timer_layout.addWidget(self.timer_toolbar_display)
        
        timer_container.setLayout(timer_layout)
        layout.addWidget(timer_container)
        
        
        
        panel.setLayout(layout)
        return panel
    
    def on_challenge_selected(self, challenge_text):
        """Handle challenge selection from dropdown"""
        # Extract the base challenge name (remove completion time if present)
        if " - ✅" in challenge_text:
            base_challenge_name = challenge_text.split(" - ✅")[0]
        else:
            base_challenge_name = challenge_text
        
        # Use the challenge name directly as the ID (from JSON keys)
        new_challenge_id = base_challenge_name
        
        # Check if there's already a challenge running and it's different
        if self.current_challenge and new_challenge_id != self.current_challenge:
            reply = QMessageBox.question(
                self,
                'Switch Challenge',
                f'Selecting a new challenge will reset the current challenge.\n\n'
                'Are you sure you want to continue?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Reset current challenge
                self.reset_current_challenge()
                self.selected_challenge_id = new_challenge_id
                
                # Load challenge connectivity into RGC1 for proper graph response
                if new_challenge_id in self.challenges_data:
                    challenge_data = self.challenges_data[new_challenge_id]
                    # Use first solution's connectivity if multiple solutions exist
                    if isinstance(challenge_data, list):
                        first_solution = challenge_data[0]
                        self.data_manager.load_challenge_connectivity(
                            first_solution['connectivity'],
                            first_solution['threshold']
                        )
                    else:
                        self.data_manager.load_challenge_connectivity(
                            challenge_data['connectivity'],
                            challenge_data['threshold']
                        )
                self.start_challenge_button.setEnabled(True)
                self.start_challenge_button.setText("Start Challenge")
                self.data_manager.reset_graphing_buffers()


            else:
                # Revert dropdown to current challenge
                current_challenge_text = self.current_challenge if self.current_challenge else "Select Challenge..."
                
                # Temporarily disconnect signal to avoid recursion
                self.challenge_combo.currentTextChanged.disconnect()
                self.challenge_combo.setCurrentText(current_challenge_text)
                self.challenge_combo.currentTextChanged.connect(self.on_challenge_selected)
                return
        else:
            # No conflict, proceed normally
            previous_challenge = self.selected_challenge_id
            self.selected_challenge_id = new_challenge_id
            
            # Don't load any challenge connectivity on selection - wait for Start button
            # This prevents the RGC graph from showing active without any input stimulus
            
            # Explicitly reset to empty connectivity to prevent any RGC activation
            empty_connectivity = []
            for i in range(9):
                empty_connectivity.append({"state": "off", "delay": "None"})
            
            self.data_manager.load_challenge_connectivity(
                empty_connectivity,
                1  # Default threshold
            )
        
            # Just reset the graphing buffers to clear any previous data
            self.data_manager.reset_graphing_buffers()

            # Only reset panels if selecting a different challenge
            if previous_challenge != new_challenge_id:
                self.reset_stimulus_panel()
                self.reset_connectivity_panel()

            
            # Enable start button if challenge is selected and not currently running the same challenge
            if self.current_challenge == new_challenge_id:
                self.start_challenge_button.setEnabled(False)
                self.start_challenge_button.setText("Challenge Running")
            else:
                self.start_challenge_button.setEnabled(True)
                self.start_challenge_button.setText("Start Challenge")

    def start_current_challenge(self):
        """Start the currently selected challenge"""
        if self.selected_challenge_id:
            self.start_challenge(self.selected_challenge_id)
        
        self.stimulus_panel.setEnabled(True)
    
    def reset_stimulus_panel(self):
        """Reset the stimulus panel to clean state while maintaining experiment mode LED state"""
        # Reset all grid buttons to unchecked state (for Discovery Mode UI only)
        for button in self.grid_buttons:
            button.setChecked(False)
        
        # Reset data manager stimulus state for Discovery Mode
        self.data_manager.DM_stim = np.array([False, False, False, False, False, False, False, False, False])
    
        
        # Reset motion type to Static
        self.motion_combo.setCurrentText("Static")
        
        # Reset speed and direction (will be disabled for Static)
        self.speed_combo.clear()
        self.speed_combo.addItem("---")
        self.direction_combo.clear()
        self.direction_combo.addItem("---")
        
        # Disable speed and direction groups
        self.speed_group.setEnabled(False)
        self.direction_group.setEnabled(False)
    
    def reset_connectivity_panel(self):
        """Reset the connectivity panel to clean state"""
        # Reset user connectivity widget
        self.user_connectivity_widget.reset_connectivity()
        
        # Reset threshold to default value
        self.user_threshold_spinbox.setValue(1)
        
        # Disable connectivity panel and apply grayed-out styling
        self.set_connectivity_panel_enabled(False)
    
    def reset_current_challenge(self):
        """Reset the current challenge state"""
        if self.current_challenge:

            # Stop timer if running
            if self.challenge_timer.isActive():
                self.challenge_timer.stop()
                try:
                    self.challenge_timer.timeout.disconnect()
                except:
                    pass  # Ignore if already disconnected
            
            # Reset UI elements
            self.timer_toolbar_display.setText("00:00")
            self.reset_stimulus_panel()
            self.reset_connectivity_panel() 
            self.stimulus_panel.setEnabled(False)
            self.set_connectivity_panel_enabled(False)
            
            # Reset to empty connectivity to avoid showing active RGC without stimulus
            empty_connectivity = []
            for i in range(9):
                empty_connectivity.append({"state": "off", "delay": "None"})
            
            self.data_manager.load_challenge_connectivity(
                empty_connectivity,
                1  # Default threshold
            )
            
            # Clear current challenge and reset key index
            self.current_challenge = None
            self.key_index = 0
            
    
    # Copy all the methods from ExperimentWindow here
    def create_instructions_panel(self):
        """Create the top instructions panel"""
        panel = QGroupBox("Instructions: ")
        panel.setStyleSheet(GROUP_BOX_STYLES['discovery_instructions'])
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        
        instructions = QLabel("""
        1. Select and start a challenge from the menu above. 
        2. Complete phases 1 and 2.

        Tip: Watch the live RGC response graph to guide your progress. 
        """)
        instructions.setAlignment(Qt.AlignLeft)
        instructions.setStyleSheet("""
            QLabel {
                font-family: 'Asap';
                font-size: 14px;
                color: #000000;
                background-color: transparent;
                padding: 0px;
                line-height: 1.2;
            }
        """)
        
        layout.addWidget(instructions)
        panel.setLayout(layout)
        panel.setFixedHeight(120)
        
        return panel
    
    def create_stimulus_panel(self):
        """Create the left panel for stimulus configuration"""
        panel = QGroupBox("Phase 1: Discovery the Preferred Stimulus")
        panel.setStyleSheet(GROUP_BOX_STYLES['discovery_panel'])
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        

        stim_layout = QHBoxLayout()
        
        
        # 3x3 grid of toggle buttons
        grid_container = QGroupBox("Stimulus Pattern")
        grid_container.setStyleSheet(GROUP_BOX_STYLES["discovery_sub_panel"])
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(5)
        self.grid_layout.setAlignment(Qt.AlignCenter)
        
        self.grid_buttons = []
        for j in range(9):
            button = QPushButton(f"{j+1}")
            button.setFixedSize(50, 50)
            button.setCheckable(True)
            button.setStyleSheet(BUTTON_STYLES['discovery_grid'])
            button.clicked.connect(lambda checked, index=j: self.update_grid_selection(checked, index))
            self.grid_layout.addWidget(button, j // 3, j % 3)
            self.grid_buttons.append(button)
        
        grid_container.setLayout(self.grid_layout)
        stim_layout.addWidget(grid_container)
        layout.addLayout(stim_layout)
        
        # Properties section
        properties_container = QWidget()
        properties_layout = QVBoxLayout()
        
        # Motion type selection
        motion_group = QGroupBox("Motion Type")
        motion_group.setStyleSheet(GROUP_BOX_STYLES['discovery_sub_panel'])
        motion_layout = QVBoxLayout()
        
        # Motion type combobox
        self.motion_combo = QComboBox()
        self.motion_combo.addItems(["Static", "Moving"])
        self.motion_combo.setCurrentText("Static")  # Set default to static
        self.motion_combo.setStyleSheet(DROPDOWN_STYLES['secondary'])
        
        # Connect combobox to enable/disable speed and direction
        self.motion_combo.currentTextChanged.connect(self.on_motion_type_changed)
        
        motion_layout.addWidget(self.motion_combo)
        motion_group.setLayout(motion_layout)
        properties_layout.addWidget(motion_group)
        
        # Speed selection
        speed_group = QGroupBox("Speed")
        speed_group.setStyleSheet(GROUP_BOX_STYLES['discovery_sub_panel'])
        speed_layout = QVBoxLayout()
        
        # Speed combobox
        self.speed_combo = QComboBox()
        self.speed_combo.addItem("---")  # Start with "---" since Static is default
        self.speed_combo.setStyleSheet(DROPDOWN_STYLES['secondary'])
        
        speed_layout.addWidget(self.speed_combo)
        speed_group.setLayout(speed_layout)
        self.speed_group = speed_group  # Store reference for enabling/disabling
        properties_layout.addWidget(speed_group)
        
        # Direction selection
        direction_group = QGroupBox("Direction")
        direction_group.setStyleSheet(GROUP_BOX_STYLES['discovery_sub_panel'])
        direction_layout = QVBoxLayout()
        
        # Direction combobox
        self.direction_combo = QComboBox()
        self.direction_combo.addItem("---")  # Start with "---" since Static is default
        self.direction_combo.setStyleSheet(DROPDOWN_STYLES['secondary'])
        
        direction_layout.addWidget(self.direction_combo)
        direction_group.setLayout(direction_layout)
        self.direction_group = direction_group  # Store reference for enabling/disabling
        properties_layout.addWidget(direction_group)
        
        # Initially disable both speed and direction since static is selected
        self.speed_group.setEnabled(False)
        self.direction_group.setEnabled(False)
        
        properties_container.setLayout(properties_layout)
        stim_layout.addWidget(properties_container)
        
        # Test stimulus button
        self.test_stimulus_button = QPushButton("Test Stimulus")
        self.test_stimulus_button.setStyleSheet(BUTTON_STYLES['discovery_test'])
        self.test_stimulus_button.clicked.connect(self.test_stimulus)
        layout.addWidget(self.test_stimulus_button)
        
        panel.setLayout(layout)
        return panel
    
    def get_challenge_difficulty(self, challenge_name):
        """Determine the difficulty level of a challenge based on its name"""
        if challenge_name.startswith("Easy"):
            return "easy"
        elif challenge_name.startswith("Medium"):
            return "medium"
        elif challenge_name.startswith("Hard"):
            return "hard"
        else:
            return "medium"  # Default to medium if unclear
    
    def get_point_deduction(self, challenge_name):
        """Get point deduction amount based on challenge difficulty"""
        difficulty = self.get_challenge_difficulty(challenge_name)
        
        if difficulty == "easy":
            return 5
        elif difficulty == "medium":
            return 5
        elif difficulty == "hard":
            return 5
        else:
            return 5  # Default to medium
    
    def test_stimulus(self):
        # get key info from the json file - handle multiple solutions
        challenge_data = self.challenges_data[self.current_challenge]
        
        # get user input from GUI
        user_stim = np.array(self.data_manager.DM_stim).astype(bool) 
        user_motion = self.motion_combo.currentText().lower()
        user_dir = self.direction_combo.currentText().lower()
        user_speed = self.speed_combo.currentText().lower()

        # Check if no stimulus is selected using .any()
        if np.array_equal(user_stim, np.array([True]*9)):
            QMessageBox.warning(self, "No Selection", "Please select at least one stimulus position.")
            return
        
        # Check if challenge has multiple solutions (array of solution objects) or single solution
        stimulus_match = False
        if isinstance(challenge_data, list):
            # Multiple possible solutions - check if user input matches any of them
            for index, possible_solution in enumerate(challenge_data):
                key_stim = np.array(possible_solution['stim_array']).astype(bool)
                key_motion = possible_solution['motion_type'].lower()
                key_dir = "---" if possible_solution['direction'] == "" else possible_solution['direction'].lower()
                key_speed = "---" if possible_solution['speed'] == "" else possible_solution['speed'].lower()
                
                if (np.array_equal(user_stim, key_stim) and 
                    user_motion == key_motion and 
                    user_dir == key_dir and 
                    user_speed == key_speed):
                    stimulus_match = True
                    self.key_index = index  # Store which solution was matched
                    break
        else:
            # Single solution - original behavior
            key_stim = np.array(challenge_data['stim_array']).astype(bool)
            key_motion = challenge_data['motion_type'].lower()
            key_dir = "---" if challenge_data['direction'] == "" else challenge_data['direction'].lower()
            key_speed = "---" if challenge_data['speed'] == "" else challenge_data['speed'].lower()
            
            if (np.array_equal(user_stim, key_stim) and 
                user_motion == key_motion and 
                user_dir == key_dir and 
                user_speed == key_speed):
                stimulus_match = True
                self.key_index = 0  # For single solution, always use index 0
        
        if stimulus_match:
            # Create a custom message box with green checkmark
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Correct Stimulus")
            msg_box.setText("<center>✅<br><br>Correct stimulus!<br><br>Proceed to Phase 2: Discover the Circuit Connectivity.</center>")
            msg_box.setIcon(QMessageBox.NoIcon)
            msg_box.exec_()
            
            # Disable Phase 1 to lock in the correct answer
            self.stimulus_panel.setEnabled(False)
            # Enable connectivity panel (Phase 2)
            self.set_connectivity_panel_enabled(True)
        else:
            # Wrong answer - deduct points based on difficulty
            points_lost = self.get_point_deduction(self.current_challenge)
            self.lose_points(points_lost)
            
            QMessageBox.warning(self, "Incorrect Stimulus", f"Incorrect stimulus pattern. You lost {points_lost} points. Try again!")
            return 
        
    def create_connectivity_panel(self):
        """Create the right panel for connectivity configuration"""
        panel = QGroupBox("Phase 2: Discover the Circuit Connectivity")
        panel.setStyleSheet(GROUP_BOX_STYLES['discovery_panel'])
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Legend section - matching ConnectivityManager format
        legend_layout = QGridLayout()
        legend_layout.setVerticalSpacing(2)
        
        # Create legend labels and circles - store references for styling changes
        self.connectivity_legend_labels = []
        self.connectivity_legend_circles = []
        
        self.silent_label = QLabel("Silent:")
        self.silent_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
        legend_layout.addWidget(self.silent_label, 1, 1, alignment=Qt.AlignCenter)
        self.silent_circle = DiscoveryLegendCircle("gray")
        legend_layout.addWidget(self.silent_circle, 2, 1, alignment=Qt.AlignCenter)
        self.connectivity_legend_labels.append(self.silent_label)
        self.connectivity_legend_circles.append(self.silent_circle)

        self.excitatory_label = QLabel("Excitatory:")
        self.excitatory_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
        legend_layout.addWidget(self.excitatory_label, 1, 2, alignment=Qt.AlignCenter)
        self.excitatory_circle = DiscoveryLegendCircle("red")
        legend_layout.addWidget(self.excitatory_circle, 2, 2, alignment=Qt.AlignCenter)
        self.connectivity_legend_labels.append(self.excitatory_label)
        self.connectivity_legend_circles.append(self.excitatory_circle)
        
        self.inhibitory_label = QLabel("Inhibitory:")
        self.inhibitory_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
        legend_layout.addWidget(self.inhibitory_label, 1, 3, alignment=Qt.AlignCenter)
        self.inhibitory_circle = DiscoveryLegendCircle("blue")
        legend_layout.addWidget(self.inhibitory_circle, 2, 3, alignment=Qt.AlignCenter)
        self.connectivity_legend_labels.append(self.inhibitory_label)
        self.connectivity_legend_circles.append(self.inhibitory_circle)
        
        self.delay_label = QLabel("Delay:")
        self.delay_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
        legend_layout.addWidget(self.delay_label, 1, 4, alignment=Qt.AlignCenter)
        self.delay_circle = DiscoveryLegendCircle("delay")
        legend_layout.addWidget(self.delay_circle, 2, 4, alignment=Qt.AlignCenter)
        self.connectivity_legend_labels.append(self.delay_label)
        self.connectivity_legend_circles.append(self.delay_circle)
        
        layout.addLayout(legend_layout)
        
        # User RGC widget - matching NeuronWidget format
        self.user_connectivity_widget = UserNeuronWidget()
        layout.addWidget(self.user_connectivity_widget, alignment=Qt.AlignCenter)
        
        # Threshold control - matching ConnectivityManager format
        threshold_container = QWidget()
        threshold_layout = QHBoxLayout()
        threshold_layout.setContentsMargins(1, 1, 1, 1)
        threshold_layout.setSpacing(0)
        
        self.threshold_label = QLabel("Threshold:")
        self.threshold_label.setFixedWidth(65)
        self.threshold_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
        
        self.user_threshold_spinbox = QSpinBox()
        self.user_threshold_spinbox.setRange(0, 9)
        self.user_threshold_spinbox.setSingleStep(1)
        self.user_threshold_spinbox.setValue(1)  # Default threshold
        self.user_threshold_spinbox.setFixedWidth(45)
        self.user_threshold_spinbox.setAlignment(Qt.AlignCenter)
        self.user_threshold_spinbox.setStyleSheet(DROPDOWN_STYLES['secondary'])
        
        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.user_threshold_spinbox, alignment=Qt.AlignLeft)
        threshold_container.setLayout(threshold_layout)
        layout.addWidget(threshold_container)
        
        # Test connectivity button
        self.test_connectivity_button = QPushButton("Test Connectivity")
        self.test_connectivity_button.setStyleSheet(BUTTON_STYLES['discovery_test'])
        self.test_connectivity_button.clicked.connect(self.test_connectivity)
        layout.addWidget(self.test_connectivity_button)
        
        panel.setLayout(layout)
        return panel
    
    # Essential methods for the Discovery Mode functionality
    def create_bottom_rgc_panel(self):
        """Create the RGC panel with live graph (now for side-by-side layout)"""
        panel = QWidget()
        panel.setFixedHeight(120)  # Match instructions panel height
        panel.setStyleSheet(GROUP_BOX_STYLES['discovery_panel'])
        
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(8, 2, 8, 8)
        
        # Title label
        title_label = QLabel("Live RGC Response")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(LEGEND_STYLES['discovery_instructions'])
        layout.addWidget(title_label)
        
        # RGC plot widget
        import pyqtgraph as pg
        self.rgc_plot = pg.PlotWidget()
        self.rgc_plot.setFixedHeight(90)  
        self.rgc_plot.setLabel('left', 'RGC 1', **{'font-weight': 'normal', 'font-size': '9px'})
        # Hide bottom axis labels but keep it visible
        self.rgc_plot.getAxis('bottom').setStyle(showValues=False)
        self.rgc_plot.getAxis('left').setStyle(tickFont=pg.QtGui.QFont('Asap', 8))
        self.rgc_plot.setYRange(-0.25, 0.25)
        
        # Configure plot appearance to match graphing_manager style
        self.rgc_plot.setBackground('#F2F2F2')  # Light gray background like graphing_manager
        self.rgc_plot.getAxis('left').setPen(pg.mkPen(color='black', width=2))
        self.rgc_plot.getAxis('bottom').setPen(pg.mkPen(color='black', width=2))
        self.rgc_plot.getAxis('left').setTextPen(pg.mkPen(color='black'))
        self.rgc_plot.getAxis('bottom').setTextPen(pg.mkPen(color='black'))
        
        # Disable mouse interaction
        self.rgc_plot.hideButtons()
        self.rgc_plot.setMouseEnabled(x=False, y=False)
        
        # Setup RGC curves with color-changing capability like graphing_manager
        self.rgc_curves = {
            'gray': self.rgc_plot.plot(pen=pg.mkPen(color='gray', width=0.5, alpha=0.3)),
            'yellow': self.rgc_plot.plot(pen=pg.mkPen(color='#DEB33D', width=8, alpha=0.9))
        }
        
        # Set fixed x-axis range and disable auto-ranging
        # Set fixed x-axis range and disable auto-ranging to match main tab
        self.rgc_plot.setXRange(0, 430)  # Match main tab range
        self.rgc_plot.disableAutoRange(axis='x')
        self.rgc_plot.disableAutoRange(axis='y')
        
        # Setup custom y-axis label with minimal tick
        self.rgc_plot.getAxis('left').setTicks([[(0.0, '  ')]])
        
        layout.addWidget(self.rgc_plot)
        
        panel.setLayout(layout)
        return panel
    
    def setup_live_graphing(self):
        """Setup the live graphing system for RGC responses"""
        # Connect to the main data manager's buffer data signal
        self.data_manager.buffer_data_ready.connect(self.update_discovery_plots)
    
    # Add other essential methods
    def update_grid_selection(self, checked, index):        
        """Update visual feedback when grid buttons are toggled"""
        # Update the data manager with current selection
        self.data_manager.DM_stim[index] = checked

    def test_connectivity(self):
        """Compare connectivity with json key"""
        # Get challenge data - handle multiple solutions
        challenge_data = self.challenges_data[self.current_challenge]

        # Get connectivity from user widget
        user_connectivity_raw = self.user_connectivity_widget.get_connectivity()
        user_connectivity = np.array(user_connectivity_raw).flatten()
        user_threshold = self.user_threshold_spinbox.value()

        # check first if the user has turned on at least one photoreceptor
        if np.array_equal(user_connectivity, [{"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}, {"state": "off", "delay": "None"}]):
            QMessageBox.warning(self, "No Connectivity", "Please configure at least one photoreceptor.")
            return
      
        # Check if challenge has multiple solutions (array of solution objects) or single solution
        connectivity_match = False
        if isinstance(challenge_data, list):
            # Multiple possible solutions - use the specific solution that was matched in Phase 1
            if self.key_index < len(challenge_data):
                target_solution = challenge_data[self.key_index]
                key_connectivity = np.array(target_solution['connectivity'])
                key_threshold = target_solution['threshold']
                if np.array_equal(key_connectivity, user_connectivity) and key_threshold == user_threshold:
                    connectivity_match = True
        else:
            # Single solution - original behavior
            key_connectivity = np.array(challenge_data['connectivity'])
            key_threshold = challenge_data['threshold']
            if np.array_equal(key_connectivity, user_connectivity) and key_threshold == user_threshold:
                connectivity_match = True
        
        if connectivity_match:
            # Create a custom message box with green checkmark
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Correct Connectivity")
            msg_box.setText("<center>✅<br><br>Correct connectivity!<br><br>Challenge Completed!</center>")
            msg_box.setIcon(QMessageBox.NoIcon)
            msg_box.exec_()
            
            # Complete the challenge
            self.complete_challenge()
            
            # Disable Phase 2 to lock in the correct answer
            self.connectivity_panel.setEnabled(False)

        else:
            # Wrong answer - deduct points based on difficulty
            points_lost = self.get_point_deduction(self.current_challenge)
            self.lose_points(points_lost)
            
            QMessageBox.warning(self, "Incorrect Connectivity", f"Incorrect connectivity configuration. You lost {points_lost} points. Try again!")
            return
            # TODO: come up with a way to give user what stims its currently allowing ? 
        
        
        
        
    
    def on_motion_type_changed(self):
        """Enable/disable speed and direction selection based on motion type"""
        motion_type = self.motion_combo.currentText()
        
        # Enable/disable speed and direction groups
        is_static = motion_type == "Static"
        is_moving = motion_type == "Moving"
        
        self.speed_group.setEnabled(not is_static)
        self.direction_group.setEnabled(not is_static)
        
        # Update combobox options based on motion type
        if is_static:
            # Set both speed and direction to "---" for static
            self.speed_combo.clear()
            self.speed_combo.addItem("---")
            self.direction_combo.clear()
            self.direction_combo.addItem("---")
        elif is_moving:
            # Set speed options for moving
            self.speed_combo.clear()
            self.speed_combo.addItems(["Slow", "Medium", "Fast"])
            self.speed_combo.setCurrentText("Slow")
            # Set direction options for moving
            self.direction_combo.clear()
            self.direction_combo.addItems(["Left", "Right"])
            self.direction_combo.setCurrentText("Right")
    
    def start_challenge(self, challenge_id):
        """Start a specific challenge"""
        if self.current_challenge:
            QMessageBox.information(self, "Challenge Active", 
                f"Please complete the current challenge first!")
            return

        # Reset all buffers to start fresh with the new challenge
        self.data_manager.reset_graphing_buffers()
        self.current_challenge = challenge_id
        self.key_index = 0  # Reset key index for new challenge
        
        # Load challenge connectivity only when challenge is actually started
        if challenge_id in self.challenges_data:
            challenge_data = self.challenges_data[challenge_id]
            # If multiple solutions, just load an empty connectivity initially
            if isinstance(challenge_data, list):
                first_solution = challenge_data[0]
                self.data_manager.load_challenge_connectivity(
                    first_solution['connectivity'],
                    first_solution['threshold']
                )
            else:
                # For single solution challenges, load actual connectivity
                self.data_manager.load_challenge_connectivity(
                    challenge_data['connectivity'],
                    challenge_data['threshold']
                )
       
        # Disable start button and update text
        self.start_challenge_button.setEnabled(False)
        self.start_challenge_button.setText("Challenge Running")
        
        # Start timer
        self.challenge_start_time = QTime.currentTime()
        self.challenge_timer.timeout.connect(self.update_timer_display)
        self.challenge_timer.start(100)  # Update every 100ms
                
        # Update timer display
        self.timer_toolbar_display.setText(f"00:00")
            
    def complete_challenge(self):
        """Complete the current challenge"""
        if not self.current_challenge:
            return
        
        # Stop timer
        self.challenge_timer.stop()
        self.challenge_timer.timeout.disconnect()
        
        # Calculate elapsed time
        elapsed_ms = self.challenge_start_time.msecsTo(QTime.currentTime())
        elapsed_seconds = elapsed_ms / 1000.0
        minutes = int(elapsed_seconds // 60)
        seconds = elapsed_seconds % 60
        
        time_str = f"{minutes:02d}:{seconds:05.2f}"
        
        # Store completion time
        self.challenge_times[self.current_challenge] = time_str
        
        # Update dropdown to show completion time
        self.update_challenge_dropdown_with_time(self.current_challenge, time_str)
        
        # Update displays
        self.timer_toolbar_display.setText("00:00")
        
        # Re-enable start challenge button
        self.start_challenge_button.setEnabled(True)
        
        # Update displays
        self.timer_toolbar_display.setText("00:00")
        
        # Re-enable start challenge button
        self.start_challenge_button.setEnabled(True)
        self.start_challenge_button.setText("Start Challenge")
        
        challenge_name = self.current_challenge
        self.current_challenge = None
        
        print(f"Completed challenge: {challenge_name} in {time_str}")
        QMessageBox.information(self, "Challenge Completed!", 
            f"Congratulations!\n\nYou completed '{challenge_name}' in {time_str}")
    
    def update_challenge_dropdown_with_time(self, challenge_name, time_str):
        """Update the challenge dropdown to show completion time"""
        # Find the index of the completed challenge
        for i in range(self.challenge_combo.count()):
            item_text = self.challenge_combo.itemText(i)
            # Check if this is the challenge we just completed (handle both formats)
            if item_text == challenge_name or item_text.startswith(f"{challenge_name} -"):
                # Update the text to include completion time
                new_text = f"{challenge_name} - ✅ {time_str}"
                self.challenge_combo.setItemText(i, new_text)
                break
    
    def stop_challenge_stimulation(self):
        """Stop challenge stimulation - turn off all LEDs and stimulation"""
        # Stop the challenge timer if it's running
        if hasattr(self, 'challenge_timer') and self.challenge_timer.isActive():
            self.challenge_timer.stop()
        
        # Stop stimulation (this will turn off the on/off button)
        self.data_manager.set_stim_running(False)
        
    
    def update_timer_display(self):
        """Update the timer display during a challenge"""
        if not self.current_challenge:
            return
        
        elapsed_ms = self.challenge_start_time.msecsTo(QTime.currentTime())
        elapsed_seconds = elapsed_ms / 1000.0
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        
        self.timer_toolbar_display.setText(f"{minutes:02d}:{seconds:02d}")
    
    def update_discovery_plots(self, buffer_data):
        """Update Discovery Mode plots with data from main GPIO worker"""
        try:
            # Handle the new unified data format
            if 'computed_rgc_responses' in buffer_data:
                # New format has full buffer in 'computed_rgc_responses'
                rgc_response_buffer = buffer_data["computed_rgc_responses"]
            elif 'latest_computed_rgc_responses' in buffer_data:
                # Fallback: use the data manager to get full buffer
                rgc_response_buffer = np.array(list(self.data_manager.computed_rgc_response_buffer_queue))
            else:
                return
            
            if len(rgc_response_buffer) == 0:
                return
                
            x_axis = np.arange(rgc_response_buffer.shape[0])
            
            # Update RGC1 response curve (index 0 for RGC1)
            rgc1_values = rgc_response_buffer[:, 0, 0]  # RGC1 response
            rgc1_y_fixed = np.full_like(rgc1_values, 0.0)
            
            # Use the existing color scheme: gray baseline, yellow for active
            self.plot_discovery_colored_segments(
                x_axis, rgc1_y_fixed, rgc1_values, 
                self.rgc_curves
            )
            
        except Exception as e:
            # Handle errors silently to avoid flooding console - but uncomment for debugging
            # print(f"Discovery Mode plot update error: {e}")
            pass
    
    def plot_discovery_colored_segments(self, x_data, y_data, raw_values, curve_dict):
        """Plot colored segments for Discovery Mode RGC graph"""
        if len(x_data) < 2:
            return

        # Clear existing curves
        for curve in curve_dict.values():
            curve.clear()
            
        # Group consecutive points by activity level
        segments = {'gray': [], 'yellow': []}
        
        current_value = None
        segment_start = 0
        
        # If no challenge is currently active, force all segments to gray
        # This prevents RGC from showing active between challenge selection and start
        if self.current_challenge is None:
            # Just show everything as gray/inactive if no challenge is running
            segments['gray'] = list(zip(x_data, y_data))
            curve_dict['gray'].setData(x_data, y_data)
            return
        
        for i in range(len(raw_values)):
            # Determine if RGC is active (threshold > 0.5)
            value_category = 'yellow' if raw_values[i] > 0.5 else 'gray'
            
            if current_value != value_category:
                # Finish previous segment
                if current_value is not None and segment_start < i:
                    segment_x = x_data[segment_start:i+1]
                    segment_y = y_data[segment_start:i+1]
                    if len(segment_x) > 1:
                        segments[current_value].extend(list(zip(segment_x, segment_y)))
                        # Add separator for discontinuous segments
                        if i < len(raw_values) - 1:
                            segments[current_value].append((np.nan, np.nan))
                
                current_value = value_category
                segment_start = i
        
        # Handle final segment
        if current_value is not None and segment_start < len(raw_values):
            segment_x = x_data[segment_start:]
            segment_y = y_data[segment_start:]
            if len(segment_x) > 1:
                segments[current_value].extend(list(zip(segment_x, segment_y)))
        
        # Plot segments with correct colors
        for color, segment_points in segments.items():
            if segment_points and color in curve_dict:
                x_vals = [point[0] for point in segment_points]
                y_vals = [point[1] for point in segment_points]
                curve_dict[color].setData(x_vals, y_vals)
    
    def lose_points(self, points_to_lose):
        """Decrease points and update the display"""
        if self.current_points > 0:
            self.current_points = max(0, self.current_points - points_to_lose)
            
            # Update toolbar points display
            self.lives_toolbar_label.setText(f"{self.current_points}")
            
            # Update points color based on remaining points
            if self.current_points > 20:
                self.lives_toolbar_label.setStyleSheet(LEGEND_STYLES['toolbar_lives_white'])
            else:
                self.lives_toolbar_label.setStyleSheet(LEGEND_STYLES['toolbar_lives_warning_white'])
            
            if self.current_points == 0:
                QMessageBox.information(self, "Game Over", "You've run out of points!")
            
    
    def set_connectivity_panel_visual_state(self, enabled):
        """Set visual appearance of connectivity panel components based on enabled state"""
        if enabled:
            # Restore normal styling
            for label in self.connectivity_legend_labels:
                label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
            
            # Restore legend circles to normal colors
            for circle in self.connectivity_legend_circles:
                circle.set_grayed(False)
            
            self.threshold_label.setStyleSheet(LEGEND_STYLES['discovery_legend'])
            
            # Restore connectivity widget to normal appearance
            self.user_connectivity_widget.setStyleSheet("")
            self.user_connectivity_widget.set_grayed_out(False)
            self.user_connectivity_widget.setEnabled(True)
            
            # Re-enable the spinbox and test button
            self.user_threshold_spinbox.setEnabled(True)
            self.test_connectivity_button.setEnabled(True)
            
        else:
            # Apply grayed-out styling
            grayed_style = """
                QLabel {
                    font-family: 'Asap';
                    font-size: 11px;
                    color: #a0a0a0;
                    background-color: transparent;
                    padding: 2px;
                }
            """
            
            for label in self.connectivity_legend_labels:
                label.setStyleSheet(grayed_style)
            
            # Gray out legend circles
            for circle in self.connectivity_legend_circles:
                circle.set_grayed(True)
            
            self.threshold_label.setStyleSheet(grayed_style)
            
            # Apply grayed-out appearance to connectivity widget using custom method
            self.user_connectivity_widget.set_grayed_out(True)
            self.user_connectivity_widget.setEnabled(False)
            
            # Also gray out the spinbox and test button
            self.user_threshold_spinbox.setEnabled(False)
            self.test_connectivity_button.setEnabled(False)
    
    def set_connectivity_panel_enabled(self, enabled):
        """Enable/disable connectivity panel with proper visual styling"""
        self.connectivity_panel.setEnabled(enabled)
        self.set_connectivity_panel_visual_state(enabled)
    
    def enable_phase_two(self):
        """Enable phase 2 (connectivity panel) with proper visual styling"""
        self.set_connectivity_panel_enabled(True)
        
    
    def cleanup_discovery_mode(self):
        """Clean up Discovery Mode state when tab is closed - reset connectivity and switch back to lab mode"""
        # Stop any running challenge stimulation
        self.stop_challenge_stimulation()
        # Turn off all LEDs
        for row in range(3):
            for col in range(3):
                self.data_manager.set_selected_stim_state(row, col, False)
                self.data_manager.set_activated_stim_state(row, col, False)
        
        # Switch back to lab mode only when Discovery Mode tab is closed
        self.data_manager.set_mode("lab")
            
    def closeEvent(self, event):
        """Handle widget cleanup when closing"""
        self.cleanup_discovery_mode()
        event.accept()