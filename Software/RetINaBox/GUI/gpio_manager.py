from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QThread, QMetaObject, Qt
import numpy as np 

# Only import RPi.GPIO if we're on a Raspberry Pi
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("RPi.GPIO not available - using simulation mode")
    GPIO_AVAILABLE = False

def setup_gpio_system(data_manager):
    """
    Setup the complete GPIO system with manager, worker, and thread
    Always creates worker for timer functionality - operates in simulation mode if GPIO unavailable
    Returns: (gpio_interface, gpio_worker, gpio_thread) or (None, None, None) if failed
    """

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

class GPIOInterface(QObject):
    """
    Object interfaces directly with GPIO hardware
    """
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        
        # GPIO Pin Mappings 
        # 3x3 grid mapping: [row][col] = pin_number(in GPIO.BOARD)
        self.STIM_LED_PINS = [
            [11, 13, 15], 
            [19, 21, 23],    
            [29, 31, 33]   
        ]

        self.RGC_LED_PINS = [35, 37] # [RGC1, RGC2]   
        self.RGC_OUT_PINS = [24, 26]    
        
        self.PHOTODIODE_PINS = [
            [7, 12, 16],     
            [18, 22, 32],     
            [36, 38, 40]     
        ]
        
        # Initialize GPIO if available
        if GPIO_AVAILABLE:
            self.setup_gpio()
        else:
            print("GPIO not available - running in simulation mode")
    
    def setup_gpio(self):
        """Initialize GPIO pins for LEDs and photodiodes"""  
        GPIO.setmode(GPIO.BOARD)  # Use BOARD pin numbering
        
        # Setup LED pins as outputs
        for row in range(3):
            for col in range(3):
                led_pin = self.STIM_LED_PINS[row][col]
                GPIO.setup(led_pin, GPIO.OUT)
                GPIO.output(led_pin, GPIO.LOW)  # Start with LEDs off
        
                # Setup photodiode pins as inputs
                photodiode_pin = self.PHOTODIODE_PINS[row][col]
                GPIO.setup(photodiode_pin, GPIO.IN)

        # Setup RGC LED pins as outputs
        for index in range (2):
            RGC_LED_PIN = self.RGC_LED_PINS[index]
            GPIO.setup(RGC_LED_PIN, GPIO.OUT)
            GPIO.output(RGC_LED_PIN, GPIO.LOW)
            RGC_OUT_PIN = self.RGC_OUT_PINS[index]
            GPIO.setup(RGC_OUT_PIN, GPIO.OUT)
            GPIO.output(RGC_OUT_PIN, GPIO.LOW)

    def write_rgc_leds(self, rgc_bool_status):
        if not GPIO_AVAILABLE:
            return
        else:
            for i, state in enumerate(rgc_bool_status):
                LED_pin = self.RGC_LED_PINS[i]
                OUT_pin = self.RGC_OUT_PINS[i]
                gpio_state = GPIO.HIGH if state else GPIO.LOW
                GPIO.output(LED_pin, gpio_state)
                GPIO.output(OUT_pin, gpio_state)
        
    def write_stim_leds(self, led_states):
        """
        Write LED states to GPIO pins
        led_states: 1D array of 9 boolean values (flattened 3x3 grid)
        """
        if not GPIO_AVAILABLE:
            return  # Skip if GPIO not available
            
        for i, state in enumerate(led_states):
            row = i // 3
            col = i % 3
            led_pin = self.STIM_LED_PINS[row][col]
            
            # Convert boolean to GPIO state
            gpio_state = GPIO.HIGH if state else GPIO.LOW
            GPIO.output(led_pin, gpio_state)

    def read_photodiodes(self):
        """
        Read photodiode values from GPIO pins
        Returns: 3x3 numpy array of photodiode readings
        
        Note: Photodiodes have inverted logic:
        - LED ON → Photodiode sees light → LOW voltage (0V)
        - LED OFF → Photodiode no light → HIGH voltage (3.3V)
        """
        if not GPIO_AVAILABLE:
            # In simulation mode, return current LED states as photodiode feedback
            return np.array(self.data_manager.activated_stim_states)
        
        photodiode_values = np.zeros((3, 3))
        
        for row in range(3):
            for col in range(3):
                photodiode_pin = self.PHOTODIODE_PINS[row][col]
                # Raw value is 0 (light detected) or 1 (no light detected)
                digital_value = GPIO.input(photodiode_pin)
                
                # IMPORTANT: photodiode logic - invert the reading
                # GPIO: HIGH voltage (1) means no light detected → we want 0
                # GPIO: LOW voltage (0) means light detected → we want 1
                photodiode_values[row, col] = 1 - digital_value
        
        return photodiode_values
    
    def cleanup_gpio(self):
        """Clean up GPIO resources"""
        if GPIO_AVAILABLE:
            GPIO.cleanup()

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
        connectivity_hash = hash(str(all_connectivity_data))
        
        if connectivity_hash != self._cached_connectivity_hash:
            self._update_connectivity_cache(all_connectivity_data)
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
                delayed_photodiode_values[rgc_i, photo_i] = photodiode_buffer[delayed_index, photo_i]
        
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

    def _update_connectivity_cache(self, all_connectivity_data):
        """
        Process and cache connectivity data
        Only called when connectivity actually changes
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
