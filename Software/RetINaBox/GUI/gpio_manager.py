from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread, QMetaObject, Qt
import numpy as np 

# lgpio library for Raspberry Pi 5

lgpio = None
GPIO_AVAILABLE = False

def check_lgpio_availability():
    """Check and prepare lgpio system before initialization"""
    global GPIO_AVAILABLE, lgpio
    
    try:
        import lgpio as lgpio_lib
        lgpio = lgpio_lib
        # Test if we can open GPIO chip
        try:
            chip = lgpio.gpiochip_open(0)
            lgpio.gpiochip_close(chip)
            GPIO_AVAILABLE = True
            print("lgpio for GPIO control initialized successfully (Pi 5)")
            return True
        except Exception as e:
            print(f"lgpio available but cannot access GPIO: {e}")
            print("You may need to run: sudo python3 GPIO/gpio_cleanup.py")
            GPIO_AVAILABLE = False
            return False
    except ImportError:
        print("lgpio not available - using simulation mode")
        GPIO_AVAILABLE = False
        return False

# Initialize lgpio availability
check_lgpio_availability()

def setup_gpio_system(data_manager):
    """
    Setup the complete GPIO system with manager, worker, and thread
    Always creates worker for timer functionality - operates in simulation mode if GPIO unavailable
    Returns: (gpio_interface, gpio_worker, gpio_thread) or (None, None, None) if failed
    """
    # Clean up any existing GPIO state first
    if GPIO_AVAILABLE:
        try:
            # Try to clean up any existing GPIO state
            import subprocess
            result = subprocess.run(['sudo', 'pkill', '-f', 'lgpio'], capture_output=True)
            print(f"GPIO cleanup attempt: {result.returncode}")
        except Exception as e:
            print(f"GPIO cleanup warning: {e}")

    data_manager.set_gpio_mode(GPIO_AVAILABLE)
    
    try:
        # Always create GPIO interface and worker - they handle simulation mode internally
        gpio_interface = GPIOInterface(data_manager)
        
        # Create GPIO worker thread
        gpio_thread = QThread()
        gpio_worker = GPIOWorker(gpio_interface)
        
        # Move worker to thread
        gpio_worker.moveToThread(gpio_thread)
        
        # Connect signals
        # When thread starts, start the GPIO worker
        gpio_thread.started.connect(gpio_worker.start_reading)
        
        # Core data flow: GPIO worker processes data and updates buffers directly (every 25ms)
        # Processing now happens directly in GPIO worker - no separate signal needed
        
        # LED state changes: data manager --> GPIO worker (immediate)
        data_manager.activated_LEDs_updated.connect(lambda led_states: gpio_interface.write_stim_leds(led_states.flatten()))

        # RGC response updates: data manager --> GPIO worker (immediate)
        data_manager.rgc_leds_on_updated.connect(lambda rgc_leds_state: gpio_interface.write_rgc_leds(rgc_leds_state))
        
        # Cleanup connections
        gpio_worker.finished.connect(gpio_thread.quit)
        gpio_worker.finished.connect(gpio_worker.deleteLater)
        gpio_thread.finished.connect(gpio_thread.deleteLater)
        
        print("GPIO system setup successful")   
        return gpio_interface, gpio_worker, gpio_thread
        
    except Exception as e:
        print(f"Failed to initialize GPIO system: {e}")
        print("Falling back to simulation mode")
        data_manager.set_gpio_mode(False)
        return None, None, None

def cleanup_gpio_system(gpio_worker, gpio_thread, gpio_interface):
    """
    Clean up GPIO system resources - thread-safe cleanup
    """
    if gpio_worker and gpio_thread:
        print("Cleaning up GPIO resources...")
        
        if gpio_thread.isRunning():
            # Connect finished signal to quit thread
            gpio_worker.finished.connect(gpio_thread.quit)
            
            # Emit signal to stop worker from its own thread
            gpio_worker.stop_requested.emit()
            
            # Wait for thread to finish
            if not gpio_thread.wait(3000):
                print("Warning: GPIO thread did not stop gracefully")
                gpio_thread.terminate()
                gpio_thread.wait(1000)
                
    if gpio_interface:
        gpio_interface.cleanup_gpio()
    
    # Additional cleanup for lgpio
    if GPIO_AVAILABLE:
        try:
            print("Performing final GPIO cleanup...")
        except Exception as e:
            print(f"GPIO final cleanup warning: {e}")

class GPIOInterface(QObject):
    """
    Object interfaces directly with GPIO hardware
    """
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # GPIO Pin Mappings 
        # BCM/GPIO numbering for lgpio (converted from BOARD numbering)
        self.STIM_LED_PINS = [
            [17, 27, 22],  # Row 1: BOARD 11,13,15 -> BCM 17,27,22
            [10, 9, 11],   # Row 2: BOARD 19,21,23 -> BCM 10,9,11    
            [5, 6, 13]     # Row 3: BOARD 29,31,33 -> BCM 5,6,13   
        ]

        self.RGC_LED_PINS = [19, 26]  # BOARD 35,37 -> BCM 19,26   
        self.RGC_OUT_PINS = [8, 7]    # BOARD 24,26 -> BCM 8,7    
        
        self.PHOTODIODE_PINS = [
            [4, 18, 23],   # Row 1: BOARD 7,12,16 -> BCM 4,18,23     
            [24, 25, 12],  # Row 2: BOARD 18,22,32 -> BCM 24,25,12     
            [16, 20, 21]   # Row 3: BOARD 36,38,40 -> BCM 16,20,21     
        ]
        
        # Initialize tracking for lgpio pins
        self.claimed_pins = []
        self.gpio_chip = None
        
        # Initialize GPIO if available
        if GPIO_AVAILABLE:
            self.setup_gpio()
        else:
            print("GPIO not available - running in simulation mode")
    
    def setup_gpio(self):
        """Initialize GPIO pins for LEDs and photodiodes using lgpio"""
        global GPIO_AVAILABLE
        
        if not GPIO_AVAILABLE:
            print("lgpio not available - running in simulation mode")
            return
            
        try:
            # First, try to cleanup any existing GPIO resources
            self.cleanup_gpio()
            
            self.gpio_chip = lgpio.gpiochip_open(0)  # Open GPIO chip 0
            
            # Keep track of claimed pins for proper cleanup
            self.claimed_pins = []
            
            # Setup LED pins as outputs
            for row in range(3):
                for col in range(3):
                    led_pin = self.STIM_LED_PINS[row][col]
                    try:
                        lgpio.gpio_claim_output(self.gpio_chip, led_pin)
                        self.claimed_pins.append(led_pin)
                        lgpio.gpio_write(self.gpio_chip, led_pin, 0)  # Start with LEDs off
                    except Exception as e:
                        print(f"Failed to claim LED pin {led_pin}: {e}")
                        # Try to free the pin first, then claim it
                        try:
                            lgpio.gpio_free(self.gpio_chip, led_pin)
                            lgpio.gpio_claim_output(self.gpio_chip, led_pin)
                            self.claimed_pins.append(led_pin)
                            lgpio.gpio_write(self.gpio_chip, led_pin, 0)
                        except Exception as e2:
                            print(f"Failed to recover LED pin {led_pin}: {e2}")
                    
                    # Setup photodiode pins as inputs
                    photodiode_pin = self.PHOTODIODE_PINS[row][col]
                    try:
                        lgpio.gpio_claim_input(self.gpio_chip, photodiode_pin)
                        self.claimed_pins.append(photodiode_pin)
                    except Exception as e:
                        print(f"Failed to claim photodiode pin {photodiode_pin}: {e}")
                        # Try to free the pin first, then claim it
                        try:
                            lgpio.gpio_free(self.gpio_chip, photodiode_pin)
                            lgpio.gpio_claim_input(self.gpio_chip, photodiode_pin)
                            self.claimed_pins.append(photodiode_pin)
                        except Exception as e2:
                            print(f"Failed to recover photodiode pin {photodiode_pin}: {e2}")
            
            # Setup RGC LED pins and output pins
            for index in range(2):
                RGC_LED_PIN = self.RGC_LED_PINS[index]
                RGC_OUT_PIN = self.RGC_OUT_PINS[index]
                
                # Setup RGC LED pin
                try:
                    lgpio.gpio_claim_output(self.gpio_chip, RGC_LED_PIN)
                    self.claimed_pins.append(RGC_LED_PIN)
                    lgpio.gpio_write(self.gpio_chip, RGC_LED_PIN, 0)
                except Exception as e:
                    print(f"Failed to claim RGC LED pin {RGC_LED_PIN}: {e}")
                    try:
                        lgpio.gpio_free(self.gpio_chip, RGC_LED_PIN)
                        lgpio.gpio_claim_output(self.gpio_chip, RGC_LED_PIN)
                        self.claimed_pins.append(RGC_LED_PIN)
                        lgpio.gpio_write(self.gpio_chip, RGC_LED_PIN, 0)
                    except Exception as e2:
                        print(f"Failed to recover RGC LED pin {RGC_LED_PIN}: {e2}")
                
                # Setup RGC output pin
                try:
                    lgpio.gpio_claim_output(self.gpio_chip, RGC_OUT_PIN)
                    self.claimed_pins.append(RGC_OUT_PIN)
                    lgpio.gpio_write(self.gpio_chip, RGC_OUT_PIN, 0)
                except Exception as e:
                    print(f"Failed to claim RGC output pin {RGC_OUT_PIN}: {e}")
                    try:
                        lgpio.gpio_free(self.gpio_chip, RGC_OUT_PIN)
                        lgpio.gpio_claim_output(self.gpio_chip, RGC_OUT_PIN)
                        self.claimed_pins.append(RGC_OUT_PIN)
                        lgpio.gpio_write(self.gpio_chip, RGC_OUT_PIN, 0)
                    except Exception as e2:
                        print(f"Failed to recover RGC output pin {RGC_OUT_PIN}: {e2}")
                
            print("lgpio GPIO initialization successful")
            
        except Exception as e:
            print(f"lgpio GPIO initialization failed: {e}")
            GPIO_AVAILABLE = False

    def write_rgc_leds(self, rgc_bool_status):
        """Write RGC LED states using lgpio"""
        if not GPIO_AVAILABLE:
            return
            
        if not hasattr(self, 'gpio_chip') or self.gpio_chip is None:
            return
        try:
            for i, state in enumerate(rgc_bool_status):
                LED_pin = self.RGC_LED_PINS[i]
                OUT_pin = self.RGC_OUT_PINS[i]
                gpio_state = 1 if state else 0
                lgpio.gpio_write(self.gpio_chip, LED_pin, gpio_state)
                lgpio.gpio_write(self.gpio_chip, OUT_pin, gpio_state)
        except Exception as e:
            print(f"Error writing RGC LEDs with lgpio: {e}")
        
    def write_stim_leds(self, led_states):
        """
        Write stimulus LED states to GPIO pins using lgpio
        Args: led_states - flattened array of 9 boolean values (True=ON, False=OFF)
        """
        if not GPIO_AVAILABLE:
            return  # Skip if GPIO not available
            
        if not hasattr(self, 'gpio_chip') or self.gpio_chip is None:
            return
        try:
            for i, state in enumerate(led_states):
                row = i // 3
                col = i % 3
                led_pin = self.STIM_LED_PINS[row][col]
                gpio_state = 1 if state else 0
                lgpio.gpio_write(self.gpio_chip, led_pin, gpio_state)
        except Exception as e:
            print(f"Error writing stimulus LEDs with lgpio: {e}")

    def read_photodiodes(self):
        """
        Read photodiode values from GPIO pins using lgpio
        Returns: 3x3 numpy array of photodiode readings
        
        Note: Photodiodes have inverted logic:
        - LED ON → Photodiode sees light → LOW voltage (0V)
        - LED OFF → Photodiode no light → HIGH voltage (3.3V)
        """
        if not GPIO_AVAILABLE:
            # In simulation mode, return current LED states as photodiode feedback
            return np.array(self.data_manager.activated_stim_states)
        
        photodiode_values = np.zeros((3, 3))
        
        if not hasattr(self, 'gpio_chip') or self.gpio_chip is None:
            return np.array(self.data_manager.activated_stim_states)
        try:
            for row in range(3):
                for col in range(3):
                    photodiode_pin = self.PHOTODIODE_PINS[row][col]
                    # Raw value is 0 (light detected) or 1 (no light detected)
                    digital_value = lgpio.gpio_read(self.gpio_chip, photodiode_pin)
                    
                    # IMPORTANT: photodiode logic - invert the reading
                    # GPIO: HIGH voltage (1) means no light detected → we want 0
                    # GPIO: LOW voltage (0) means light detected → we want 1
                    photodiode_values[row, col] = 1 - digital_value
        except Exception as e:
            print(f"Error reading photodiodes with lgpio: {e}")
            return np.array(self.data_manager.activated_stim_states)

        return photodiode_values
    
    def cleanup_gpio(self):
        """Clean up GPIO resources"""
        if GPIO_AVAILABLE:
            # Free all claimed pins first
            if hasattr(self, 'claimed_pins') and hasattr(self, 'gpio_chip'):
                for pin in self.claimed_pins:
                    try:
                        lgpio.gpio_free(self.gpio_chip, pin)
                    except Exception as e:
                        print(f"Warning: Failed to free pin {pin}: {e}")
                self.claimed_pins.clear()
            
            # Close the GPIO chip
            if hasattr(self, 'gpio_chip'):
                try:
                    lgpio.gpiochip_close(self.gpio_chip)
                except Exception as e:
                    print(f"Warning: Failed to close GPIO chip: {e}")

class GPIOWorker(QObject):
    # Single, clear signal for photodiode data ready
    photodiode_data_ready = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, gpio_interface):
        super().__init__()
        self.gpio_interface = gpio_interface
        self.data_manager = gpio_interface.data_manager  # Add reference to data_manager
        self.dt_ms = self.data_manager.dt_ms  # Get dt_ms from data_manager
        self.timer = None
        # Pre-compute connectivity mappings once
        self.state_to_amplitude = {"off": 0, "excitatory": 1, "inhibitory": -1}
        self.delay_to_ms = self.data_manager.graphing_delay_to_ms 
        
        # Cache processed connectivity data to avoid repeated processing
        self._cached_connectivity_hash = None
        self._cached_polarities = None
        self._cached_delay_indices = None
        self._cached_off_mask = None
        self._cached_neuron_polarities = None  # Cache for ON/OFF neuron types
        
        # Connect stop signal to stop method
        self.stop_requested.connect(self.stop)

    def start_reading(self):
        """Start the 25ms photodiode reading cycle - called after moveToThread()"""
        if self.timer is None:
            self.timer = QTimer()
            self.timer.timeout.connect(self.read_photodiodes)
            
        if not self.timer.isActive():
            self.timer.start(25)  # 40Hz sampling rate for photodiode monitoring
            

    def stop_reading(self):
        """Stop the GPIO reading timer and emit finished signal"""
        if self.timer and self.timer.isActive():
            self.timer.stop()
        # Emit finished to trigger cleanup
        self.finished.emit()

    def read_photodiodes(self):
        """
        Core 25ms cycle: Read photodiodes and emit data ready signal
        This is the single point of photodiode data acquisition
        """
        photodiode_data = self.gpio_interface.read_photodiodes()    
        
        # Add current photodiode data to buffer first
        self.data_manager.add_photodiode_states_to_buffer(photodiode_data)
        
        self.photodiode_data_ready.emit(photodiode_data)

        #  Only update connectivity processing if data changed
        all_connectivity_data = self.data_manager.get_all_neuron_connectivity()
        
        # Also include neuron polarities in the hash check
        neuron_polarities = {
            1: self.data_manager.get_neuron_polarity(1),
            2: self.data_manager.get_neuron_polarity(2)
        }
        
        connectivity_hash = hash(str(all_connectivity_data) + str(neuron_polarities))
        
        if connectivity_hash != self._cached_connectivity_hash:
            self._update_connectivity_cache(all_connectivity_data, neuron_polarities)
            self._cached_connectivity_hash = connectivity_hash
        
        # Use cached connectivity data
        # Get delayed photodiode values from the raw buffer for all connections at once
        photodiode_buffer = self.data_manager.get_buffer_as_array("raw_photodiode")
        buffer_length = photodiode_buffer.shape[0]
        delayed_photodiode_values = np.zeros((2, 9))
        
        for rgc_i in range(2):
            for photo_i in range(9):
                delay_idx = self._cached_delay_indices[rgc_i, photo_i]
                # Access the buffer with proper delay indexing
                delayed_index = max(0, buffer_length + delay_idx)
                raw_photodiode_value = photodiode_buffer[delayed_index, photo_i]
                
                # Apply polarity-dependent processing using cached neuron polarity
                if self._cached_neuron_polarities[rgc_i] == "ON":
                    # ON cells: light detected -> 1, no light -> 0 (normal)
                    delayed_photodiode_values[rgc_i, photo_i] = raw_photodiode_value
                else:  # OFF cells
                    # OFF cells: light detected -> 0, no light -> 1 (inverted)
                    delayed_photodiode_values[rgc_i, photo_i] = 1 - raw_photodiode_value
        
        # Calculate responses directly using cached polarities
        current_responses = self._cached_polarities * delayed_photodiode_values  # Shape: (2, 9)
        
        # Handle "off" states using cached mask
        current_responses[self._cached_off_mask] = 0.0
        
        # Add to plotting buffer queue (this automatically handles rolling window)
        self.data_manager.computed_photodiode_response_buffer_queue.append(current_responses)

        # compute RGC responses
        rgc_response = self.compute_current_rgc_response(current_responses)
        self.data_manager.computed_rgc_response_buffer_queue.append(rgc_response)
        
        # Emit only the latest data 
        self.data_manager.emit_latest_data()

    def _update_connectivity_cache(self, all_connectivity_data, neuron_polarities):
        """
        Process and cache connectivity data and neuron polarities
        Only called when connectivity or polarity actually changes
        """
        # Extract connectivity data into NumPy arrays (2 RGCs × 9 photodiodes)
        states = np.array([
            [all_connectivity_data[rgc+1][i//3][i%3]["state"] for i in range(9)]
            for rgc in range(2)
        ])
        
        delays = np.array([
            [all_connectivity_data[rgc+1][i//3][i%3]["delay"] for i in range(9)]
            for rgc in range(2)
        ])
        
        # Convert states and delays to numerical arrays using pre-computed mappings
        state_vectorizer = np.vectorize(self.state_to_amplitude.get)
        self._cached_polarities = state_vectorizer(states)  # Shape: (2, 9)
        
        delay_vectorizer = np.vectorize(self.delay_to_ms.get)
        delay_ms_array = delay_vectorizer(delays)  # Shape: (2, 9)
        
        # Calculate and cache delay indices for all connections
        delay_steps = (delay_ms_array / self.dt_ms).astype(int)  # Shape: (2, 9)
        self._cached_delay_indices = -1 - delay_steps  # Shape: (2, 9)
        
        # Cache "off" states mask
        self._cached_off_mask = (states == "off")
        
        # Cache neuron polarities for efficient polarity-dependent processing
        self._cached_neuron_polarities = [
            neuron_polarities[1],  # RGC1 polarity
            neuron_polarities[2]   # RGC2 polarity
        ]

    def compute_current_rgc_response(self, current_photoreceptor_response):
        thresholds = [self.data_manager.get_neuron_threshold(1), self.data_manager.get_neuron_threshold(2)]
        summed_responses = np.sum(current_photoreceptor_response, axis=1)  # Sum across photoreceptors for each RGC
        thresholded_responses = np.where(summed_responses >= thresholds, 1, 0)

        if not np.array_equal(thresholded_responses, self.data_manager.rgc_leds_state):
            self.data_manager.rgc_leds_on_updated.emit(thresholded_responses)
            self.data_manager.rgc_leds_state = thresholded_responses
        return thresholded_responses.reshape(2, 1)
   

    def stop(self):
        """Clean shutdown of GPIO worker - called from worker thread"""
        # Stop timer safely from the worker's own thread
        if self.timer and self.timer.isActive():
            self.timer.stop()
        # Emit finished to trigger thread cleanup
        self.finished.emit()
