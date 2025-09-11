import os
import sys
from PyQt5.QtCore import QSize, Qt, QTimer, QPointF, QRectF, pyqtSignal

from PyQt5.QtWidgets import *
from PyQt5.QtGui import * 
from PyQt5.QtSvg import QSvgRenderer, QSvgWidget
import numpy as np
from data_manager import DataManager
from styles import *

"""
Contains the Visual stimulus manager with stim buttons and options for motion and turning stim on
"""
class VisualStimManager(QGroupBox):
    def __init__(self, data_manager):
        super().__init__("Visual Stimulus Controller")
        self.data_manager = data_manager
        self.setFixedWidth(250)
        self.visual_LED_grid = LEDGrid(data_manager)
        self.setStyleSheet(GROUP_BOX_STYLES['default'])
        
        # --- LED toggle buttons
        self.LED_toggle_button = LEDControlButton(self.data_manager)
        # when toggled in the widget, updates information in the data_manager which then emits signal about the toggle
        self.data_manager.stim_running_updated.connect(self.LED_toggle_button.update_checked_state)
        self.data_manager.stim_running_updated.connect(self.update_visual_LED_grid)
        self.data_manager.mode_changed.connect(self.update_visual_LED_grid)
        self.data_manager.mode_changed.connect(self.on_mode_changed)  # Add mode change handler
        # Connect to selected_LEDs_updated to refresh button states when data manager changes programmatically
        self.data_manager.selected_LEDs_updated.connect(self.visual_LED_grid.refresh_button_states_from_data_manager)

        # --- Mode 
        self.mode_widget = ModeWidget(self.data_manager)
        # when mode is changed, it updates information in data_manager which then emits signals about the mode change 
        self.data_manager.current_stim_mode_updated.connect(self.update_mode_controls)
        self.data_manager.current_stim_mode_updated.connect(self.LED_toggle_button.update_button)

        # --- Speed Label + Value + Slider
        self.speed_widget = SpeedSlider(self.data_manager)
        self.speed_widget.hide()  # Hidden by default since Static is default mode
        # when speed is changed, it updates information in data_manager which then emits signals about the speed change 
        self.data_manager.current_stim_speed_updated.connect(self.visual_LED_grid.on_speed_change)

        # --- Direction buttons
        self.directions_widget = DirectionSelector(self.data_manager)
        self.directions_widget.hide()  # Hidden by default since Static is default mode
        self.data_manager.current_stim_direction_updated.connect(self.visual_LED_grid.on_direction_change)

        # --- Putting all widgets together in grid
        grid_layout = QGridLayout()
        
        # Create compact labels with transparent background
        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("background: transparent; font-size: 15px;")
        mode_label.setFixedHeight(20)
        
        self.direction_label = QLabel("Direction:")
        self.direction_label.setStyleSheet("background: transparent; font-size: 15px; color: transparent;")  # Transparent text initially
        self.direction_label.setFixedHeight(20)
        
        self.speed_label = QLabel("Speed:")
        self.speed_label.setStyleSheet("background: transparent; font-size: 15px; color: transparent;")  # Transparent text initially
        self.speed_label.setFixedHeight(20)
        
        grid_layout.addWidget(mode_label, 0, 0)
        grid_layout.addWidget(self.mode_widget, 0, 1, 1, 2)  # span 2 columns
        grid_layout.addWidget(self.direction_label, 1, 0)
        grid_layout.addWidget(self.directions_widget, 1, 1)
        grid_layout.addWidget(self.speed_label, 2, 0)
        grid_layout.addWidget(self.speed_widget, 2, 1, 1, 2)  # span 2 columns for 2/3 width

        # Reduce vertical spacing between rows
        grid_layout.setVerticalSpacing(5)
        
        # Set column stretch factors: labels (1/3) and widgets (2/3)
        grid_layout.setColumnStretch(0, 1)  # Label column
        grid_layout.setColumnStretch(1, 2)  # Widget columns (combined)

        """
        Putting both panels together 
        """
        layout = QVBoxLayout()
        layout.setContentsMargins(5,85,5,15)
        layout.addWidget(self.visual_LED_grid, alignment=Qt.AlignCenter)
        layout.addWidget(self.LED_toggle_button, alignment=Qt.AlignCenter)
        layout.addLayout(grid_layout)
        self.setLayout(layout)
        
    def update_mode_controls(self, mode):
        """
        Show/hide widgets based on mode while maintaining layout position.
        """
        if mode != "Motion":
            # Hide motion-specific controls when in Static mode but keep layout space
            self.speed_widget.hide()
            self.speed_label.setStyleSheet("background: transparent; font-size: 15px; color: transparent;")  # Make text transparent
            self.directions_widget.hide()
            self.direction_label.setStyleSheet("background: transparent; font-size: 15px; color: transparent;")  # Make text transparent
        else:
            # Show motion-specific controls when in Motion mode
            self.speed_widget.show()
            self.speed_label.setStyleSheet("background: transparent; font-size: 15px; color: black;")  # Make text visible
            self.directions_widget.show()
            self.direction_label.setStyleSheet("background: transparent; font-size: 15px; color: black;")  # Make text visible
        
        # If stimulation is running, restart it in the new mode
        if self.data_manager.get_stim_running():
            self.visual_LED_grid.handle_stimulation_change()
    
    def update_visual_LED_grid(self, toggle_bool):
        """Simplified LED grid update - just enable/disable mode controls and trigger stimulation"""
        if toggle_bool:
            self.mode_widget.setEnabled(False)
        else: 
            self.mode_widget.setEnabled(True)

        # Use the centralized stimulation handler
        self.visual_LED_grid.handle_stimulation_change() 

    def on_mode_changed(self, mode):
        """Handle mode changes to disable/enable LED toggle button during Discovery Mode challenges"""
        if mode == "experiment":
            # Disable LED toggle button during Discovery Mode challenges
            # LEDs are already on from set_mode(), but user can't modify them
            self.LED_toggle_button.setEnabled(False)
        elif mode == "lab":
            # Re-enable LED toggle button when returning to lab mode
            self.LED_toggle_button.setEnabled(True)

class LEDButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.svg_unchecked = QSvgRenderer(os.path.join(script_dir, "Graphics", "LED_unselected.svg"))
        self.svg_checked = QSvgRenderer(os.path.join(script_dir, "Graphics", "LED_selected.svg"))
        self.svg_on = QSvgRenderer(os.path.join(script_dir, "Graphics", "LED_on.svg"))
        self.setCheckable(True)      
        self.setFixedSize(25, 30) 
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
        """) 
        # the button can be checked and if checked, it can also be on
        self.is_on = False

    def toggle_on(self, turn_on):
        self.is_on = turn_on
        self.update()

    def paintEvent(self, event):
        # draw button background first (so hover/pressed look still works)
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Convert QRect to QRectF
        bounds = QRectF(self.rect())

        # Draw the appropriate SVG
        if self.isChecked() and not self.is_on:
            self.svg_checked.render(painter, bounds)
        elif self.is_on:
            self.svg_on.render(painter, bounds)
        else:
            self.svg_unchecked.render(painter, bounds)
        # End painting
        painter.end()

class LegendCircle(QWidget):
    def __init__(self, circle_type="gray", parent=None):
        super().__init__(parent)
        self.circle_type = circle_type
        self.setFixedSize(20, 20)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define circle parameters
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(self.width(), self.height()) // 2 - 2  # Leave small margin
        
        # Choose color based on type
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
            painter.setBrush(QBrush(Qt.transparent))
            painter.setPen(QPen(QColor(128, 128, 128), 1))
        else:
            # Solid colored circle
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
        
        painter.drawEllipse(QPointF(center_x, center_y), radius, radius)
        
        # Draw triangle for delay type
        if self.circle_type == "delay":
            painter.setPen(QColor("black"))
            font = painter.font()
            font.setPointSizeF(radius * 1.5 )  # Size relative to circle radius
            painter.setFont(font)
            
            # Center triangle character
            triangle_char = "▲"
            rect = QRectF(center_x - radius, center_y - radius, 2*radius, 2*radius)
            painter.drawText(rect, Qt.AlignCenter, triangle_char)

class LEDGrid(QWidget): # good yellow color =  #C49102;
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.updates_since_stim_onset = 0
        
        # Create a single timer for all flash operations
        self.flash_timer = QTimer()
        self.flash_on = False

        layout = QVBoxLayout()

        """
        LED 3x3 panel
        """
        visual_LED_container = QWidget()
        visual_LED_grid = QGridLayout()
        visual_LED_grid.setSpacing(0)  # Remove all internal spacing/grid lines
        visual_LED_grid.setContentsMargins(0, 0, 0, 0)
        visual_LED_container.setLayout(visual_LED_grid)
        visual_LED_container.setFixedSize(165, 165)  # Increased height to accommodate labels
        # Apply border only to the main container, make inner containers transparent
        visual_LED_container.setStyleSheet("""
            QWidget#led_main_container {
                background-color: #f5f5f5;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        visual_LED_container.setObjectName("led_main_container")  # Set object name for specific targeting
        self.buttons = []

        for row in range(3):
            row_buttons = []
            for col in range(3):
                # Create container for LED button + label
                led_container = QWidget()
                led_container.setStyleSheet("""
                    QWidget {
                        background-color: transparent;
                        border: none;
                    }
                """)  # Ensure inner containers have no borders
                led_layout = QVBoxLayout()
                led_layout.setContentsMargins(2, 2, 2, 2)  # Small internal margins for breathing room
                led_layout.setSpacing(1)  # Minimal gap between button and label
                
                # Create LED button
                btn = LEDButton()
                state = self.data_manager.get_selected_stim_state(row, col)
                btn.setChecked(state)

                # Connect to slot, passing coordinates
                btn.clicked.connect(lambda checked, r=row, c=col: self.toggle_led(r, c, checked))
                
                # Create number label (1-9, left to right, top to bottom)
                led_number = row * 3 + col + 1
                number_label = QLabel(str(led_number))
                number_label.setAlignment(Qt.AlignCenter)
                number_label.setStyleSheet("font-size: 10px; color: #666666; font-weight: normal;")
                number_label.setFixedHeight(12)  # Small fixed height for label
                
                # Add button and label to container
                led_layout.addWidget(btn, alignment=Qt.AlignCenter)
                led_layout.addWidget(number_label)
                led_container.setLayout(led_layout)
                
                # Add container to grid
                visual_LED_grid.addWidget(led_container, row, col)
                row_buttons.append(btn)
            
            self.buttons.append(row_buttons)
        """
        LED legend
        """
        LED_legend_layout = QGridLayout()
        LED_legend_layout.setVerticalSpacing(2)
        self.setStyleSheet(LEGEND_STYLES['stim_legend'])
        LED_legend_layout.addWidget(QLabel("Unselected:"), 1, 1, alignment=Qt.AlignCenter)
        unselected_btn = LEDButton()
        unselected_btn.setFixedSize(20, 25)
        unselected_btn.setChecked(False)
        unselected_btn.setEnabled(False)
        LED_legend_layout.addWidget(unselected_btn, 2, 1, alignment=Qt.AlignCenter)
        LED_legend_layout.addWidget(QLabel("Selected:"), 1, 2, alignment=Qt.AlignCenter)
        selected_btn = LEDButton()
        selected_btn.setChecked(True)
        selected_btn.setEnabled(False)
        selected_btn.setFixedSize(20, 25)
        LED_legend_layout.addWidget(selected_btn, 2, 2, alignment=Qt.AlignCenter)
        LED_legend_layout.addWidget(QLabel("Active:"), 1, 3, alignment=Qt.AlignCenter)
        LED_on_btn = LEDButton()
        LED_on_btn.setChecked(True)
        LED_on_btn.toggle_on(True)
        LED_on_btn.setFixedSize(20, 25)
        LED_on_btn.setEnabled(False)
        LED_legend_layout.addWidget(LED_on_btn, 2, 3, alignment=Qt.AlignCenter)

        layout.addLayout(LED_legend_layout)
        layout.addWidget(visual_LED_container, alignment=Qt.AlignHCenter)
        self.setLayout(layout)
    
    def toggle_led(self, row, col, checked):
        """
        Update screen, GPIO, and data_manager when a button is clicked.
        """
        self.data_manager.set_selected_stim_state(row, col, checked)
        # the data_manager emits a signal 

    def refresh_button_states_from_data_manager(self):
        """
        Sync LED button states with data manager - called when data manager changes programmatically
        """
        for row in range(3):
            for col in range(3):
                btn = self.buttons[row][col]
                # Get current state from data manager and update button
                selected_state = self.data_manager.get_selected_stim_state(row, col)
                activated_state = self.data_manager.get_activated_stim_state(row, col)
                
                # Temporarily disconnect signal to avoid triggering data manager updates
                btn.clicked.disconnect()
                btn.setChecked(selected_state)
                btn.toggle_on(activated_state)
                # Reconnect the signal
                btn.clicked.connect(lambda checked, r=row, c=col: self.toggle_led(r, c, checked))

    def reset_to_default(self):
        # uses the settings from self.data_manager.visual_stim["default_led_states"] to reset the LEDs to their default status as the user defined or as set by preset
        self.updates_since_stim_onset = 0
        
        # Stop any running timer
        self.flash_timer.stop()
        
        for row in range(3):
            for col in range(3):
                btn = self.buttons[row][col]
                btn.setEnabled(True)
                state = self.data_manager.get_selected_stim_state(row, col)
                btn.is_on = False
                btn.setChecked(state)
                # reset the activity_states 
                self.data_manager.set_activated_stim_state(row, col, is_activated=False)

    def update_button_style_static(self, led_toggle_bool, led_flash_signal=None):
        self.updates_since_stim_onset += 1
        # because we only have 9 LEDs, looping does not come at an expensive cost
        if led_flash_signal is None: # the case for static 
            led_flash_signal = led_toggle_bool

        for row in range(3):
            for col in range(3):
                btn = self.buttons[row][col]
                btn.setEnabled(not led_toggle_bool) # blocks signals when LED activated 

                if btn.isChecked():
                    if led_flash_signal:
                        # Active LED color
                        btn.toggle_on(True)
                        self.data_manager.set_activated_stim_state(row, col, is_activated=True)
                    else:
                        # Selected but not active
                        btn.toggle_on(False)
                        self.data_manager.set_activated_stim_state(row, col, is_activated=False)

    def _speed_toggle_unit(self, led_toggle_bool, direction=None):
        """Toggle the flash state and update LEDs accordingly"""
        self.flash_on = not self.flash_on
        if direction is None: 
            self.update_button_style_static(led_toggle_bool, self.flash_on)
        else: 
            self.update_button_style_motion(led_toggle_bool, direction)

    def start_stimulation(self, mode, speed=None, direction=None):
        """Centralized method to start stimulation in any mode"""
        # Stop any existing stimulation first
        self.stop_stimulation()
        
        # Reset state
        self.updates_since_stim_onset = 0
        self.flash_on = False
        
        if mode == "Static":
            # Static mode: just turn on selected LEDs
            self.update_button_style_static(True)
        elif mode == "Motion":
            # Motion mode: start the timer for animated movement
            if speed is None:
                speed = self.data_manager.get_current_stim_speed()
            if direction is None:
                direction = self.data_manager.get_current_stim_direction()
            
            # Initial LED setup
            self._speed_toggle_unit(True, direction=None)
            
            # Set up timer for motion
            ms_interval = self.data_manager.speed_ms_interval[speed]
            self.flash_timer.timeout.connect(lambda: self._speed_toggle_unit(True, direction))
            self.flash_timer.start(ms_interval)
    
    def stop_stimulation(self):
        """Centralized method to stop all stimulation"""
        # Stop timer if running
        self.flash_timer.stop()
        
        # Disconnect timer signals
        try:
            self.flash_timer.timeout.disconnect()
        except TypeError:
            pass  # No connections existed
        
        # Reset LEDs to default state
        self.reset_to_default()

    def speed_update(self, led_toggle_bool, speed, direction=None):
        """Simplified speed update - just restart stimulation with new parameters"""
        if led_toggle_bool:
            self.start_stimulation("Motion", speed, direction)
        else:
            self.stop_stimulation()
    
    def handle_stimulation_change(self):
        """Central method to handle any stimulation parameter change"""
        is_running = self.data_manager.get_stim_running()
        mode = self.data_manager.get_current_stim_mode()
        
        if is_running:
            if mode == "Static":
                self.start_stimulation("Static")
            elif mode == "Motion":
                speed = self.data_manager.get_current_stim_speed()
                direction = self.data_manager.get_current_stim_direction()
                self.start_stimulation("Motion", speed, direction)
        else:
            self.stop_stimulation()
    
    def on_speed_change(self, speed):
        """Handle speed changes - only restart if Motion mode is active"""
        if (self.data_manager.get_current_stim_mode() == "Motion" and 
            self.data_manager.get_stim_running()):
            self.handle_stimulation_change()
        
    def on_direction_change(self, direction):
        """Handle direction changes - only restart if Motion mode is active"""
        if (self.data_manager.get_current_stim_mode() == "Motion" and 
            self.data_manager.get_stim_running()):
            self.handle_stimulation_change()

    def _get_new_coord(self, row, col, direction):
        if direction == "Up":
            return ((row - 1) % 3), col
        elif direction == "Down":
            return ((row + 1) % 3), col
        elif direction == "Left":
            return row, ((col - 1) % 3)
        elif direction == "Right":
            return row, ((col + 1) % 3)
    
    def update_button_style_motion(self, led_toggle_bool, direction):
        self.updates_since_stim_onset += 1
        next_active = []
        for row in range(3):
            for col in range(3):
                btn = self.buttons[row][col]
                btn.setEnabled(not led_toggle_bool) # blocks signals when LED activated 
                if self.data_manager.get_activated_stim_state(row, col):
                    # disactivate current led button
                    btn.toggle_on(False)
                    self.data_manager.set_activated_stim_state(row, col, is_activated=False)
                    # activate the next in the direction required
                    new_row, new_col = self._get_new_coord(row, col, direction)
                    next_active.append((new_row, new_col))

        for new_row, new_col in next_active:     
            self.buttons[new_row][new_col].toggle_on(True)
            self.data_manager.set_activated_stim_state(new_row, new_col, is_activated=True)
    
    
class LEDControlButton(QPushButton):    
    def __init__(self, data_manager): 
        super().__init__()
        self.setFixedWidth(100)
        self.data_manager = data_manager
        self.setCheckable(True)
        
        # Single connection established once
        self.clicked.connect(self.handle_click)
        
        # Initialize button state
        self.update_button()
        
        # Apply secondary button styles with larger font
        button_style = BUTTON_STYLES['secondary'] + "font-size: 14px;"
        self.setStyleSheet(button_style)
    
    def handle_click(self):
        """Single click handler for both Static and Motion modes"""
        self.data_manager.set_stim_running(self.isChecked())
    
    def update_button(self):
        """Update button text based on current mode - no signal connections"""
        if self.data_manager.get_current_stim_mode() == "Static":
            self.setText("On / Off")
        elif self.data_manager.get_current_stim_mode() == "Motion":
            self.setText("Start / Stop")
    
    def update_checked_state(self):
        """Update the button's checked state based on the data manager's stim_running state"""
        stim_running = self.data_manager.get_stim_running()
        self.setChecked(stim_running)

class ModeWidget(QWidget):
    def __init__(self, data_manager): 
        super().__init__()
        self.data_manager = data_manager
        
        mode_layout = QHBoxLayout()
        mode_layout.setContentsMargins(0,0,0,0)
        self.static_radio = QRadioButton(text="Static")
        self.motion_radio = QRadioButton(text="Motion")
        
        # Set font size for radio buttons
        self.static_radio.setStyleSheet("font-size: 13px;")
        self.motion_radio.setStyleSheet("font-size: 13px;")
        
        # Set default selection
        self.static_radio.setChecked(True)
        
        # Connect signals
        self.static_radio.toggled.connect(lambda checked: self.on_mode_change("Static") if checked else None)
        self.motion_radio.toggled.connect(lambda checked: self.on_mode_change("Motion") if checked else None)
       
        
        mode_layout.addWidget(self.static_radio)
        mode_layout.addWidget(self.motion_radio)

        self.setLayout(mode_layout)
        #self.mode_dropdown.currentTextChanged.connect(self.on_mode_change)
    
    def on_mode_change(self, text):
        self.data_manager.set_current_stim_mode(text)
        # the data_manager will emit a signal 

class SpeedSlider(QWidget):
    def __init__(self, data_manager): 
        super().__init__()
        self.data_manager = data_manager
        self.setFixedWidth(125)
        self.setStyleSheet(LEGEND_STYLES['stim_legend'])

        # Map slider indices to speed names
        self.speed_map = {
            0: "Slow",
            1: "Medium",
            2: "Fast"
        }

        # Create slider
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(2)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(1)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setPageStep(1)
        self.speed_slider.setValue(1)  # Default to "Medium"

        # Connect signal
        self.speed_slider.valueChanged.connect(self.update_speed)

        # Layout
        slider_layout = QVBoxLayout()
        slider_layout.addWidget(self.speed_slider)

        # Labels underneath
        slider_labels_layout = QHBoxLayout()
        slider_labels_layout.addWidget(QLabel("Slow"), alignment=Qt.AlignLeft)
        slider_labels_layout.addWidget(QLabel("Medium"), alignment=Qt.AlignHCenter)
        slider_labels_layout.addWidget(QLabel("Fast"), alignment=Qt.AlignRight)

        slider_layout.addLayout(slider_labels_layout)

        self.setLayout(slider_layout)

    def update_speed(self, value):
        speed_str = self.speed_map[value]
        # Update the data manager
        self.data_manager.set_current_stim_speed(speed_str)

class DirectionSelector(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Create radio buttons with arrow Unicode characters
        self.left_radio = QRadioButton('← Left')
        self.right_radio = QRadioButton('→ Right')
        
        # Set font size for radio buttons
        self.left_radio.setStyleSheet("font-size: 13px;")
        self.right_radio.setStyleSheet("font-size: 13px;")
        
        # Add to layout
        layout.addWidget(self.left_radio)
        layout.addWidget(self.right_radio)
        
        # Set default selection based on data manager's current direction
        current_direction = self.data_manager.get_current_stim_direction()
        if current_direction == "Left":
            self.left_radio.setChecked(True)
        elif current_direction == "Right":
            self.right_radio.setChecked(True)
        
        # Connect signals - radio buttons automatically handle exclusivity
        self.left_radio.toggled.connect(lambda checked: self.on_direction_selected("Left") if checked else None)
        self.right_radio.toggled.connect(lambda checked: self.on_direction_selected("Right") if checked else None)

        self.setLayout(layout)
        
    def on_direction_selected(self, direction):
        # Update data manager when direction is selected
        self.data_manager.set_current_stim_direction(direction)

"""
Code for the central panel of TopPanel. Contains the two neurons, and their photoreceptor cell manager popout
"""
class ConnectivityManager(QGroupBox):
    def __init__(self, data_manager):
        super().__init__("Connectivity Manager")
        self.setStyleSheet(GROUP_BOX_STYLES['default'])
        self.setContentsMargins(2,2,2,2)  # Match Signal Monitor GroupBox margins
        self.data_manager = data_manager
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(8, 8, 8, 8)  # Match Signal Monitor internal margins
        self.layout.setSpacing(0)  # Match Signal Monitor spacing
        self.setLayout(self.layout)

        # Create legend widget that won't be disabled
        self.legend_widget = self.create_legend_widget()
        self.layout.addWidget(self.legend_widget)

        # Add separator line after legend
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("QFrame { color: #CCCCCC; margin: 5px 0px; }")
        self.layout.addWidget(separator1)

        # Create container for interactive elements that can be disabled
        self.interactive_container = QWidget()
        interactive_layout = QVBoxLayout()
        interactive_layout.setContentsMargins(0, 0, 0, 0)
        interactive_layout.setSpacing(6)  # Add consistent spacing between elements
        self.interactive_container.setLayout(interactive_layout)

        self.RGC_1 = NeuronWidget(neuron_num=1, data_manager=self.data_manager)

        # Connect to data manager updates to refresh GUI when presets are loaded
        self.data_manager.neuron_connectivity_updated.connect(self.update_thresholds_from_data)

        self.threshold_1 = QSpinBox()
        self.threshold_1.setRange(0, 9)
        self.threshold_1.setSingleStep(1)
        self.threshold_1.setValue(self.data_manager.get_neuron_threshold(1))
        self.threshold_1.setFixedWidth(45)
        self.threshold_1.setAlignment(Qt.AlignCenter)
        self.threshold_1.valueChanged.connect(lambda value: self.data_manager.set_neuron_threshold(1, value))
        threshold_1_label = QLabel("Threshold:")
        threshold_1_label.setStyleSheet("background: transparent; font-size: 15px;")


        threshold_1_label.setFixedWidth(75)
        interactive_layout.addWidget(self.RGC_1)
        t_1_layout = QHBoxLayout()
        t_1_layout.setContentsMargins(1, 1, 1, 1)
        t_1_layout.setSpacing(0)  
        t_1_layout.addWidget(threshold_1_label)
        t_1_layout.addWidget(self.threshold_1, alignment=Qt.AlignLeft)
        interactive_layout.addLayout(t_1_layout)

        # Add separator line between RGC 1 and RGC 2
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("QFrame { color: #CCCCCC; margin: 5px 0px; }")
        interactive_layout.addWidget(separator2)

        self.RGC_2 = NeuronWidget(neuron_num=2, data_manager=self.data_manager)
        self.threshold_2 = QSpinBox()
        self.threshold_2.setRange(0, 9)
        self.threshold_2.setSingleStep(1)
        self.threshold_2.setValue(self.data_manager.get_neuron_threshold(2))
        self.threshold_2.setFixedWidth(45)
        self.threshold_2.setAlignment(Qt.AlignCenter)
        self.threshold_2.valueChanged.connect(lambda value: self.data_manager.set_neuron_threshold(2, value))

        threshold_2_label = QLabel("Threshold:")
        threshold_2_label.setStyleSheet("background: transparent; font-size: 15px;")
        interactive_layout.addWidget(self.RGC_2)
        t_2_layout = QHBoxLayout()
        t_2_layout.setContentsMargins(1, 1, 1, 1)
        t_2_layout.setSpacing(0)  
        threshold_2_label.setFixedWidth(75)
        t_2_layout.addWidget(threshold_2_label)
        t_2_layout.addWidget(self.threshold_2, alignment=Qt.AlignLeft)
        interactive_layout.addLayout(t_2_layout)

        # Add the interactive container to the main layout
        self.layout.addWidget(self.interactive_container)

    def create_legend_widget(self):
        """Create a separate legend widget that won't be disabled"""
        legend_widget = QWidget()
        legend_widget.setFixedHeight(50)  # Match Signal Monitor legend height
        legend_widget.setStyleSheet("background: transparent;")  # Make legend background transparent
        legend_layout = QGridLayout()
        legend_layout.setVerticalSpacing(2)
        
        # Create labels with custom styling
        silent_label = QLabel("Silent:")
        silent_label.setStyleSheet("font-size: 11px;")
        legend_layout.addWidget(silent_label, 1, 1, alignment=Qt.AlignCenter)
        silent_circle = LegendCircle("gray")
        legend_layout.addWidget(silent_circle, 2, 1, alignment=Qt.AlignCenter)

        excitatory_label = QLabel("Excitatory:")
        excitatory_label.setStyleSheet("font-size: 11px;")
        legend_layout.addWidget(excitatory_label, 1, 2, alignment=Qt.AlignCenter)
        excitatory_circle = LegendCircle("red")
        legend_layout.addWidget(excitatory_circle, 2, 2, alignment=Qt.AlignCenter)
        
        inhibitory_label = QLabel("Inhibitory:")
        inhibitory_label.setStyleSheet("font-size: 11px;")
        legend_layout.addWidget(inhibitory_label, 1, 3, alignment=Qt.AlignCenter)
        inhibitory_circle = LegendCircle("blue")
        legend_layout.addWidget(inhibitory_circle, 2, 3, alignment=Qt.AlignCenter)
        
        delay_label = QLabel("Delay:")
        delay_label.setStyleSheet("font-size: 11px;")
        legend_layout.addWidget(delay_label, 1, 4, alignment=Qt.AlignCenter)
        delay_circle = LegendCircle("delay")
        legend_layout.addWidget(delay_circle, 2, 4, alignment=Qt.AlignCenter)
        
        legend_widget.setLayout(legend_layout)
        return legend_widget

    def setEnabled(self, enabled):
        """Override setEnabled to only affect interactive elements, not the legend"""
        # Only disable/enable the interactive container, not the legend
        self.interactive_container.setEnabled(enabled)

    def update_thresholds_from_data(self):
        """Update threshold spinboxes when data is loaded from preset"""
        # Temporarily disconnect signals to avoid triggering data updates
        self.threshold_1.valueChanged.disconnect()
        self.threshold_2.valueChanged.disconnect()
        
        # Update values from data manager
        self.threshold_1.setValue(self.data_manager.get_neuron_threshold(1))
        self.threshold_2.setValue(self.data_manager.get_neuron_threshold(2))
        
        # Reconnect signals
        self.threshold_1.valueChanged.connect(lambda value: self.data_manager.set_neuron_threshold(1, value))
        self.threshold_2.valueChanged.connect(lambda value: self.data_manager.set_neuron_threshold(2, value))

class NeuronWidget(QWidget):
    def __init__(self, neuron_num, data_manager):
        super().__init__()
        self.setFixedSize(225, 200)
        self.data_manager = data_manager
        self.neuron_num = neuron_num 
        self.circle_positions = [
            (12, 38),  # top left
            (127, 38),  # top center
            (241, 38),  # top right
            (65, 105),  # middle left
            (179, 105),  # middle center
            (295, 105),  # middle right
            (120, 172),  # bottom left
            (239, 172),  # bottom center
            (353, 172)   # bottom right
        ]
        
        # Connect to data manager updates to refresh the widget when connectivity changes
        self.data_manager.neuron_connectivity_updated.connect(self.update)


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer = QSvgRenderer(os.path.join("GUI","Graphics", f"RGC_{self.neuron_num}.svg"))
        bounds = QRectF(self.rect())
        renderer.render(painter, bounds)

        """
        Draws the mini 3x3 grid of circles over the neuron.
        """
        viewBox = renderer.viewBoxF()
        painter.setWindow(viewBox.toRect())
        painter.setViewport(self.rect())
        cell_w = 35
        cell_h = 35

        # Draw each cell as a colored circle
        counter = 0
        for i in range(3):
            for j in range(3):
                cell_data = self.data_manager.get_neuron_connectivity_single_val(self.neuron_num, i, j, key=None)
                state = cell_data["state"]
                delay = cell_data["delay"]

                # Choose color
                if state == "excitatory":
                    color = QColor("red")
                elif state == "inhibitory":
                    color = QColor("blue")
                else:
                    color = QColor("gray")

                x = self.circle_positions[counter][0]
                y = self.circle_positions[counter][1]
                radius = min(cell_w, cell_h) / 3
                counter += 1

                painter.setBrush(QBrush(color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(x, y), radius, radius)

                if delay != "None":
                    painter.setPen(QColor("black"))
                    font = painter.font()
                    font.setPointSizeF(radius * 1.5)  # size relative to circle radius
                    painter.setFont(font)
                    
                    # Center text at (x, y)
                    triangle_char = "▲"
                    rect = QRectF(x - radius, y - radius, 2*radius, 2*radius)
                    painter.drawText(rect, Qt.AlignCenter, triangle_char)

    def mousePressEvent(self, event):
        self.show_popup_grid()

    def show_popup_grid(self):
        pop = GridPopupDialog(self.neuron_num, self.data_manager, parent=self)    
        pop.exec_()
           

class GridPopupDialog(QDialog):
    def __init__(self, neuron_num, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.neuron_num = neuron_num
        self.setWindowFlags(Qt.Popup)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"RGC {self.neuron_num} Connectivity"), alignment=Qt.AlignCenter)
        grid_layout = QGridLayout()
        
        self.cell_widgets = []
        
        for row in range(3):
            row_widgets = []
            for col in range(3):
                cell = ConnectivityUnit(self.data_manager, neuron_num, row, col)
                row_widgets.append(cell)
                grid_layout.addWidget(cell, row, col)
            self.cell_widgets.append(row_widgets)

        layout.addLayout(grid_layout)
        self.setLayout(layout)

class ConnectivityUnit(QWidget):
    def __init__(self, data_manager, neuron_num, row, col):
        super().__init__()
        self.data_manager = data_manager
        self.neuron_num = neuron_num
        self.row = row
        self.col = col
        self.setFixedSize(125,110)

        # Polarity Button
        self.polarity_btn = PlusMinusButton()
        self.polarity_btn.clicked.connect(self.update_state)
        self.polarity_btn.state = self.data_manager.get_neuron_connectivity_single_val(self.neuron_num, self.row, self.col, key="state")
        self.polarity_btn.update_style()


        self.delay_slider = QSlider(Qt.Horizontal)
        self.delay_slider.setFixedHeight(25)
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
        
        # Create slider
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(3)
        self.delay_slider.setTickPosition(QSlider.TicksBelow)
        self.delay_slider.setTickInterval(1)
        self.delay_slider.setSingleStep(1)
        self.delay_slider.setPageStep(1)
        self.delay_slider.setValue(self.delay_map_str_int[self.data_manager.get_neuron_connectivity_single_val(self.neuron_num, self.row, self.col, key="delay")])  # Default to "None"
        self.delay_slider.valueChanged.connect(self.update_connectivity)

        # Layouts
        toggle_btns_layout = QHBoxLayout()
        toggle_btns_layout.addWidget(self.polarity_btn)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay:"))
        delay_layout.addWidget(self.delay_slider)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(toggle_btns_layout)
        layout.addLayout(delay_layout)

        self.setLayout(layout)

        # Configure visual state settings upon initialization
        self.update_state()

    def update_state(self):
        state = self.polarity_btn.state
        if state == "off":
            self.delay_slider.setValue(0)
            self.delay_slider.setEnabled(False)
        else:
            self.delay_slider.setEnabled(True)


        self.update_connectivity()

    def update_connectivity(self):
        data_dict =  {"state": self.polarity_btn.state, "delay": self.delay_map_int_str[self.delay_slider.value()]}
        self.data_manager.set_neuron_connectivity_single_dict(self.neuron_num, self.row, self.col, data_dict)


class PlusMinusButton(QPushButton):
    def __init__(self):
        super().__init__()
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
            self.setStyleSheet("""
                QPushButton {
                    background-color: gray;
                    border-radius: 15px;
                }
            """)
        elif self.state == "excitatory":
            self.setText("+")
            self.setStyleSheet("""
                QPushButton {
                    background-color: red;
                    color: white;
                    font-weight: bold;
                    border-radius: 15px;
                }
            """)
        else:
            self.setText("−")
            self.setStyleSheet("""
                QPushButton {
                    background-color: blue;
                    color: white;
                    font-weight: bold;
                    border-radius: 15px;
                }
            """)

