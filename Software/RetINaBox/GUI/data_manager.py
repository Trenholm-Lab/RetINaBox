from PyQt5.QtCore import QObject, pyqtSignal 
import numpy as np
import json
import time
from collections import deque



class DataManager(QObject):
    """
    Object contains all global data to be shared across the entire RetINaBox GUI. 
    """
    mode_changed = pyqtSignal(str)
    buffer_data_ready = pyqtSignal(dict)
    neuron_connectivity_updated = pyqtSignal()
    selected_LEDs_updated = pyqtSignal()
    activated_LEDs_updated = pyqtSignal(np.ndarray)
    rgc_leds_on_updated = pyqtSignal(np.ndarray)
    current_stim_mode_updated = pyqtSignal(str)
    current_stim_speed_updated = pyqtSignal(int)
    current_stim_direction_updated = pyqtSignal(str)
    stim_running_updated = pyqtSignal(bool)
    photodiode_signals_updated = pyqtSignal(np.ndarray)


    def __init__(self):
        super().__init__()

        # Graphing data
        self.tau_ms = 25 # neuron dynamics time constant
        self.dt_ms = 25 # raw sampling interval 
        self.duration_s = 10 # duration of graphing buffer in seconds
        self.interval_ms = 25 # plotting interval between samples in ms 

        self.speed_ms_interval = [500, 300, 100] # ms interval for slow, medium, fast speeds
        self.graphing_delay_to_ms = {"None": 0.0, "short": 100.0, "medium": 300.0, "long": 500.0}

        self.rgc_leds_state = [0, 0] # 0 = off, 1 = on

        # Global state for RGC neurons 
        self.neuron_connectivity_data = {
            "rgc1": {"connectivity": self.set_default_neuron_connectivity(),
                     "threshold": 1},
            "rgc2": {"connectivity": self.set_default_neuron_connectivity(),
                     "threshold": 1}
        }
        
        
        # Global state for visual stim
        self.selected_stim_states = [[False, False, False],
                                     [False, False, False],
                                     [False, False, False]]
        self.activated_stim_states = [[False, False, False],
                                      [False, False, False],
                                      [False, False, False]]
        
        self.current_stim_mode = "Static"
        self.current_stim_speed = "Medium"
        self.current_stim_direction = "Right"
    
        self.stim_running = False

        self.speed_map = {
            "Slow": 0,
            "Medium": 1,
            "Fast": 2
        }

        # GPIO/Simulation Mode Toggle
        # GPIO availability will be set by GPIO manager if hardware is available and setup succeeds
        self.GPIO_AVAILABLE = False  # Set to True by GPIO manager if successful
        
        # Initialize photodiode signals - will be updated by set_gpio_mode() after GPIO setup
        self.photodiode_signals = [[0.0, 0.0, 0.0],
                                   [0.0, 0.0, 0.0],
                                   [0.0, 0.0, 0.0]]

        # Initialize deque with maxlen = buffer_size to automatically discard oldest when full
        self.raw_response_buffer_queue = self.initialize_buffer() # shape T,9 
        self.activated_LED_buffer_queue = self.initialize_buffer() # shape T,9

        self.computed_photodiode_response_buffer_queue = self.initialize_graphing_buffer(2, 9) # shape T,2,9
        self.computed_rgc_response_buffer_queue = self.initialize_graphing_buffer(2, 1) # shape T,2,1

        # Connect internal signal to ensure LED states are always added to buffer when they change
        self.activated_LEDs_updated.connect(self.add_activated_LED_states_to_buffer)
        
        # Emit initial buffer data
        self.emit_buffer_data()

        # Discovery mode stimulus selection 
        self.DM_connectivity = []
        
        # Discovery Mode connectivity data - separate from main GUI
        self.DM_connectivity_data = {
            "rgc1": {"connectivity": self.set_default_neuron_connectivity(),
                     "threshold": 1},
            "rgc2": {"connectivity": self.set_default_neuron_connectivity(),
                     "threshold": 1}
        }
        
        # Data mode for connectivity selection ("lab" or "experiment")
        self.data_mode = "lab"
        
        # Live graphing control
        self.live_graphing_enabled = True  # Disabled by default for main GUI
        self.discovery_live_graphing_enabled = True  # Always enabled for Discovery Mode
    
    '''
    Experiment functions
    '''
    def set_leaderboard_participation(self, include_leaderboard):
        """Set whether the player wants to be on the leaderboard"""
        self.include_leaderboard = include_leaderboard

    def get_leaderboard_participation(self):
        """Get whether the player wants to be on the leaderboard"""
        return getattr(self, 'include_leaderboard', False)

    def set_name(self, name):
        """Set the player name"""
        self.player_name = name

    def get_name(self):
        """Get the player name"""
        return getattr(self, 'player_name', 'Guest')

    def set_mode(self, mode):
        """Set the current mode of the DataManager"""
        self.data_mode = mode
        self.mode = mode
        if self.mode == "lab":
            self.reset_graphing_buffers()

            self.set_stim_running(False)            
            self.DM_stim = np.array([False,False,False,False,False,False,False,False,False])
            for row in range(3):
                for col in range(3):
                    self.set_selected_stim_state(row, col, False)
            
            # Reset connectivity to default (all off, no delays)
            self.reset_all_connectivity()
            self.set_discovery_live_graphing_enabled(False)
            self.set_live_graphing_enabled(True)
            
        elif self.mode == "experiment":
            self.reset_graphing_buffers()

            # turn on all LEDs 
            for row in range(3):
                for col in range(3):
                    self.set_selected_stim_state(row, col, True)
                    self.set_activated_stim_state(row, col, True)
            self.set_current_stim_mode("Static")
            self.current_stim_mode_updated.emit("Static")
            self.set_stim_running(True)
            self.DM_stim = np.array([False,False,False,False,False,False,False,False,False])
            
            # Reset connectivity to default (all off, no delays)
            self.reset_all_connectivity()
            self.set_discovery_live_graphing_enabled(True)
            self.set_live_graphing_enabled(False)
        
        # Emit the mode_changed signal so connected widgets can update
        self.mode_changed.emit(mode)
    """
    Graphing functions
    """
    def reset_graphing_buffers(self):
        """Reset all graphing buffers to zero values"""
        # Reinitialize all buffers with zeros
        self.raw_response_buffer_queue = self.initialize_buffer()
        self.activated_LED_buffer_queue = self.initialize_buffer()
        self.computed_photodiode_response_buffer_queue = self.initialize_graphing_buffer(2, 9)
        self.computed_rgc_response_buffer_queue = self.initialize_graphing_buffer(2, 1)
        
        # Emit initial buffer data to refresh graphs
        self.emit_buffer_data()


    def initialize_graphing_buffer(self, rgc_num, curves_per_cell):
        buffer_size = int(self.duration_s * 1000 / self.interval_ms)
        
        # Create deque with pre-allocated zero arrays
        buffer_queue = deque(maxlen=buffer_size)
        
        # Create all zero states at once using numpy
        zero_states = np.zeros((buffer_size, rgc_num, curves_per_cell))
        
        # Add each row as a separate array to the deque
        for i in range(buffer_size):
            buffer_queue.append(zero_states[i])
        
        return buffer_queue  # shape of buffer_queue = T, 2, 9 or T,2,1
    
    def initialize_buffer(self):
        buffer_size = int(self.duration_s * 1000 / self.interval_ms)
        
        buffer_queue = deque(maxlen=buffer_size)
        
        # Create all zero states at once 
        zero_states = np.zeros((buffer_size, 9))
        
        # Add each row as a separate array to the deque
        for i in range(buffer_size):
            buffer_queue.append(zero_states[i])
        
        return buffer_queue

    def add_photodiode_states_to_buffer(self, photodiode_states):
        flattened_response_vector = np.array(photodiode_states).flatten()
        self.raw_response_buffer_queue.append(flattened_response_vector) 

        # Emit signal for thread-safe communication to graph worker
        self.photodiode_signals_updated.emit(np.array(photodiode_states))  
    
    def add_activated_LED_states_to_buffer(self):
        flattened_activated_vector = np.array(self.get_activated_stim_states()).flatten()
        self.activated_LED_buffer_queue.append(flattened_activated_vector)
        # Emit updated buffer data after LED buffer changes
        self.emit_latest_data()

    def emit_latest_data(self):
        """Emit both latest data and full buffer data for optimal processing"""
        # Only emit if live graphing is enabled and there are active listeners and we have data
        if (self.get_live_graphing_enabled() and 
            self.receivers(self.buffer_data_ready) > 0 and 
            len(self.activated_LED_buffer_queue) > 0):
            # For the live graph worker, emit full buffer arrays for preprocessing
            # For backward compatibility, also emit latest single data point
            buffer_data = {
                'raw_photodiode': np.array(list(self.raw_response_buffer_queue)),
                'computed_photodiode_responses': np.array(list(self.computed_photodiode_response_buffer_queue)),
                'computed_rgc_responses': np.array(list(self.computed_rgc_response_buffer_queue)),
                'timestamp': time.time(),  
                # Keep latest single data for backward compatibility
                'latest_raw_photodiode': self.raw_response_buffer_queue[-1].copy(),
                'latest_computed_photodiode_responses': self.computed_photodiode_response_buffer_queue[-1].copy(),
                'latest_computed_rgc_responses': self.computed_rgc_response_buffer_queue[-1].copy()
            }
            self.buffer_data_ready.emit(buffer_data)

    def emit_buffer_data(self):
        """Emit full buffer data - only used for initialization or when full data needed"""
        buffer_data = {
            'activated_LEDs': np.array(list(self.activated_LED_buffer_queue)),
            'computed_photodiode_responses': np.array(list(self.computed_photodiode_response_buffer_queue)),
            'computed_rgc_responses': np.array(list(self.computed_rgc_response_buffer_queue))
        }
        self.buffer_data_ready.emit(buffer_data)

    def get_buffer_as_array(self, buffer_str):
        if buffer_str == "raw_photodiode":
            return np.array(list(self.raw_response_buffer_queue))
        elif buffer_str == "activated_LEDs":
            return np.array(list(self.activated_LED_buffer_queue))
        elif buffer_str == "computed_photodiode_responses":
            return np.array(list(self.computed_photodiode_response_buffer_queue))
        elif buffer_str == "computed_rgc_responses":
            return np.array(list(self.computed_rgc_response_buffer_queue))

    """
    Connectivity functions 
    """
    def get_neuron_threshold(self, neuron_num):
        # Use Discovery Mode thresholds when in experiment mode
        if hasattr(self, 'data_mode') and self.data_mode == "experiment":
            return self.DM_connectivity_data[f"rgc{neuron_num}"]["threshold"]
        else:
            return self.neuron_connectivity_data[f"rgc{neuron_num}"]["threshold"]

    def set_neuron_threshold(self, neuron_num, new_threshold):
        self.neuron_connectivity_data[f"rgc{neuron_num}"]["threshold"] = new_threshold
        self.neuron_connectivity_updated.emit()

    def set_default_neuron_connectivity(self):
        self.default_connectivity_dict = {"state": "off", "delay": "None"}
        return [[self.default_connectivity_dict.copy() for _ in range(3)] for _ in range(3)]

    def reset_all_connectivity(self):
        """Reset all neuron connectivity to default state (all off, no delays) and reset thresholds"""
        # Reset connectivity for both RGC neurons
        for neuron_num in [1, 2]:
            # Reset connectivity to default (all off, no delays)
            self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"] = self.set_default_neuron_connectivity()
            
            # Reset threshold to default value
            self.neuron_connectivity_data[f"rgc{neuron_num}"]["threshold"] = 1
        
        # Emit signal to update GUI components
        self.neuron_connectivity_updated.emit()

    def set_neuron_connectivity_single_val(self, neuron_num, row, col, key, value):
        self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"][row][col][key] = value
        self.neuron_connectivity_updated.emit()
    
    def set_neuron_connectivity_single_dict(self, neuron_num, row, col, data_dict):
        self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"][row][col] = data_dict
        self.neuron_connectivity_updated.emit()
    
    def get_neuron_connectivity_single_val(self, neuron_num, row, col, key=None):
        if key == None:
            return self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"][row][col]
        return self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"][row][col][key]
    
    def set_neuron_connectivity_all(self, neuron_num, connectivity_dict):
        self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"] = connectivity_dict
        self.neuron_connectivity_updated.emit()
    
    def load_challenge_connectivity(self, connectivity_array, threshold):
        """
        Load challenge connectivity into DM_connectivity_data for Discovery Mode isolation
        Args:
            connectivity_array: Flat array of 9 connectivity objects from challenge JSON
            threshold: Threshold value from challenge JSON
        """
        # Convert flat array to 3x3 structure
        connectivity_3x3 = np.array(connectivity_array).reshape(3, 3).tolist()
        
        # Load into Discovery Mode data structure instead of main connectivity
        # Make sure to load for both RGC1 and RGC2
        self.DM_connectivity_data["rgc1"]["connectivity"] = connectivity_3x3
        self.DM_connectivity_data["rgc1"]["threshold"] = threshold
        
        # For Discovery Mode, we only use RGC1, but make sure RGC2 has default connectivity
        # This ensures the GPIO worker can compute both without errors
        self.DM_connectivity_data["rgc2"]["connectivity"] = self.set_default_neuron_connectivity()
        self.DM_connectivity_data["rgc2"]["threshold"] = 1
        
        # Force neuron connectivity updated signal to refresh the graphing worker cache
        self.neuron_connectivity_updated.emit()
            
    def get_neuron_connectivity_all(self, neuron_num):
        """Get complete connectivity data for a neuron"""
        return self.neuron_connectivity_data[f"rgc{neuron_num}"]["connectivity"]
    
    def get_all_neuron_connectivity(self):
        """
        Get all neuron connectivity data in one call for performance optimization
        Returns: Dict with structure {neuron_num: {row: {col: connectivity_data}}}
        
        Automatically returns Discovery Mode connectivity when in experiment mode,
        or main GUI connectivity when in lab mode.
        """
        # Use Discovery Mode connectivity when in experiment mode
        if hasattr(self, 'data_mode') and self.data_mode == "experiment":
            source_data = self.DM_connectivity_data
        else:
            source_data = self.neuron_connectivity_data
            
        all_data = {}
        
        for neuron_num in [1, 2]:  # RGC 1 and RGC 2
            all_data[neuron_num] = {}
            for row in range(3):
                all_data[neuron_num][row] = {}
                for col in range(3):
                    all_data[neuron_num][row][col] = source_data[f"rgc{neuron_num}"]["connectivity"][row][col]
        
        return all_data
    
    def check_connectivity_pattern(self, expected_pattern):
        """
        Check if current RGC connectivity matches expected pattern
        
        Args:
            expected_pattern: Dictionary with expected connectivity for each RGC
                             Format: {"rgc1": [[...], [...], [...]], "rgc2": [[...], [...], [...]]}
        
        Returns:
            bool: True if connectivity matches, False otherwise
        """
        if expected_pattern is None:
            return True
        
        for rgc_key in ["rgc1", "rgc2"]:
            if rgc_key in expected_pattern:
                current_connectivity = self.neuron_connectivity_data[rgc_key]["connectivity"]
                expected_connectivity = expected_pattern[rgc_key]
                
                # Compare connectivity patterns
                if current_connectivity != expected_connectivity:
                    return False
        
        return True
    
    """
    Stimulus functions
    """
    def set_selected_stim_state(self, row, col, is_selected):
        self.selected_stim_states[row][col] = is_selected # bool
        self.selected_LEDs_updated.emit()
    
    def get_selected_stim_state(self, row, col):
        return self.selected_stim_states[row][col]
    
    def set_activated_stim_state(self, row, col, is_activated):
        self.activated_stim_states[row][col] = is_activated # bool
        self.activated_LEDs_updated.emit(np.array(self.activated_stim_states).flatten())

    def get_activated_stim_state(self, row, col):
        return self.activated_stim_states[row][col]
    
    def get_activated_stim_states(self):
        """
        Returns: 3x3 numpy array of activated LED states (True/False)
        """
        return np.array(self.activated_stim_states, dtype=bool)

    def set_current_stim_mode(self, mode_str):
        self.current_stim_mode = mode_str
        self.current_stim_mode_updated.emit(mode_str)
    
    def get_current_stim_mode(self):
        return self.current_stim_mode
    
    def set_current_stim_speed(self, speed_str):
        if speed_str != self.current_stim_speed:
            self.current_stim_speed = speed_str
            speed_int = self.speed_map[speed_str]
            self.current_stim_speed_updated.emit(speed_int)
    
    def get_current_stim_speed(self):
        speed_str = self.current_stim_speed
        speed_int = self.speed_map[speed_str]
        return speed_int
    
    def set_current_stim_direction(self, direction_str):
        self.current_stim_direction = direction_str
        self.current_stim_direction_updated.emit(direction_str)
    
    def get_current_stim_direction(self):
        return self.current_stim_direction

    def set_stim_running(self, stim_running_bool): # stim_on = bool
        self.stim_running = stim_running_bool
        self.stim_running_updated.emit(stim_running_bool)
    
    def get_stim_running(self):
        return self.stim_running
    
    """
    GPIO functions
    """ 
    def get_current_photodiode_signal(self):
        """Get current photodiode signals"""
        return self.photodiode_signals
    
    def set_gpio_mode(self, gpio_available):
        """
        Set GPIO availability mode
        gpio_available: bool - True for real GPIO, False for simulation
        """
        self.GPIO_AVAILABLE = gpio_available
        if gpio_available:
            # GPIO mode: keep separate photodiode signals that will be updated by GPIO worker
            self.photodiode_signals = [[0.0, 0.0, 0.0],
                                       [0.0, 0.0, 0.0],
                                       [0.0, 0.0, 0.0]]
        else:
            # Simulation mode: use LED states as fake photodiode signals
            self.photodiode_signals = self.activated_stim_states

    def load_discovery_mode_challenge(self, challenge_file):
        """
        Load a Discovery Mode challenge connectivity into DM_connectivity_data
        This keeps Discovery Mode separate from main GUI connectivity.
        """
        try:
            with open(challenge_file, 'r') as f:
                challenge_data = json.load(f)
            
            # Load challenge connectivity into Discovery Mode data structure
            self.DM_connectivity_data = challenge_data
            
            print(f"Discovery Mode challenge loaded: {challenge_file}")
            return True
            
        except Exception as e:
            print(f"Error loading Discovery Mode challenge: {e}")
            return False
        
    
    def set_live_graphing_enabled(self, enabled):
        """
        Enable or disable live graphing for main GUI
        Discovery Mode has its own separate control
        """
        self.live_graphing_enabled = enabled
        
    def get_live_graphing_enabled(self):
        """
        Get live graphing status based on current context
        Returns Discovery Mode setting when in experiment mode, main GUI setting otherwise
        """
        if hasattr(self, 'data_mode') and self.data_mode == "experiment":
            return self.discovery_live_graphing_enabled
        else:
            return self.live_graphing_enabled
    
    def set_discovery_live_graphing_enabled(self, enabled):
        """
        Enable or disable live graphing specifically for Discovery Mode
        """
        self.discovery_live_graphing_enabled = enabled

