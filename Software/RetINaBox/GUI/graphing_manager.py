from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, QThread, Qt, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtSvg import QSvgWidget
import pyqtgraph as pg
import numpy as np
from collections import deque
from styles import *


pg.setConfigOption('background', '#F2F2F2')  # 'w' for white, 'k' for black
pg.setConfigOption('foreground', 'k')  # 'k' for black text, 'w' for white text
pg.setConfigOption('antialias', False)  # Smooth lines

class LiveGraphWorker(QObject):
    """
    Worker thread for preprocessing live graph data to reduce GUI thread load
    Handles color mapping, segment preparation, and data optimization
    """
    # Signal emitted with preprocessed graph data ready for plotting
    preprocessed_data_ready = pyqtSignal(dict)
    finished = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.running = False
        
        # Color mapping constants for fast lookup
        self.photodiode_color_map = {0: 'gray', 1: 'red', 2: 'blue'}
        self.rgc_color_map = {0: 'gray', 1: 'active'}
        
        # Precomputed offsets for efficiency
        self.vertical_offsets = np.array([(8 - i) * 2.0 for i in range(9)])
        
        # Segment building cache to avoid recomputation
        self.segment_cache = {}
        
        # Pre-allocate fixed-size arrays to avoid dynamic memory allocation
        self.max_buffer_size = 500  # Maximum expected buffer size
        
        # Connect stop signal to stop method
        self.stop_requested.connect(self.stop_processing)
        self.temp_x_array = np.zeros(self.max_buffer_size, dtype=np.float32)
        self.temp_y_array = np.zeros(self.max_buffer_size, dtype=np.float32)
        self.temp_color_indices = np.zeros(self.max_buffer_size, dtype=np.int32)
        self.temp_raw_array = np.zeros(self.max_buffer_size, dtype=np.float32)
        
    def start_processing(self):
        """Start the preprocessing worker"""
        self.running = True
        print("Live graph worker started for data preprocessing")

    def stop_processing(self):
        """Stop the preprocessing worker and emit finished signal"""
        self.running = False
        self.finished.emit()

    @pyqtSlot(dict)
    def preprocess_graph_data(self, buffer_data):
        """
        Preprocess graph data for optimal GUI rendering
        This does all the heavy lifting so the GUI thread just needs to call setData()
        """
        if not self.running:
            return
        
        # Check if live graphing is enabled before processing
        if not self.data_manager.get_live_graphing_enabled():
            return
            
        try:
            # Extract data arrays
            raw_photodiode = buffer_data.get("raw_photodiode", np.array([]))
            photodiode_array = buffer_data.get("computed_photodiode_responses", np.array([]))
            rgc_array = buffer_data.get("computed_rgc_responses", np.array([]))

            if raw_photodiode.size == 0 or photodiode_array.size == 0 or rgc_array.size == 0:
                return
                
            # Generate x-axis data
            x_axis = np.arange(raw_photodiode.shape[0])

            # Preprocess LED indicators (current state only)
            raw_photodiodes = self._preprocess_raw_photodiodes(raw_photodiode)
            
            # Preprocess photodiode curve segments
            photodiode_segments = self._preprocess_photodiode_segments(x_axis, photodiode_array)
            
            # Preprocess RGC curve segments  
            rgc_segments = self._preprocess_rgc_segments(x_axis, rgc_array)
            
            # Package all preprocessed data
            preprocessed_data = {
                'x_axis': x_axis,
                'raw_photodiodes': raw_photodiodes,
                'photodiode_segments': photodiode_segments,
                'rgc_segments': rgc_segments,
                'timestamp': buffer_data.get('timestamp', 0)  # For tracking freshness
            }
            
            # Emit preprocessed data to GUI thread
            self.preprocessed_data_ready.emit(preprocessed_data)
            
        except Exception as e:
            print(f"Error in live graph preprocessing: {e}")
    
    def _preprocess_raw_photodiodes(self, raw_photodiode):
        """
        Preprocess LED indicator colors for all 9 LEDs
        Returns: list of color tuples ready for setBrush()
        """
        if len(raw_photodiode) == 0:
            return [(255, 255, 255, 0)] * 9  # All clear
            
        current_raw_photodiode_states = raw_photodiode[-1]  
        raw_photodiode_indicators = []
        
        for i in range(9):
            if i < len(current_raw_photodiode_states) and current_raw_photodiode_states[i] > 0.5:
                raw_photodiode_indicators.append((255, 255, 0, 200))  # Yellow
            else:
                raw_photodiode_indicators.append((255, 255, 255, 0))  # Clear

        return raw_photodiode_indicators

    def _preprocess_photodiode_segments(self, x_axis, photodiode_array):
        """
        Preprocess photodiode curve segments with colors
        Returns: dict of segments organized by LED index and RGC index
        """
        segments = {}
        
        for led_i in range(9):
            segments[led_i] = {}
            vertical_offset = self.vertical_offsets[led_i]
            
            for rgc_i in range(2):
                if rgc_i < photodiode_array.shape[1] and led_i < photodiode_array.shape[2]:
                    photodiode_values = photodiode_array[:, rgc_i, led_i]
                    y_fixed = np.full_like(photodiode_values, vertical_offset)
                    
                    # Build color-coded segments
                    segments[led_i][rgc_i] = self._build_colored_segments(
                        x_axis, y_fixed, photodiode_values, is_rgc=False
                    )
                else:
                    segments[led_i][rgc_i] = {'gray': {'x': [], 'y': []}, 'red': {'x': [], 'y': []}, 'blue': {'x': [], 'y': []}}
        
        return segments
    
    def _preprocess_rgc_segments(self, x_axis, rgc_array):
        """
        Preprocess RGC curve segments with colors
        Returns: dict of segments for RGC1 and RGC2
        """
        segments = {}
        
        # RGC1 (index 0)
        if rgc_array.shape[1] > 0:
            rgc1_values = rgc_array[:, 0, 0]
            y_fixed = np.zeros_like(rgc1_values)  # Fixed horizontal line
            segments['rgc1'] = self._build_colored_segments(
                x_axis, y_fixed, rgc1_values, is_rgc=True, active_color='yellow'
            )
        else:
            segments['rgc1'] = {'gray': {'x': [], 'y': []}, 'yellow': {'x': [], 'y': []}}
        
        # RGC2 (index 1)
        if rgc_array.shape[1] > 1:
            rgc2_values = rgc_array[:, 1, 0]
            y_fixed = np.zeros_like(rgc2_values)  # Fixed horizontal line
            segments['rgc2'] = self._build_colored_segments(
                x_axis, y_fixed, rgc2_values, is_rgc=True, active_color='green'
            )
        else:
            segments['rgc2'] = {'gray': {'x': [], 'y': []}, 'green': {'x': [], 'y': []}}
        
        return segments
    
    def _build_colored_segments(self, x_data, y_data, raw_values, is_rgc=False, active_color=None):
        """
        Build color-coded line segments for efficient plotting using pre-allocated arrays
        Returns: dict with color keys containing x,y coordinate lists
        """
        if len(x_data) < 2:
            if is_rgc:
                return {'gray': {'x': [], 'y': []}, active_color: {'x': [], 'y': []}}
            else:
                return {'gray': {'x': [], 'y': []}, 'red': {'x': [], 'y': []}, 'blue': {'x': [], 'y': []}}
        
        data_length = len(x_data)
        if data_length > self.max_buffer_size:
            # Fallback to dynamic allocation for unusually large datasets
            x_array = np.asarray(x_data, dtype=np.float32)
            y_array = np.asarray(y_data, dtype=np.float32) 
            raw_array = np.asarray(raw_values, dtype=np.float32)
            color_indices = np.zeros(data_length, dtype=np.int32)
        else:
            # Use pre-allocated arrays for better performance
            self.temp_x_array[:data_length] = x_data
            self.temp_y_array[:data_length] = y_data
            self.temp_raw_array[:data_length] = raw_values
            x_array = self.temp_x_array[:data_length]
            y_array = self.temp_y_array[:data_length]
            raw_array = self.temp_raw_array[:data_length]
            color_indices = self.temp_color_indices[:data_length]
            color_indices.fill(0)  # Reset to zeros
        
        # Vectorized color assignment using pre-allocated arrays
        if is_rgc:
            color_indices[raw_array > 0.5] = 1
            color_map = {0: 'gray', 1: active_color}
            available_colors = ['gray', active_color]
        else:
            color_indices[raw_array > 0.5] = 1  # red
            color_indices[raw_array < -0.5] = 2  # blue
            color_map = self.photodiode_color_map
            available_colors = ['gray', 'red', 'blue']
        
        # Initialize segments dict
        segments = {color: {'x': [], 'y': []} for color in available_colors if color}
        
        # Build segments by grouping consecutive same-colored points
        i = 0
        while i < len(color_indices):
            current_color_idx = color_indices[i]
            current_color = color_map[current_color_idx]
            
            # Find end of this color segment
            segment_start = i
            while i < len(color_indices) and color_indices[i] == current_color_idx:
                i += 1
            segment_end = i
            
            # Add segment if it has more than one point
            if segment_end > segment_start + 1 and current_color in segments:
                # Add NaN separator if this isn't the first segment for this color
                if segments[current_color]['x']:
                    segments[current_color]['x'].append(np.nan)
                    segments[current_color]['y'].append(np.nan)
                
                # Add the segment data (convert to regular lists to avoid view issues)
                segments[current_color]['x'].extend(x_array[segment_start:segment_end].tolist())
                segments[current_color]['y'].extend(y_array[segment_start:segment_end].tolist())
        
        return segments

class ScaleBarWidget(QWidget):
    """Custom scale bar widget to replace x-axis labels"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)  # Increased height to fit scale text properly
        self.scale_length = 40  # Length in pixels for the scale bar (reduced to make room for "Time")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        
        # Draw "Time" label on the left side (centered vertically) with graph label styling
        time_label = "Time"
        # Use the same font styling as graph labels (font-weight: normal)
        time_font = pg.QtGui.QFont(FONTS['family'], 10)  
        time_font.setWeight(pg.QtGui.QFont.Normal)
        painter.setFont(time_font)
        
        time_rect = painter.fontMetrics().boundingRect(time_label)
        time_x = width // 2 - time_rect.width() // 2  # Centered horizontally
        time_y = height // 2 + time_rect.height() // 2 - 2
        painter.drawText(time_x, time_y, time_label)
        
        # Calculate scale bar position (aligned with 9s to 10s marks on the graph)
        bar_y = height // 2
        # Position bar from 9s (360 timepoints) to 10s (400 timepoints) 
        # Scale based on widget width: 360-400 timepoints out of 430 total range
        bar_x_start = int(width * (360 / 430)) - 4 # 9s mark position
        bar_x_end = int(width * (400 / 430)) - 9   # 10s mark position

        # Set pen for drawing scale bar
        pen = QPen(Qt.black, 1)
        painter.setPen(pen)
        
        # Draw main horizontal line
        painter.drawLine(bar_x_start, bar_y, bar_x_end, bar_y)
        
        # Draw vertical ticks at ends
        tick_height = 4
        painter.drawLine(bar_x_start, bar_y - tick_height//2, bar_x_start, bar_y + tick_height//2)
        painter.drawLine(bar_x_end, bar_y - tick_height//2, bar_x_end, bar_y + tick_height//2)
        
        # Draw scale text label BELOW the bar (right side) with smaller font
        scale_font = pg.QtGui.QFont(FONTS['family'], 9)  # Smaller font for scale text
        painter.setFont(scale_font)
        
        scale_text = f"1 sec"
        scale_rect = painter.fontMetrics().boundingRect(scale_text)
        scale_x = bar_x_start + (self.scale_length - scale_rect.width()) // 2  # Center under scale bar
        scale_y = bar_y + 12  # Reduced from 15 to 12 pixels below the bar
        painter.drawText(scale_x, scale_y, scale_text)

        
def setup_live_graph_system(data_manager, plot_update_rate_ms=50):
    """
    Setup the live_graph system with worker thread for preprocessing graph data
    plot_update_rate_ms: Plot update interval in milliseconds (50-100ms recommended for Raspberry Pi)
    Returns: (live_graph_worker, live_graph_thread) for optimal GUI performance
    """
    try:
        # Create live graph worker thread
        live_graph_thread = QThread()
        live_graph_worker = LiveGraphWorker(data_manager)
        
        # Move worker to thread
        live_graph_worker.moveToThread(live_graph_thread)
        
        # Connect signals
        # When thread starts, start the worker
        live_graph_thread.started.connect(live_graph_worker.start_processing)
        
        # Connect data manager signals to worker for preprocessing
        data_manager.buffer_data_ready.connect(live_graph_worker.preprocess_graph_data)
        
        # Cleanup connections
        live_graph_worker.finished.connect(live_graph_thread.quit)
        live_graph_worker.finished.connect(live_graph_worker.deleteLater)
        live_graph_thread.finished.connect(live_graph_thread.deleteLater)
        
        print(f"Live graph system setup successful with {plot_update_rate_ms}ms plot updates")
        return live_graph_worker, live_graph_thread
        
    except Exception as e:
        print(f"Failed to initialize live graph system: {e}")
        return None, None


def cleanup_live_graph_system(live_graph_worker, live_graph_thread):
    """Clean up live_graph system resources"""
    if live_graph_worker and live_graph_thread:
        print("Cleaning up live graphs sytem...")
        
        if live_graph_thread.isRunning():
            # Connect finished signal to quit thread
            live_graph_worker.finished.connect(live_graph_thread.quit)
            
            # Emit signal to stop worker from its own thread
            live_graph_worker.stop_requested.emit()
            
            # Wait for thread to finish
            if not live_graph_thread.wait(3000):
                print("Warning: Live graph thread did not stop gracefully")
                live_graph_thread.terminate()
                live_graph_thread.wait(1000)
                
        print("Live Graph system cleaned up")

class LiveGrapherWidget(QGroupBox):
    def __init__(self, data_manager, live_graph_worker, live_graph_thread, plot_update_rate_ms=50):
        super().__init__("Signal Monitor")
        self.data_manager = data_manager
        self.setStyleSheet(GROUP_BOX_STYLES['default'])
        self.setContentsMargins(2,2,2,2)
        self.live_graph_worker = live_graph_worker
        self.live_graph_thread = live_graph_thread

        # Initialize local rolling buffers for efficient plotting
        self.buffer_size = int(data_manager.duration_s * 1000 / data_manager.interval_ms)  # 400 timepoints
        self.init_local_buffers()

        # Rate limiting for plot updates (50ms = 20 Hz instead of 25ms = 40 Hz)
        self.plot_update_interval = plot_update_rate_ms  # milliseconds (adjustable: 50-100ms)
        self.pending_plot_data = None
        self.last_plot_update = 0
        
        # Timer for rate-limited plot updates
        self.plot_timer = QTimer()
        self.plot_timer.setSingleShot(True)
        self.plot_timer.timeout.connect(self._execute_pending_plot_update)
        
        # Pre-allocate fixed-size arrays to avoid dynamic memory allocation during plotting
        self.temp_plotting_x = np.zeros(self.buffer_size, dtype=np.float32)
        self.temp_plotting_y = np.zeros(self.buffer_size, dtype=np.float32)
        self.temp_plotting_raw = np.zeros(self.buffer_size, dtype=np.float32)
        self.temp_color_indices = np.zeros(self.buffer_size, dtype=np.int32)
        
        
        # Initialize UI
        self.setup_ui()
        self.setup_plots()

        # Connect to the new preprocessed data signal from live graph worker with rate limiting
        if self.live_graph_worker:
            self.live_graph_worker.preprocessed_data_ready.connect(self._rate_limited_plot_update)
        else:
            # Fallback to original signal if worker not available
            self.data_manager.buffer_data_ready.connect(self._rate_limited_fallback_plot)

    def _rate_limited_plot_update(self, preprocessed_data):
        """
        Rate-limited plot update for preprocessed data - limits to 50ms intervals (20 Hz)
        This reduces CPU load while maintaining smooth visual appearance
        """
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Store the latest data
        self.pending_plot_data = ('preprocessed', preprocessed_data)
        
        # Check if enough time has passed since last update
        time_since_last_update = current_time - self.last_plot_update
        
        if time_since_last_update >= self.plot_update_interval:
            # Update immediately if enough time has passed
            self._execute_pending_plot_update()
        else:
            # Schedule update after remaining time
            remaining_time = self.plot_update_interval - time_since_last_update
            if not self.plot_timer.isActive():
                self.plot_timer.start(int(remaining_time))

    def _rate_limited_fallback_plot(self, latest_data):
        """
        Rate-limited plot update for fallback mode - limits to 50ms intervals (20 Hz)
        """
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Store the latest data
        self.pending_plot_data = ('fallback', latest_data)
        
        # Check if enough time has passed since last update
        time_since_last_update = current_time - self.last_plot_update
        
        if time_since_last_update >= self.plot_update_interval:
            # Update immediately if enough time has passed
            self._execute_pending_plot_update()
        else:
            # Schedule update after remaining time
            remaining_time = self.plot_update_interval - time_since_last_update
            if not self.plot_timer.isActive():
                self.plot_timer.start(int(remaining_time))

    def _execute_pending_plot_update(self):
        """
        Execute the pending plot update and update timing
        """
        if self.pending_plot_data is None:
            return
            
        import time
        self.last_plot_update = time.time() * 1000  # Update timestamp
        
        plot_type, data = self.pending_plot_data
        self.pending_plot_data = None  # Clear pending data
        
        try:
            if plot_type == 'preprocessed':
                self.plot_preprocessed_data(data)
            elif plot_type == 'fallback':
                self.plot_new_single_data(data)
        except Exception as e:
            print(f"Error in rate-limited plot update: {e}")

    def set_plot_update_rate(self, interval_ms):
        """
        Adjust the plot update rate (for performance tuning on different devices)
        interval_ms: Update interval in milliseconds (50-100ms recommended for Raspberry Pi)
        """
        self.plot_update_interval = max(25, min(200, interval_ms))  # Clamp between 25-200ms

    def init_local_buffers(self):
        """Initialize local rolling buffers for efficient plotting"""
        # Pre-allocate deques for rolling data - much more efficient than arrays
        self.local_activated_LEDs = deque(maxlen=self.buffer_size)
        self.local_photodiode_responses = deque(maxlen=self.buffer_size)
        self.local_rgc_responses = deque(maxlen=self.buffer_size)
        
        # Initialize with zeros
        for _ in range(self.buffer_size):
            self.local_activated_LEDs.append(np.zeros(9))
            self.local_photodiode_responses.append(np.zeros((2, 9)))
            self.local_rgc_responses.append(np.zeros((2, 1)))

    def setup_ui(self):
        """Setup the main UI layout with graphs"""
        # Create the layout directly on this GroupBox
        graphs_layout = QVBoxLayout() 
        graphs_layout.setContentsMargins(8, 8, 8, 8)  
        graphs_layout.setSpacing(0)  
        
        # Add unified legend at the top
        self.create_unified_legend(graphs_layout)
        
        # Add separator line between legend and RGC GroupBoxes
        legend_separator = QFrame()
        legend_separator.setFrameShape(QFrame.HLine)
        legend_separator.setFrameShadow(QFrame.Sunken)
        legend_separator.setStyleSheet("QFrame { color: #CCCCCC; margin: 5px 0px; }")
        graphs_layout.addWidget(legend_separator)
        
        # Create RGC GroupBoxes directly
        self.create_rgc_groupboxes(graphs_layout)
        
        self.setLayout(graphs_layout)

    def create_unified_legend(self, layout):
        """Create a unified legend showing all line types and colors"""
        legend_widget = QWidget()
        legend_widget.setFixedHeight(50)
        legend_widget.setStyleSheet("background: transparent;")  # Make legend background transparent

        # Line types
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(10)
        
        # Create small plot widgets for legend items
        legend_items = [
            {"color": "red", "width": 3, "label": "Excitatory"},
            {"color": "blue", "width": 3, "label": "Inhibitory"}, 
        ]

        for item in legend_items:
            # Create mini plot widget for each legend item
            mini_plot = pg.PlotWidget()
            mini_plot.setFixedSize(20, 10)
            mini_plot.hideAxis('left')
            mini_plot.hideAxis('bottom')
            mini_plot.setMouseEnabled(x=False, y=False)
            mini_plot.hideButtons()
            
            # Draw sample line
            x_sample = np.array([0, 0.5])
            y_sample = np.array([0.5, 0.5])
            mini_plot.plot(x_sample, y_sample, pen=pg.mkPen(color=item["color"], width=item["width"], alpha=0.9))
            mini_plot.setXRange(0, 0.5)
            mini_plot.setYRange(0, 1)
            
            # Create label
            label = QLabel(item["label"])
            label.setStyleSheet("font-size: 11px;")
            
            # Add to legend layout
            item_layout = QHBoxLayout()
            item_layout.setSpacing(5)
            item_layout.addWidget(mini_plot)
            item_layout.addWidget(label)
            
            legend_layout.addLayout(item_layout)
        
        # Add stretch to center the legend
        legend_layout.insertStretch(0)
        legend_layout.addStretch()
                
        legend_widget.setLayout(legend_layout)
        layout.addWidget(legend_widget)

    def create_rgc_groupboxes(self, layout):
        """Create RGC GroupBoxes and add them to the layout"""
        # Create RGC1 GroupBox with transparent border
        rgc1_groupbox = QGroupBox("RGC 1")
        rgc1_groupbox.setStyleSheet(GROUP_BOX_STYLES['default'] + """
            QGroupBox { 
                border: 1px solid transparent; 
                font-weight: bold; 
                margin-top: 0px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                top: 2px;
                padding: 0 5px 0 5px;
            }
        """)
        rgc1_layout = QVBoxLayout()
        rgc1_layout.setContentsMargins(6, 8, 6, 4) 
        rgc1_layout.setSpacing(6)  

        # RGC1 Input plot
        self.plot1 = pg.PlotWidget()
        self.plot1.setLabel('left', 'Photoreceptor Output', **{'font-weight': 'normal', 'font-size': '10px'})
        self.plot1.getAxis('bottom').setStyle(showValues=False)
        tick_font_1 = pg.QtGui.QFont(FONTS['family'], 10)
        tick_font_1.setWeight(pg.QtGui.QFont.Normal)
        self.plot1.getAxis('left').setStyle(tickFont=tick_font_1)
        # Hide the bottom axis completely
        self.plot1.getAxis('bottom').setHeight(0)
        self.plot1.getAxis('bottom').hide()
        self.plot1.hideButtons()
        self.plot1.setMouseEnabled(x=False, y=False)  # Disable zooming and panning 
        rgc1_layout.addWidget(self.plot1, stretch=4)  
        
        # RGC1 Response plot
        self.plot3 = pg.PlotWidget()
        self.plot3.setLabel('left', 'RGC 1', **{'font-weight': 'normal', 'font-size': '10px'})
        self.plot3.getAxis('bottom').setStyle(showValues=False)
        tick_font_3 = pg.QtGui.QFont(FONTS['family'], 10)
        tick_font_3.setWeight(pg.QtGui.QFont.Normal)
        self.plot3.getAxis('left').setStyle(tickFont=tick_font_3)
        # Link x-axis of RGC1 plots
        self.plot3.setXLink(self.plot1)
        self.plot3.hideButtons()
        self.plot3.setMouseEnabled(x=False, y=False)  # Disable zooming and panning 
        self.plot3.setFixedHeight(40)  # Set small fixed height for RGC response plot
        rgc1_layout.addWidget(self.plot3, stretch=0)  # No stretch, use fixed size
        
        rgc1_layout.setSpacing(0) 
        self.scale_bar_1 = ScaleBarWidget()
        rgc1_layout.addWidget(self.scale_bar_1, stretch=0)
        
        rgc1_groupbox.setLayout(rgc1_layout)
        layout.addWidget(rgc1_groupbox)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { color: #CCCCCC; margin: 5px 0px; }")
        layout.addWidget(separator)
        
        rgc2_groupbox = QGroupBox("RGC 2")
        rgc2_groupbox.setStyleSheet(GROUP_BOX_STYLES['default'] + """
            QGroupBox { 
                border: 1px solid transparent; 
                font-weight: bold; 
                margin-top: 0px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                top: 2px;
                padding: 0 5px 0 5px;
            }
        """)
        rgc2_layout = QVBoxLayout()
        rgc2_layout.setContentsMargins(6, 8, 6, 4)  
        rgc2_layout.setSpacing(6)  
        
        # RGC2 Input plot
        self.plot2 = pg.PlotWidget()
        self.plot2.setLabel('left', 'Photoreceptor Output', **{'font-weight': 'normal', 'font-size': '10px'})
        self.plot2.getAxis('bottom').setStyle(showValues=False)
        tick_font_2 = pg.QtGui.QFont(FONTS['family'], 10)
        tick_font_2.setWeight(pg.QtGui.QFont.Normal)
        self.plot2.getAxis('left').setStyle(tickFont=tick_font_2)
        # Hide the bottom axis completely
        self.plot2.getAxis('bottom').setHeight(0)
        self.plot2.getAxis('bottom').hide()
        self.plot2.hideButtons()
        self.plot2.setMouseEnabled(x=False, y=False)  # Disable zooming and panning 
        rgc2_layout.addWidget(self.plot2, stretch=4)  
        
        # RGC2 Response plot
        self.plot4 = pg.PlotWidget()  
        self.plot4.setLabel('left', 'RGC 2', **{'font-weight': 'normal', 'font-size': '10px'})
        # Hide bottom axis labels but keep ticks
        self.plot4.getAxis('bottom').setStyle(showValues=False)
        tick_font_4 = pg.QtGui.QFont(FONTS['family'], 10)
        tick_font_4.setWeight(pg.QtGui.QFont.Normal)
        self.plot4.getAxis('left').setStyle(tickFont=tick_font_4)
        # Link x-axis of RGC2 plots
        self.plot4.setXLink(self.plot2)
        self.plot4.hideButtons()
        self.plot4.setMouseEnabled(x=False, y=False)  # Disable zooming and panning 
        self.plot4.setFixedHeight(40)  
        rgc2_layout.addWidget(self.plot4, stretch=0) 
        # Add scale bar widget right under plot4 with minimal spacing
        rgc2_layout.setSpacing(0)  
        self.scale_bar_2 = ScaleBarWidget()
        rgc2_layout.addWidget(self.scale_bar_2, stretch=0)
        
        rgc2_groupbox.setLayout(rgc2_layout)
        layout.addWidget(rgc2_groupbox)

    def setup_plots(self):
        """Initialize plot curves"""

        # Plot 1 & 2: LED and Photodiode Responses
        self.activated_LED_curves_1 = []
        self.activated_LED_curves_2 = []
        self.photodiode_curves = []
        self.photodiode_indicators_1 = []  # Status indicator squares for plot1
        self.photodiode_indicators_2 = []  # Status indicator squares for plot2
        
        for _ in range(9):
            # LED shaded region (white with alpha 0.3)
            # Create dummy curves for initialization
            dummy_curve1 = pg.PlotCurveItem(x=[], y=[], pen=None)
            dummy_curve2 = pg.PlotCurveItem(x=[], y=[], pen=None)
            led_fill_1 = pg.FillBetweenItem(dummy_curve1, dummy_curve2, brush=pg.mkBrush(color=(255, 225, 0, 85)))
            self.plot1.addItem(led_fill_1) 
            dummy_curve3 = pg.PlotCurveItem(x=[], y=[], pen=None)
            dummy_curve4 = pg.PlotCurveItem(x=[], y=[], pen=None)
            led_fill_2 = pg.FillBetweenItem(dummy_curve3, dummy_curve4, brush=pg.mkBrush(color=(255, 225, 0, 85)))
            self.plot2.addItem(led_fill_2)
            self.activated_LED_curves_1.append(led_fill_1)
            self.activated_LED_curves_2.append(led_fill_2)

            # Status indicator squares (initially clear)
            indicator_1 = pg.ScatterPlotItem(
                x=[407], y=[(8 - _) * 2.0], 
                symbol='o', size=10, 
                brush=pg.mkBrush(color=(255, 255, 255, 0)),  # Clear initially
                pen=pg.mkPen(color=(128, 128, 128, 225), width=2)  # Darker gray outline
            )
            indicator_2 = pg.ScatterPlotItem(
                x=[407], y=[(8 - _) * 2.0], 
                symbol='o', size=10, 
                brush=pg.mkBrush(color=(255, 255, 255, 0)),  # Clear initially
                pen=pg.mkPen(color=(128, 128, 128, 225), width=2)  # Darker gray outline
            )
            self.plot1.addItem(indicator_1)
            self.plot2.addItem(indicator_2)
            self.photodiode_indicators_1.append(indicator_1)
            self.photodiode_indicators_2.append(indicator_2)

            # Photodiode curves - now store multiple curve items for different colors
            rgc_curves = []
            # For each RGC, create curve items for each color state
            rgc1_curves = {
                'gray': self.plot1.plot(pen=pg.mkPen(color='gray', width=0.5, alpha=0.3)),
                'red': self.plot1.plot(pen=pg.mkPen(color='red', width=4, alpha=0.8)),
                'blue': self.plot1.plot(pen=pg.mkPen(color='blue', width=4, alpha=0.8))
            }
            rgc2_curves = {
                'gray': self.plot2.plot(pen=pg.mkPen(color='gray', width=0.5, alpha=0.3)),
                'red': self.plot2.plot(pen=pg.mkPen(color='red', width=4, alpha=0.8)),
                'blue': self.plot2.plot(pen=pg.mkPen(color='blue', width=4, alpha=0.8))
            }
            rgc_curves.append(rgc1_curves)
            rgc_curves.append(rgc2_curves)
            self.photodiode_curves.append(rgc_curves)

        # Plot 3 & 4: Individual RGC Cell Responses - color-coded like photodiodes
        # RGC1 curves (gray inactive, yellow bold when active)
        self.rgc1_curves = {
            'gray': self.plot3.plot(pen=pg.mkPen(color='gray', width=0.5, alpha=0.3)),
            'yellow': self.plot3.plot(pen=pg.mkPen(color=COLORS['yellow'], width=8, alpha=0.9))
        }
        
        # RGC2 curves (gray inactive, green bold when active)
        self.rgc2_curves = {
            'gray': self.plot4.plot(pen=pg.mkPen(color='gray', width=0.5, alpha=0.3)),
            'green': self.plot4.plot(pen=pg.mkPen(color=COLORS['darkGreen'], width=8, alpha=0.9))
        }
        
        # Set y-axis range for both RGC plots
        self.plot3.setYRange(-0.75, 0.25)
        self.plot4.setYRange(-0.75, 0.25)

        # Setup custom y-axis labels
        self.setup_input_y_axis_labels()

        # Set fixed x-axis ranges and disable auto-ranging 
        self.plot1.setXRange(0, 430)
        self.plot2.setXRange(0, 430)
        self.plot3.setXRange(0, 430)
        self.plot4.setXRange(0, 430)
        self.plot1.disableAutoRange(axis='x')
        self.plot2.disableAutoRange(axis='x') 
        self.plot3.disableAutoRange(axis='x')
        self.plot4.disableAutoRange(axis='x')
        
        # Limit x-axis ticks - major ticks every 1 second, minor ticks every 0.5 seconds (no labels)
        major_tick_positions = [0, 40, 80, 120, 160, 200, 240, 280, 320, 360, 400]
        major_tick_labels = [''] * len(major_tick_positions)  # Empty labels for major ticks
        
        minor_tick_positions = [20, 60, 100, 140, 180, 220, 260, 300, 340, 380]
        minor_tick_labels = [''] * len(minor_tick_positions)  # Empty labels for minor ticks

        x_ticks = [
            list(zip(major_tick_positions, major_tick_labels)),  # Major ticks (no labels)
            list(zip(minor_tick_positions, minor_tick_labels))   # Minor ticks (no labels)
        ]
        
        self.plot1.getAxis('bottom').setTicks(x_ticks)
        self.plot2.getAxis('bottom').setTicks(x_ticks)
        self.plot3.getAxis('bottom').setTicks(x_ticks)
        self.plot4.getAxis('bottom').setTicks(x_ticks)
        
        # Disable y-axis auto-ranging for RGC plots to keep lines at fixed position
        self.plot3.disableAutoRange(axis='y')
        self.plot4.disableAutoRange(axis='y')
        
        # Set the custom ticks for both RGC response plots with matching font styling
        self.plot3.getAxis('left').setTicks([[(0.0, '  ')]])
        # Use same font size and weight as the numbered tick labels (1-9)
        tick_font_setup_3 = pg.QtGui.QFont(FONTS['family'], 11)
        self.plot3.getAxis('left').setStyle(tickFont=tick_font_setup_3)
        self.plot4.getAxis('left').setTicks([[(0.0, '  ')]])
        # Use same font size and weight as the numbered tick labels (1-9)
        tick_font_setup_4 = pg.QtGui.QFont(FONTS['family'], 11)
        self.plot4.getAxis('left').setStyle(tickFont=tick_font_setup_4)
        
        # Add vertical "Photoreceptor input" labels to the right of the circles
        # For plot1 (RGC1)
        photoreceptor_label_1 = pg.TextItem("Photoreceptor input", angle=90, anchor=(0.5, 0.5))
        label_font_1 = pg.QtGui.QFont(FONTS['family'], 10)  # Same as y-axis labels
        label_font_1.setWeight(pg.QtGui.QFont.Normal)  # Explicit normal weight to match y-axis
        photoreceptor_label_1.setFont(label_font_1)
        photoreceptor_label_1.setColor('black')  # Match y-axis label color
        photoreceptor_label_1.setPos(425, 8) 
        self.plot1.addItem(photoreceptor_label_1)
        
        # For plot2 (RGC2)
        photoreceptor_label_2 = pg.TextItem("Photoreceptor input", angle=90, anchor=(0.5, 0.5))
        label_font_2 = pg.QtGui.QFont(FONTS['family'], 10)  # Same as y-axis labels
        label_font_2.setWeight(pg.QtGui.QFont.Normal)  # Explicit normal weight to match y-axis
        photoreceptor_label_2.setFont(label_font_2)
        photoreceptor_label_2.setColor('black')  # Match y-axis label color
        photoreceptor_label_2.setPos(425, 8)  
        self.plot2.addItem(photoreceptor_label_2)

    def setup_input_y_axis_labels(self):
        """Setup custom y-axis labels for the combined plot"""
        # Combined plot: LED/Photodiode labels (1-9) at curve centers
        offset_spacing = 2.0  # Vertical spacing between rows
        tick_positions = []
        tick_labels = []
        for i in range(9):
            # Calculate center position for each LED/photodiode row
            center_offset = (8 - i) * offset_spacing
            tick_positions.append(center_offset)
            tick_labels.append(str(i + 1))  # Numbers 1-9
        
        # Set custom ticks for combined plot with consistent font styling
        self.plot1.getAxis('left').setTicks([list(zip(tick_positions, tick_labels))])
        self.plot2.getAxis('left').setTicks([list(zip(tick_positions, tick_labels))])
    
    @pyqtSlot(dict)
    def plot_preprocessed_data(self, preprocessed_data):
        """
        Plot using preprocessed data from live graph worker - ultra-fast GUI updates!
        All heavy computation has been done in the worker thread
        """
        try:
            # Extract preprocessed components
            raw_photodiode_indicators = preprocessed_data.get('raw_photodiodes', [])
            photodiode_segments = preprocessed_data.get('photodiode_segments', {})
            rgc_segments = preprocessed_data.get('rgc_segments', {})
            
            # Update LED indicators - just apply preprocessed colors
            for i, led_color in enumerate(raw_photodiode_indicators):
                if i < len(self.photodiode_indicators_1):
                    self.photodiode_indicators_1[i].setBrush(pg.mkBrush(color=led_color))
                if i < len(self.photodiode_indicators_2):
                    self.photodiode_indicators_2[i].setBrush(pg.mkBrush(color=led_color))
            
            # Update photodiode curves - apply preprocessed segments
            for led_i in range(9):
                if led_i in photodiode_segments:
                    # RGC1 curves
                    if 0 in photodiode_segments[led_i] and led_i < len(self.photodiode_curves):
                        rgc1_segments = photodiode_segments[led_i][0]
                        self._apply_segments_to_curves(rgc1_segments, self.photodiode_curves[led_i][0])
                    
                    # RGC2 curves
                    if 1 in photodiode_segments[led_i] and led_i < len(self.photodiode_curves):
                        rgc2_segments = photodiode_segments[led_i][1]
                        self._apply_segments_to_curves(rgc2_segments, self.photodiode_curves[led_i][1])
            
            # Update RGC curves - apply preprocessed segments
            if 'rgc1' in rgc_segments:
                # Map 'yellow' to actual color for RGC1
                rgc1_mapped = {
                    'gray': rgc_segments['rgc1']['gray'],
                    'yellow': rgc_segments['rgc1']['yellow']
                }
                self._apply_segments_to_curves(rgc1_mapped, self.rgc1_curves)
            
            if 'rgc2' in rgc_segments:
                # Map 'green' to actual color for RGC2
                rgc2_mapped = {
                    'gray': rgc_segments['rgc2']['gray'],
                    'green': rgc_segments['rgc2']['green']
                }
                self._apply_segments_to_curves(rgc2_mapped, self.rgc2_curves)
                
        except Exception as e:
            print(f"Error in plot_preprocessed_data: {e}")
    
    def _apply_segments_to_curves(self, segments, curve_dict):
        """
        Apply preprocessed segments to curve objects using pre-allocated arrays for optimal performance
        """
        # Clear all curves first
        for curve in curve_dict.values():
            curve.clear()
        
        # Apply each color's segments using pre-allocated arrays when possible
        for color, data in segments.items():
            if color in curve_dict and data['x']:
                # Use pre-allocated arrays if data fits, otherwise allocate dynamically
                data_length = len(data['x'])
                if data_length <= self.buffer_size:
                    # Use pre-allocated arrays for better performance
                    self.temp_plotting_x[:data_length] = data['x']
                    self.temp_plotting_y[:data_length] = data['y']
                    x_data = self.temp_plotting_x[:data_length].copy()  # Copy to avoid view issues
                    y_data = self.temp_plotting_y[:data_length].copy()
                else:
                    # Fallback for large segments
                    x_data = np.array(data['x'], dtype=np.float32)
                    y_data = np.array(data['y'], dtype=np.float32)
                
                curve_dict[color].setData(x_data, y_data)

    @pyqtSlot(dict)
    def plot_new_single_data(self, latest_data):
        """
        Fallback method for when live graph worker is not available
        Update plots with single new data point - much more efficient!
        latest_data contains only the most recent data points, not full arrays
        """
        # Handle both new format (with 'latest_' prefix) and old format for backward compatibility
        if 'latest_activated_LEDs' in latest_data:
            # New format with both full buffer and latest data
            activated_LEDs = latest_data["latest_activated_LEDs"]
            computed_photodiode_responses = latest_data["latest_computed_photodiode_responses"]
            computed_rgc_responses = latest_data["latest_computed_rgc_responses"]
        else:
            # Old format with just latest data
            activated_LEDs = latest_data["activated_LEDs"]
            computed_photodiode_responses = latest_data["computed_photodiode_responses"]
            computed_rgc_responses = latest_data["computed_rgc_responses"]
        
        # Add new data to local rolling buffers
        self.local_activated_LEDs.append(activated_LEDs)
        self.local_photodiode_responses.append(computed_photodiode_responses)
        self.local_rgc_responses.append(computed_rgc_responses)
        
        # Convert to arrays for plotting (only when needed)
        led_array = np.array(list(self.local_activated_LEDs))
        photodiode_array = np.array(list(self.local_photodiode_responses))
        rgc_array = np.array(list(self.local_rgc_responses))
        
        # Generate x-axis
        x_axis = np.arange(led_array.shape[0])
        
        # Plot with optimized approach
        self.plot_optimized_data(x_axis, led_array, photodiode_array, rgc_array)

    def plot_optimized_data(self, x_axis, led_array, photodiode_array, rgc_array):
        """
        Optimized plotting that only updates what's necessary
        """
        offset_spacing = 2.0  # Vertical spacing between rows
        
        for i in range(9):
            # Calculate vertical offset for this row
            vertical_offset = (8 - i) * offset_spacing
            
            # Update LED indicators with latest state (more efficient than full array processing)
            current_led_value = led_array[-1, i] if len(led_array) > 0 else 0
            if current_led_value > 0.5:  # LED is ON
                led_color = (255, 255, 0, 200)  # Yellow
            else:  # LED is OFF
                led_color = (255, 255, 255, 0)  # Clear (transparent)
            
            # Update both indicators for this LED (same for both RGCs)
            self.photodiode_indicators_1[i].setBrush(pg.mkBrush(color=led_color))
            self.photodiode_indicators_2[i].setBrush(pg.mkBrush(color=led_color))

            # Plot photodiode curves with color-coded segments
            for rgc_i in range(2):
                photodiode_y = photodiode_array[:, rgc_i, i]
                # Keep lines at fixed vertical offset (no movement up/down)
                photodiode_y_offset = np.full_like(photodiode_y, vertical_offset)
                
                # Create segments based on photodiode values (use raw values for color decisions)
                self.plot_colored_segments(x_axis, photodiode_y_offset, photodiode_y, self.photodiode_curves[i][rgc_i])

        # Plot RGC responses - horizontal lines that change color/boldness
        # RGC1 response
        rgc1_values = rgc_array[:, 0, 0].copy()  # Make copy to avoid reference issues
        rgc1_y_fixed = np.full_like(rgc1_values, 0.0)  # Fixed horizontal line at y=0.0
        
        # Plot colored segments for RGC1
        self.plot_colored_segments(x_axis, rgc1_y_fixed, rgc1_values, self.rgc1_curves, active_color='yellow')
        
        # RGC2 response
        rgc2_values = rgc_array[:, 1, 0].copy()  # Make copy to avoid reference issues
        rgc2_y_fixed = np.full_like(rgc2_values, 0.0)  # Fixed horizontal line at y=0.0
            
        # Plot colored segments for RGC2
        self.plot_colored_segments(x_axis, rgc2_y_fixed, rgc2_values, self.rgc2_curves, active_color='green')
    

    import numpy as np

    def plot_colored_segments(self, x_data, y_data, raw_values, curve_dict, active_color=None):
        """
        Plot line segments with different colors based on raw values using pre-allocated arrays
        For photodiodes: 0 -> gray (thin), +1 -> red (bold), -1 -> blue (bold)
        For RGCs: 0 -> gray (thin), 1 -> active_color (bold)
        """
        if len(x_data) < 2:
            return

        for curve in curve_dict.values():
            curve.clear()
        
        data_length = len(x_data)
        
        # Use pre-allocated arrays to avoid dynamic memory allocation
        if data_length <= self.buffer_size:
            # Copy data to pre-allocated arrays
            self.temp_plotting_x[:data_length] = x_data
            self.temp_plotting_y[:data_length] = y_data
            self.temp_plotting_raw[:data_length] = raw_values
            
            # Use views of pre-allocated arrays
            x_array = self.temp_plotting_x[:data_length]
            y_array = self.temp_plotting_y[:data_length]
            raw_array = self.temp_plotting_raw[:data_length]
            color_indices = self.temp_color_indices[:data_length]
            color_indices.fill(0)  # Reset to zeros
        else:
            # Fallback for unusually large data (shouldn't happen in normal operation)
            x_array = np.asarray(x_data, dtype=np.float32)
            y_array = np.asarray(y_data, dtype=np.float32)
            raw_array = np.asarray(raw_values, dtype=np.float32)
            color_indices = np.zeros(data_length, dtype=np.int32)
        
        # Vectorized color categorization using pre-allocated arrays
        if active_color:  # RGC case (binary 0/1)
            color_indices[raw_array > 0.5] = 1  # 1 for active, 0 for gray
            color_map = {0: 'gray', 1: active_color}
        else:  # Photodiode case
            color_indices[raw_array > 0.5] = 1  # red
            color_indices[raw_array < -0.5] = 2  # blue
            # Everything else stays 0 (gray)
            color_map = {0: 'gray', 1: 'red', 2: 'blue'}
        
        # Create segments by grouping consecutive points with same color
        segments = {color: {'x': [], 'y': []} for color in color_map.values() if color in curve_dict}
        
        i = 0
        while i < len(color_indices):
            current_color_idx = color_indices[i]
            current_color = color_map[current_color_idx]
            
            if current_color not in segments:
                i += 1
                continue
            
            # Find the end of this color segment
            segment_start = i
            while i < len(color_indices) and color_indices[i] == current_color_idx:
                i += 1
            segment_end = i
            
            # Add segment if it has more than one point
            if segment_end > segment_start + 1:
                # Add NaN separator if this isn't the first segment for this color
                if segments[current_color]['x']:
                    segments[current_color]['x'].append(np.nan)
                    segments[current_color]['y'].append(np.nan)
                
                # Add the segment data (convert to lists to avoid array view issues)
                segments[current_color]['x'].extend(x_array[segment_start:segment_end].tolist())
                segments[current_color]['y'].extend(y_array[segment_start:segment_end].tolist())
        
        # Plot each color's segments immediately using pre-converted data
        for color, data in segments.items():
            if data['x'] and color in curve_dict:
                # Convert to numpy arrays for setData (PyQtGraph expects numpy arrays)
                x_np = np.array(data['x'], dtype=np.float32)
                y_np = np.array(data['y'], dtype=np.float32)
                curve_dict[color].setData(x_np, y_np)


    def plot_colored_segments_realtime(self, x_data, y_data, raw_values, curve_dict, active_color=None):
        """
        Simplified real-time version - processes only new points but rebuilds segments efficiently
        """
        if len(x_data) < 2:
            return
        
        # Create unique identifier for this curve_dict
        curve_id = id(curve_dict)
        
        # Initialize persistent storage if not exists
        if not hasattr(self, '_realtime_states'):
            self._realtime_states = {}
        
        if curve_id not in self._realtime_states:
            self._realtime_states[curve_id] = {
                'last_length': 0,
                'all_colors': [],  # Store color for each point
                'last_processed_length': 0
            }
        
        state = self._realtime_states[curve_id]
        current_length = len(x_data)
        last_length = state['last_length']
        
        # Reset if data got shorter (new dataset)
        if current_length < last_length:
            state['last_length'] = 0
            state['all_colors'] = []
            state['last_processed_length'] = 0
            last_length = 0
            # Clear all curves
            for curve in curve_dict.values():
                curve.clear()
        
        # If no new data, return
        if current_length <= last_length:
            return
        
        # Convert to arrays
        raw_array = np.asarray(raw_values)
        
        # Color categorization function
        def get_color(value):
            if active_color:  # RGC case
                return active_color if value > 0.5 else 'gray'
            else:  # Photodiode case
                if abs(value) < 0.1:
                    return 'gray'
                elif value > 0.5:
                    return 'red'
                elif value < -0.5:
                    return 'blue'
                else:
                    return 'gray'
        
        # Process new points - just determine their colors
        new_colors = []
        for i in range(last_length, current_length):
            if i < len(raw_array):
                color = get_color(raw_array[i])
                new_colors.append(color)
        
        # Add new colors to our tracking
        state['all_colors'].extend(new_colors)
        
        # Only rebuild segments if we have enough new points or significant change
        points_since_last_rebuild = current_length - state['last_processed_length']
        
        # Rebuild segments if we have new data (do this every time for now to ensure it works)
        if points_since_last_rebuild > 0:
            # Clear all curves
            for curve in curve_dict.values():
                curve.clear()
            
            # Build segments from all data
            x_array = np.asarray(x_data)
            y_array = np.asarray(y_data)
            
            # Create segments
            available_colors = (['gray', active_color] if active_color else ['gray', 'red', 'blue'])
            segments = {color: {'x': [], 'y': []} for color in available_colors if color and color in curve_dict}
            
            # Group consecutive same-colored points
            i = 0
            while i < len(state['all_colors']) and i < len(x_array):
                current_color = state['all_colors'][i]
                
                if current_color not in segments:
                    i += 1
                    continue
                
                # Find end of this color segment
                segment_start = i
                while i < len(state['all_colors']) and i < len(x_array) and state['all_colors'][i] == current_color:
                    i += 1
                segment_end = i
                
                # Add segment if it has more than one point
                if segment_end > segment_start + 1:
                    # Add NaN separator if this isn't the first segment for this color
                    if segments[current_color]['x']:
                        segments[current_color]['x'].append(np.nan)
                        segments[current_color]['y'].append(np.nan)
                    
                    # Add the segment data
                    segments[current_color]['x'].extend(x_array[segment_start:segment_end])
                    segments[current_color]['y'].extend(y_array[segment_start:segment_end])
            
            # Update all plots
            for color, data in segments.items():
                if data['x'] and color in curve_dict:
                    curve_dict[color].setData(data['x'], data['y'])
            
            # Update processed length
            state['last_processed_length'] = current_length
        
        # Update state
        state['last_length'] = current_length
