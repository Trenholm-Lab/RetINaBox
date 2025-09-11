from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.QtGui import QFontDatabase, QColor
from PyQt5.QtWidgets import *
from data_manager import *
from interaction_manager import *
from PyQt5.QtSvg import QSvgWidget
from graphing_manager import *
from gpio_manager import setup_gpio_system, cleanup_gpio_system
from presets_manager import PresetOpenButton, PresetSaveButton 
import os 
import json
import numpy as np
import subprocess
from discovery_mode import *
from styles import * 
from block_breaker import BlockBreakerGameTabWidget


class HomeWindow(QMainWindow):
    """
    Home window appears upon startup and allows selection of application mode
    """
    def __init__(self):
        super().__init__()
        self.load_fonts()
        self.colors = [] # list of 8 colors 
        self.setFixedSize(QSize(500, 650))
        self.setStyleSheet(f"background-color: {COLORS['white']};")  # Set a light background color
        self.central_widget = QWidget()
        self.central_layout = QVBoxLayout()

        welcome_label_layout = QVBoxLayout()
        welcome_label_layout.setSpacing(10)
        welcome_label_1 = QLabel("Welcome to")
        welcome_label_1.setFixedHeight(30)
        welcome_label_1.setStyleSheet(f"font-family: {FONTS['family']}; font-size: {FONTS['sizes']['medium']}px; font-weight: {FONTS['weights']['regular']}; color: {COLORS['black']};")
        welcome_label_layout.addWidget(welcome_label_1, alignment=Qt.AlignHCenter)
        
        welcome_label_2 = QLabel("RetINaBox")
        welcome_label_2.setFixedHeight(40)
        welcome_label_2.setStyleSheet(f"font-family: {FONTS['family']}; font-size: {FONTS['sizes']['large']}px; font-weight: {FONTS['weights']['extraBold']}; color: {COLORS['black']};")
        welcome_label_layout.addWidget(welcome_label_2, alignment=Qt.AlignHCenter)
        self.central_layout.addLayout(welcome_label_layout)

        logo_svg = QSvgWidget(os.path.join("GUI", "Graphics", "Logo_noText.svg"))
        logo_svg.setFixedSize(300, 300)  # Set a fixed size for the logo
        self.central_layout.addWidget(logo_svg, alignment=Qt.AlignHCenter)

        holder_layout = QVBoxLayout()
        holder_layout.setSpacing(30)
        self.retinaLab_button = QPushButton("Enter The Lab")
        self.retinaLab_button.setStyleSheet(BUTTON_STYLES['secondary'])
        self.retinaLab_button.clicked.connect(self.enter_retinaLab_mode)
        self.retinaLab_button.setFixedSize(145, 35)
        holder_layout.addWidget(self.retinaLab_button, alignment=Qt.AlignHCenter)

        button_layout = QHBoxLayout()
        self.manual_button = QPushButton("User Manual")
        self.manual_button.setStyleSheet(BUTTON_STYLES['third'])
        self.manual_button.setFixedSize(100, 30)
        self.manual_button.clicked.connect(lambda: open_manual(self))

        self.lesson_button = QPushButton("Lesson Plan")
        self.lesson_button.setStyleSheet(BUTTON_STYLES['third'])
        self.lesson_button.setFixedSize(100, 30)
        button_layout.addWidget(self.manual_button)
        button_layout.addWidget(self.lesson_button)
        holder_layout.addLayout(button_layout)
        self.lesson_button.clicked.connect(lambda: open_lesson_plan(self))

        self.central_layout.addLayout(holder_layout)
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

    def load_fonts(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path_to_fonts = os.path.join(script_dir, "Graphics", "Asap", "static")
        families = []
        for filename in os.listdir(path_to_fonts):
            if filename.lower().endswith(".ttf"):
                font_path = os.path.join(path_to_fonts, filename)
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id == -1:
                    #print(f"Failed to load {filename}")
                    continue
                else:
                    fams = QFontDatabase.applicationFontFamilies(font_id)
                    families.extend(fams)
                    #print(f"Loaded {filename}: {fams}")
        return list(set(families))  # unique families

    def enter_retinaLab_mode(self):
        self.main_window = RetinaLabWindow()
        self.main_window.show()
        self.close()
    
    def enter_experiment_mode(self):
          # Import from the correct file
        self.main_window = ExperimentWindow() 
        self.main_window.show()
        self.close()

class RetinaLabWindow(QMainWindow):
    """
    Main window class contains the structure of the GUI application.
    """
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("RetINaBox") 
        self.setFixedSize(QSize(1000,750))  
        self.setStyleSheet(f"background-color: {COLORS['white']}; font-family: {FONTS['family']}; font-weight: {FONTS['weights']['medium']};")
        self.setWindowIcon(QIcon(os.path.join("GUI", "Graphics", "Logo_noText.svg")))
        
        # create a central data object to store and access global data important for user interaction and GUI function
        self.data_manager = DataManager()
        
        # Use the setup function from gpio_manager
        self.gpio_interface, self.gpio_worker, self.gpio_thread = setup_gpio_system(self.data_manager)
        
        # Start the thread if GPIO system was successfully created
        if self.gpio_thread:
            self.gpio_thread.start()
            #print("GPIO worker thread successfully started")
        
        # Initialize live_graph worker for data processing
        # Use the setup function from live_grapher - pass gpio_worker for signal connection
        self.live_graph_worker, self.live_graph_thread = setup_live_graph_system(self.data_manager)
        
        # Start the thread if live_graph system was successfully created
        if self.live_graph_thread:
            self.live_graph_thread.start()
            #print("live_graph worker thread successfully started")

        # set up main elements of the MainWindow 
        self.setup_central_window()     
        self.setup_toolbar()

    def setup_toolbar(self):
        self.toolbar = QToolBar("My Toolbar")
        self.toolbar.setStyleSheet(TOOLBARS['retinaLab'])
        
        # Fix toolbar to top and make it non-movable
        self.toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Create separate Open and Save buttons instead of combined Presets button
        # Pass parent=self to ensure proper parent relationship
        open_button = PresetOpenButton(self.data_manager)
        open_button.setParent(self.toolbar)
        save_button = PresetSaveButton(self.data_manager)
        save_button.setParent(self.toolbar)
        manual_button = ManualToolButton()
        manual_button.setParent(self.toolbar)
        outputs_button = LessonsButton(self.data_manager)  # Pass data_manager directly
        outputs_button.setParent(self.toolbar)


        # Apply toolbar button styling to all buttons
        open_button.setStyleSheet(TOOLBAR_BUTTON_STYLES['default'])
        save_button.setStyleSheet(TOOLBAR_BUTTON_STYLES['default'])
        manual_button.setStyleSheet(TOOLBAR_BUTTON_STYLES['default'])
        outputs_button.setStyleSheet(TOOLBAR_BUTTON_STYLES['default'])

        self.toolbar.addWidget(manual_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(open_button)
        self.toolbar.addWidget(save_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(outputs_button)
        self.toolbar.addSeparator()
            

    def setup_central_window(self):
        # Create tab widget as central widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Set tab position to align tabs to the left
        self.tab_widget.tabBar().setExpanding(False)
        
        # Apply custom styling to make tabs look better
        self.tab_widget.setStyleSheet(TAB_STYLES['default'])
        
        # Create the main RetINa Lab tab content
        self.create_main_lab_tab()
        
        # Set tab widget as central widget
        self.setCentralWidget(self.tab_widget)
        return 0

    def create_main_lab_tab(self):
        """Create the main RetINa Lab tab with all the original content"""
        # manager widgets  
        self.visual_stim_manager = VisualStimManager(self.data_manager)
        self.connectivity_manager = ConnectivityManager(self.data_manager)
        self.data_manager.stim_running_updated.connect(lambda: self.connectivity_manager.setEnabled(not self.data_manager.stim_running))
        self.live_graph_widget = LiveGrapherWidget(self.data_manager, self.live_graph_worker, self.live_graph_thread)

        main_lab_widget = QWidget()
        central_layout = QHBoxLayout()
        central_layout.setSpacing(10)
        central_layout.setContentsMargins(10, 10, 10, 10)

        central_layout.addWidget(self.visual_stim_manager, stretch=0)  
        central_layout.addWidget(self.connectivity_manager, stretch=0)  
        central_layout.addWidget(self.live_graph_widget, stretch=1) 

        main_lab_widget.setLayout(central_layout)
        
        # Add the main lab tab (this tab cannot be closed)
        self.tab_widget.addTab(main_lab_widget, "RetINaBox Lab")
        
        # Remove close button from the main tab only
        self.update_tab_close_buttons()
        
    def update_tab_close_buttons(self):
        """Update close button visibility for all tabs"""
        # Remove close button from the main tab (index 0) only
        self.tab_widget.tabBar().setTabButton(0, self.tab_widget.tabBar().RightSide, None)
        self.tab_widget.tabBar().setTabButton(0, self.tab_widget.tabBar().LeftSide, None)
        
    def _handle_tab_click(self, index):
        """Handle clicks on tab bar - prevent switching to disabled tabs"""
        if not self.tab_widget.isTabEnabled(index):
            # Show message explaining why tab is disabled
            QMessageBox.information(
                self, 
                "Tab Disabled",
                "The main RetINaBox Lab is disabled while Discovery Mode is active.\n\n"
                "Please close the Discovery Mode tab first to return to the lab."
            )
            
    def close_tab(self, index):
        """Close tab at given index (but not the main lab tab)"""
        if index > 0:  # Don't close the main lab tab (index 0)
            # Check if it's Discovery Mode tab and show confirmation
            if self.tab_widget.tabText(index) == "Discovery Mode":
                # Show confirmation dialog
                reply = QMessageBox.question(
                    self, 
                    'Close Discovery Mode', 
                    'Are you sure you want to close Discovery Mode?\n\n'
                    'Your progress will be lost.',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No  # Default to No for safety
                )
                
                if reply == QMessageBox.Yes:
                    self.cleanup_discovery_mode_tab(index)
                    self.tab_widget.removeTab(index)
                # If No, do nothing - tab stays open
            elif self.tab_widget.tabText(index) == "Block Breaker":
                # Close Block Breaker directly without confirmation
                self.cleanup_block_breaker_tab(index)
                self.tab_widget.removeTab(index)
            else:
                # For other tabs, close normally
                self.tab_widget.removeTab(index)
        # If somehow the close signal is triggered for the main tab, ignore it
    
    def cleanup_discovery_mode_tab(self, tab_index):
        """Clean up Discovery Mode when closing the tab"""
        try:
            discovery_widget = self.tab_widget.widget(tab_index)
            if discovery_widget and hasattr(discovery_widget, 'cleanup_discovery_mode'):
                discovery_widget.cleanup_discovery_mode()
                
            # Re-enable main tab when Discovery Mode is closed
            self.tab_widget.setTabEnabled(0, True)
            self.tab_widget.tabBar().setTabTextColor(0, QColor(0, 0, 0))  # Reset text color
        except Exception as e:
            print(f"Error cleaning up Discovery Mode: {e}")
    
    def cleanup_block_breaker_tab(self, tab_index):
        """Clean up Block Breaker when closing the tab"""
        try:
            block_breaker_widget = self.tab_widget.widget(tab_index)
            if block_breaker_widget and hasattr(block_breaker_widget, 'game_widget'):
                block_breaker_widget.game_widget.closing = True
                block_breaker_widget.game_widget.game_active = False
                block_breaker_widget.game_widget.game_timer.stop()
            
            # Turn off all LEDs when Block Breaker tab is closed
            if block_breaker_widget and hasattr(block_breaker_widget, 'data_manager') and block_breaker_widget.data_manager:
                for row in range(3):
                    for col in range(3):
                        block_breaker_widget.data_manager.set_selected_stim_state(row, col, False)
                        block_breaker_widget.data_manager.set_activated_stim_state(row, col, False)
                block_breaker_widget.data_manager.set_stim_running(False)
                
        except Exception as e:
            print(f"Error cleaning up Block Breaker: {e}")
            
    def add_code_breaker_tab(self):
        """Add Code Breaker as a new tab"""
        # Check if Code Breaker tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Code Breaker":
                self.tab_widget.setCurrentIndex(i)  # Switch to existing tab
                return
        
        # Import here to avoid circular imports
        from code_breaker import CodeBreakerWidget
        
        # Create the Code Breaker widget (modified to be a widget instead of dialog)
        code_breaker_widget = CodeBreakerWidget(self)
        
        # Add as new tab
        tab_index = self.tab_widget.addTab(code_breaker_widget, "Code Breaker")
        self.tab_widget.setCurrentIndex(tab_index)  # Switch to the new tab
        
        # Ensure the main tab still doesn't have a close button after adding new tabs
        self.update_tab_close_buttons()

    def add_discovery_mode_tab(self):
        """Add Discovery Mode as a new tab"""
        # Check if Discovery Mode tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Discovery Mode":
                self.tab_widget.setCurrentIndex(i)  # Switch to existing tab
                return
        
        # Import here to avoid circular imports
        from discovery_mode import DiscoveryModeWidget
        
        # Create the Discovery Mode widget
        discovery_mode_widget = DiscoveryModeWidget(self)
        
        # Add as new tab
        tab_index = self.tab_widget.addTab(discovery_mode_widget, "Discovery Mode")
        self.tab_widget.setCurrentIndex(tab_index)  # Switch to the new tab
        
        # Disable main tab while discovery mode is active
        self.tab_widget.setTabEnabled(0, False)
        self.tab_widget.tabBar().setTabTextColor(0, QColor(128, 128, 128))  # Gray out text
        
        # Connect to tabBarClicked to prevent clicking on disabled tabs
        if not hasattr(self, '_tab_click_connected'):
            self.tab_widget.tabBarClicked.connect(self._handle_tab_click)
            self._tab_click_connected = True
        
        # Ensure the main tab still doesn't have a close button after adding new tabs
        self.update_tab_close_buttons()

    def add_block_breaker_tab(self):
        """Add Block Breaker game as a new tab"""
        # Check if Block Breaker tab already exists
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == "Block Breaker":
                self.tab_widget.setCurrentIndex(i)  # Switch to existing tab
                return
        
        # Create the Block Breaker widget
        block_breaker_widget = BlockBreakerGameTabWidget(self.data_manager, self)
        
        # Add as new tab
        tab_index = self.tab_widget.addTab(block_breaker_widget, "Block Breaker")
        self.tab_widget.setCurrentIndex(tab_index)  # Switch to the new tab
        
        # Ensure the main tab still doesn't have a close button after adding new tabs
        self.update_tab_close_buttons()

    def closeEvent(self, event):
        """Clean up GPIO and live_graph resources when closing the application"""
        if hasattr(self, 'gpio_worker') and hasattr(self, 'gpio_thread') and hasattr(self, 'gpio_interface'):
            cleanup_gpio_system(self.gpio_worker, self.gpio_thread, self.gpio_interface)
        
        if hasattr(self, 'live_graph_worker') and hasattr(self, 'live_graph_thread'):
            cleanup_live_graph_system(self.live_graph_worker, self.live_graph_thread)
        
        event.accept()


    
class LessonsButton(QToolButton):
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager  # Store the passed data_manager directly
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setMinimumWidth(60)
        self.setText("Lessons")
        
        # Track game windows to prevent multiple instances (only for games that still use windows)
        self.game_window = None
        
        # Load activity presets data
        self.activity_presets = self.load_activity_presets()

        # Create main menu with proper parent
        outputs_menu = QMenu(self)
        outputs_menu.setToolTipsVisible(False)
        outputs_menu.setStyleSheet(MENU_STYLES['default'])

        # Add Lesson Plan PDF action
        outputs_menu.addAction("Lesson Plan PDF", lambda: open_lesson_plan(self))
        outputs_menu.addSeparator()
        
        # Create lesson submenus dynamically from activity presets
        self.create_lesson_menus(outputs_menu)
        
        # Connect the menu to the button
        self.setMenu(outputs_menu)
        self.setPopupMode(QToolButton.InstantPopup)

    def load_activity_presets(self):
        """Load activity presets from the JSON file"""
        try:
            json_path = os.path.join("GUI", ".default_code", ".default_activity_presets.json")
            with open(json_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading activity presets: {e}")
            return {}
    
    def create_lesson_menus(self, parent_menu):
        """Create lesson submenus dynamically from activity presets data"""
        if not self.activity_presets:
            return
        
        for lesson_name, activities in self.activity_presets.items():
            # Create lesson submenu
            lesson_menu = QMenu(lesson_name.replace("_", " ").title(), parent_menu)
            lesson_menu.setStyleSheet(MENU_STYLES['default'])
            
            # Add activity presets for this lesson
            for activity_name in activities.keys():
                # Convert snake_case to readable format
                display_name = activity_name.replace("_", " ").title()
                
                # Add action (placeholder for now - no functionality connected)
                action = lesson_menu.addAction(display_name)
                # Store the original keys for later use
                action.setData({'lesson': lesson_name, 'activity': activity_name})
                # Connect to placeholder method for now
                action.triggered.connect(lambda checked, l=lesson_name, a=activity_name: 
                                       self.load_activity_preset(l, a))
            
            # Add separator before games/modes if this lesson has them
            if lesson_name == "Lesson_1":
                lesson_menu.addSeparator()
                lesson_menu.addAction("Launch Code Breaker", self.launch_code_breaker)
            elif lesson_name == "Lesson_3":
                lesson_menu.addSeparator()
                lesson_menu.addAction("Launch Block Breaker", self.launch_block_game)
            
            # Add the lesson menu to parent
            parent_menu.addMenu(lesson_menu)
        
        # Add Discovery Mode as separate item (not tied to specific lesson in presets)
        discovery_menu = QMenu("Lesson 4", parent_menu)
        discovery_menu.setStyleSheet(MENU_STYLES['default'])
        discovery_menu.addAction("Launch Discovery Mode", self.launch_discovery_mode)
        parent_menu.addMenu(discovery_menu)
    
    def load_activity_preset(self, lesson_name, activity_name):
        """Load activity preset and update the data manager"""
        print(f"Loading preset: {lesson_name} -> {activity_name}")
        activity_data_copy = self.activity_presets[lesson_name][activity_name].copy() 
        for rgc_key in ['rgc1', 'rgc2']:
            if rgc_key in activity_data_copy.keys():
                activity_data_copy[rgc_key]['connectivity'] = np.array(activity_data_copy[rgc_key]['connectivity']).reshape(3,3)
            else: # set neuron connectivity to default off if not specified
                activity_data_copy[rgc_key] = {"connectivity": self.data_manager.set_default_neuron_connectivity(), "threshold": 1}
        
        # Update data_manager with loaded data
        self.data_manager.neuron_connectivity_data = activity_data_copy
                
        # Emit the signal to update GUI
        self.data_manager.neuron_connectivity_updated.emit()

    def get_main_window(self):
        """Helper method to safely get the main window"""
        # Walk up the parent hierarchy to find the RetinaLabWindow
        widget = self
        while widget:
            if isinstance(widget, RetinaLabWindow):
                return widget
            widget = widget.parent()
        return None

    def launch_block_game(self):
        """Launch the block breaker game as a tab"""
        try:
            # Get the main window safely
            main_window = self.get_main_window()
            if not main_window:
                QMessageBox.critical(self, "Error", "Could not find main window")
                return
            
            # Add Block Breaker as a tab instead of separate window
            main_window.add_block_breaker_tab()
            
        except Exception as e:
            # Show error message if game fails to launch
            QMessageBox.critical(self, "Game Launch Error", 
                               f"Failed to launch Block Breaker game:\n{str(e)}")
            print(f"Error launching Block Breaker game: {e}")

    def launch_code_breaker(self):
        try:
            # Get the main window safely
            main_window = self.get_main_window()
            if not main_window:
                QMessageBox.critical(self, "Error", "Could not find main window")
                return
            
            # Add Code Breaker as a new tab instead of opening a new window
            main_window.add_code_breaker_tab()
            
            
        except Exception as e:
            # Show error message if Code Breaker fails to launch
            QMessageBox.critical(self, "Launch Error", 
                               f"Failed to launch Code Breaker:\n{str(e)}")
            print(f"Error launching Code Breaker: {e}")

    def launch_discovery_mode(self):
        """Launch Discovery Mode as a tab"""
        try:
            # Get the main window safely
            main_window = self.get_main_window()
            if not main_window:
                QMessageBox.critical(self, "Error", "Could not find main window")
                return
            
            # Add Discovery Mode as a new tab instead of opening a new window
            main_window.add_discovery_mode_tab()
            
            
        except Exception as e:
            # Show error message if discovery mode fails to launch
            QMessageBox.critical(self, "Launch Error", 
                               f"Failed to launch Discovery Mode:\n{str(e)}")
            print(f"Error launching Discovery Mode: {e}")

def open_lesson_plan(parent):
        """Open the lesson plan PDF in the default PDF viewer"""
        abs_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__))[:-4], "Lesson_plan.pdf")

        if os.path.exists(abs_pdf_path):
            try:
                # Use subprocess to open PDF and suppress stderr warnings
                if os.name == 'posix':  # Linux/macOS
                    subprocess.Popen(['xdg-open', abs_pdf_path], 
                                   stderr=subprocess.DEVNULL, 
                                   stdout=subprocess.DEVNULL)
                else:  # Windows
                    subprocess.Popen(['start', abs_pdf_path], 
                                   shell=True,
                                   stderr=subprocess.DEVNULL, 
                                   stdout=subprocess.DEVNULL)
            except Exception as e:
                # Fallback to QDesktopServices if subprocess fails
                try:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(abs_pdf_path))
                except Exception as e2:
                    QMessageBox.critical(parent, "Error", f"Failed to open lesson plan:\n{str(e2)}")
        else:
            # Show message if lesson plan not found
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Lesson plan Not Found")
            msg.setText("Lesson plan PDF not found")
            msg.setInformativeText(f"Please place 'Lesson_plan.pdf' in the GUI folder:\n{os.path.abspath('GUI')}")
            msg.exec_()      
        
class ManualToolButton(QToolButton):
    def __init__(self):
        super().__init__()
        self.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.setMinimumWidth(60)
        self.setText("User Manual")
        self.clicked.connect(lambda: open_manual(self))

def open_manual(parent):
    """Open the manual PDF in the default PDF viewer"""
    abs_pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__))[:-4], "User_manual.pdf")

    if os.path.exists(abs_pdf_path):
        try:
            # Use subprocess to open PDF and suppress stderr warnings
            if os.name == 'posix':  # Linux/macOS
                subprocess.Popen(['xdg-open', abs_pdf_path], 
                               stderr=subprocess.DEVNULL, 
                               stdout=subprocess.DEVNULL)
            else:  # Windows
                subprocess.Popen(['start', abs_pdf_path], 
                               shell=True,
                               stderr=subprocess.DEVNULL, 
                               stdout=subprocess.DEVNULL)
        except Exception as e:
            # Fallback to QDesktopServices if subprocess fails
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(abs_pdf_path))
            except Exception as e2:
                QMessageBox.critical(parent, "Error", f"Failed to open manual:\n{str(e2)}")
    else:
        # Show message if manual not found
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Manual Not Found")
        msg.setText("Manual PDF not found")
        msg.setInformativeText(f"Please place 'User_manual.pdf' in the Retina-in-a-box folder:\n{os.path.abspath('GUI')}")
        
