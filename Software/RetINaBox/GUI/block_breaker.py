# code taken from https://www.geeksforgeeks.org/python/brick-breaker-game-in-python-using-pygame/
# originally written by GeeksforGeeks teja00219
# modified by Brune Bettler with the help of Copilot

import sys
import os
import random

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from styles import COLORS, FONTS

class GameBall:
    def __init__(self, x, y, radius=8):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed_x = 1.5    
        self.speed_y = -1.8   
        self.base_speed = 1.5
        
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        
    def bounce_x(self):
        self.speed_x = -self.speed_x
        
    def bounce_y(self):
        self.speed_y = -self.speed_y
        
    def reset(self, x, y):
        self.x = x
        self.y = y
        self.speed_x = random.choice([-1.5, 1.5])
        self.speed_y = -1.8

    def get_rect(self):
        return QRectF(self.x - self.radius, self.y - self.radius, 
                     self.radius * 2, self.radius * 2)

class GamePaddle:
    def __init__(self, x, y, width=120, height=12):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = 30
        
    def move_left(self, game_width):
        self.x = max(0, self.x - self.speed)
        
    def move_right(self, game_width):
        self.x = min(game_width - self.width, self.x + self.speed)
        
    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

class GameBrick:
    def __init__(self, x, y, width=45, height=20):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.destroyed = False
        self.color = random.choice([COLORS['lightBrown'], COLORS['darkBrown']])
        self.health = 2 if self.color == COLORS['darkBrown'] else 1
        
    def hit(self):
        self.health -= 1
        if self.health == 1 and self.color == COLORS['darkBrown']:
            self.color = COLORS['lightBrown']
        elif self.health <= 0:
            self.destroyed = True
            
    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

class RGCConfigDialog(QDialog):
    """Dialog to configure RGC paddle controls"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RGC Paddle Configuration")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        title = QLabel("Configure RGC Paddle Control")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        self.rgc1_left = QRadioButton("RGC1 → Left paddle movement")
        self.rgc1_right = QRadioButton("RGC1 → Right paddle movement")
        self.rgc1_left.setChecked(True)
        
        layout.addWidget(self.rgc1_left)
        layout.addWidget(self.rgc1_right)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Start Game")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_config(self):
        return "left" if self.rgc1_left.isChecked() else "right"

class BlockBreakerGameWidget(QWidget):
    """Main game widget using pure PyQt5"""
    
    game_over_signal = pyqtSignal()
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.setFixedSize(600, 500)
        self.setWindowTitle("RetINaBox Block-Breaker")
        self.setStyleSheet(f"background-color: {COLORS['lightGray']};")
        
        self.game_width = 600
        self.game_height = 500
        self.score = 0
        self.lives = 3
        self.game_active = False
        self.closing = False  
        
        # Game objects
        self.ball = GameBall(self.game_width // 2, self.game_height - 100)
        self.paddle = GamePaddle(self.game_width // 2 - 40, self.game_height - 30)
        self.bricks = []
        
        # RGC state tracking for edge detection
        self.previous_rgc_state = [False, False]  
        
        # Paddle movement state
        self.paddle_movement_direction = None  # None, "left", or "right"
        
        # Setup
        self.setup_bricks()
        # Delay config setup to allow parent widget hierarchy to be established
        QTimer.singleShot(100, self.setup_config)
        
        # Game timer
        self.game_timer = QTimer()
        self.game_timer.timeout.connect(self.update_game)
        self.game_timer.start(16)  # ~60 FPS
        
        # Focus for keyboard input
        self.setFocusPolicy(Qt.StrongFocus)
        
    def setup_config(self):
        """Setup game configuration"""
        # Fixed mapping: RGC1 controls right movement, RGC2 controls left movement
        # Don't start the game automatically - wait for user to click "Start Game"
        self.game_active = False
        
        # Show instructions if RGC system is available
        if self.data_manager and hasattr(self.data_manager, 'GPIO_AVAILABLE'):
            # Find the top-level tab widget parent to show instructions over the tab
            tab_parent = self
            current_parent = self.parent()
            
            # Walk up the parent hierarchy to find the BlockBreakerGameTabWidget
            while current_parent:
                if hasattr(current_parent, '__class__') and current_parent.__class__.__name__ == 'BlockBreakerGameTabWidget':
                    tab_parent = current_parent
                    break
                current_parent = current_parent.parent()
            
            instructions = QMessageBox(tab_parent)
            instructions.setWindowTitle("RGC Paddle Controls")
            instructions.setText("\n\nPaddle Controls:\n\n• RGC1 Active → Paddle moves RIGHT\n• RGC2 Active → Paddle moves LEFT\n\n")
            
            start_button = instructions.addButton("Start Game", QMessageBox.AcceptRole)
            instructions.setDefaultButton(start_button)
            
            # Only start the game if user clicks "Start Game"
            result = instructions.exec_()
            if result == QMessageBox.AcceptRole:
                self.game_active = True
        else:
            # If no GPIO system, show different instructions
            tab_parent = self
            current_parent = self.parent()
            
            # Walk up the parent hierarchy to find the BlockBreakerGameTabWidget
            while current_parent:
                if hasattr(current_parent, '__class__') and current_parent.__class__.__name__ == 'BlockBreakerGameTabWidget':
                    tab_parent = current_parent
                    break
                current_parent = current_parent.parent()
            
            instructions = QMessageBox(tab_parent)
            instructions.setWindowTitle("Block Breaker Game")
            instructions.setText("\n\nWelcome to Block Breaker!\n\nUse keyboard arrow keys to control the paddle.\n\nBreak all the bricks to win!\n\n")
            
            # Create custom button with "Start Game" text
            start_button = instructions.addButton("Start Game", QMessageBox.AcceptRole)
            instructions.setDefaultButton(start_button)
            
            # Only start the game if user clicks "Start Game"
            result = instructions.exec_()
            if result == QMessageBox.AcceptRole:
                self.game_active = True
            
    def setup_bricks(self):
        """Create the brick layout"""
        self.bricks = []
        brick_width = 45
        brick_height = 20
        rows = 8
        cols = 12
        start_x = (self.game_width - (cols * brick_width + (cols - 1) * 5)) // 2
        start_y = 50
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * (brick_width + 5)
                y = start_y + row * (brick_height + 5)
                brick = GameBrick(x, y, brick_width, brick_height)
                self.bricks.append(brick)
                
    def update_game(self):
        """Main game update loop"""
        if not self.game_active or self.closing:
            return
            
        # Handle RGC input
        self.handle_rgc_input()
        
        # Handle continuous paddle movement based on current state
        self.update_paddle_movement()
        
        # Move ball
        self.ball.move()
        
        # Ball collision with walls
        if self.ball.x <= self.ball.radius or self.ball.x >= self.game_width - self.ball.radius:
            self.ball.bounce_x()
            
        if self.ball.y <= self.ball.radius:
            self.ball.bounce_y()
            
        # Ball falls below paddle
        if self.ball.y >= self.game_height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over()
            else:
                self.reset_ball()
                
        # Ball collision with paddle
        ball_rect = self.ball.get_rect()
        paddle_rect = self.paddle.get_rect()
        if ball_rect.intersects(paddle_rect) and self.ball.speed_y > 0:
            self.ball.bounce_y()
            # Add some angle based on where ball hits paddle
            hit_pos = (self.ball.x - self.paddle.x) / self.paddle.width
            self.ball.speed_x = (hit_pos - 0.5) * 6
            
        # Ball collision with bricks
        for brick in self.bricks[:]:  # Copy list to avoid modification during iteration
            if not brick.destroyed and ball_rect.intersects(brick.get_rect()):
                brick.hit()
                self.ball.bounce_y()
                if brick.destroyed:
                    self.score += 10
                    self.bricks.remove(brick)
                break
                
        # Check win condition
        if not any(not brick.destroyed for brick in self.bricks):
            self.setup_bricks()
            self.score += 100
            self.reset_ball()
            
        # Update display
        self.update()
        
    def handle_rgc_input(self):
        """Move paddle by 150 pixels left/right on RGC transitions as described"""
        if not self.data_manager:
            return
        try:
            rgc_buffer = self.data_manager.get_buffer_as_array("computed_rgc_responses")
            if rgc_buffer is None or len(rgc_buffer) == 0:
                return
            latest_rgc_data = rgc_buffer[-1]
            rgc1_active = latest_rgc_data[0, 0] > 0.5
            rgc2_active = latest_rgc_data[1, 0] > 0.5

            prev_rgc1, prev_rgc2 = self.previous_rgc_state

            # Transition logic
            # Move right: (none active -> rgc2) or (rgc1 -> rgc2)
            if (not prev_rgc1 and not prev_rgc2 and rgc2_active and not rgc1_active) or \
               (prev_rgc1 and not prev_rgc2 and rgc2_active and not rgc1_active):
                # Move paddle right by 150 pixels
                self.paddle.x = min(self.game_width - self.paddle.width, self.paddle.x + 150)

            # Move left: (none active -> rgc1) or (rgc2 -> rgc1)
            elif (not prev_rgc1 and not prev_rgc2 and rgc1_active and not rgc2_active) or \
                 (not prev_rgc1 and prev_rgc2 and rgc1_active and not rgc2_active):
                # Move paddle left by 150 pixels
                self.paddle.x = max(0, self.paddle.x - 150)

            # Store current states for next frame comparison
            self.previous_rgc_state = [rgc1_active, rgc2_active]
        except Exception:
            pass
    
    def update_paddle_movement(self):
        """Update paddle position based on current movement state"""
        if self.paddle_movement_direction == "right":
            old_x = self.paddle.x
            self.paddle.move_right(self.game_width)
            # Stop if paddle hit the right wall
            if self.paddle.x == old_x:  # Didn't move (hit boundary)
                self.paddle_movement_direction = None
                
        elif self.paddle_movement_direction == "left":
            old_x = self.paddle.x
            self.paddle.move_left(self.game_width)
            # Stop if paddle hit the left wall
            if self.paddle.x == old_x:  # Didn't move (hit boundary)
                self.paddle_movement_direction = None
        

    def paintEvent(self, event):
        """Draw the game"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw ball
        painter.setBrush(QBrush(QColor(COLORS['black'])))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.ball.get_rect())
        
        # Draw paddle
        painter.setBrush(QBrush(QColor(COLORS['gray'])))
        painter.drawRect(self.paddle.get_rect())
        
        # Draw bricks
        for brick in self.bricks:
            if not brick.destroyed:
                painter.setBrush(QBrush(QColor(brick.color)))
                painter.drawRect(brick.get_rect())
                
        # Draw UI
        painter.setPen(QPen(QColor(COLORS['black'])))
        painter.setFont(QFont(FONTS['family'], 12))
        painter.drawText(10, 25, f"Score: {self.score}")
        painter.drawText(10, 45, f"Lives: {self.lives}")

                           
    def reset_ball(self):
        """Reset ball to starting position"""
        self.ball.reset(self.game_width // 2, self.game_height - 100)
        
    def game_over(self):
        """Handle game over"""
        self.game_active = False
        
        # Don't show popup if window is closing
        if not self.closing:
            msg = QMessageBox()
            msg.setWindowTitle("Game Over")
            msg.setText(f"Game Over!\nFinal Score: {self.score}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            
            # After user clicks OK, close the tab if we're in a tab
            self.close_tab_after_game_over()
            
        self.game_over_signal.emit()
    
    def close_tab_after_game_over(self):
        """Close the Block Breaker tab after game over"""
        # Find the tab widget parent and close this tab
        current_parent = self.parent()
        
        # Walk up the parent hierarchy to find the BlockBreakerGameTabWidget
        while current_parent:
            if hasattr(current_parent, '__class__') and current_parent.__class__.__name__ == 'BlockBreakerGameTabWidget':
                # Found the tab widget, now find the main window with the tab widget
                main_window_parent = current_parent.parent()
                while main_window_parent:
                    if hasattr(main_window_parent, 'tab_widget'):
                        # Found the main window, find which tab this is and close it
                        tab_widget = main_window_parent.tab_widget
                        for i in range(tab_widget.count()):
                            if tab_widget.widget(i) == current_parent:
                                # Don't show confirmation dialog since game is over
                                main_window_parent.cleanup_block_breaker_tab(i)
                                tab_widget.removeTab(i)
                                return
                    main_window_parent = main_window_parent.parent()
                break
            current_parent = current_parent.parent()
        
    def restart_game(self):
        """Restart the game"""
        self.score = 0
        self.lives = 3
        self.game_active = True
        self.setup_bricks()
        self.reset_ball()
        
    def closeEvent(self, event):
        """Clean up when closing"""
        self.closing = True
        self.game_active = False
        self.game_timer.stop()
        event.accept()

class BlockBreakerGameTabWidget(QWidget):
    """Game widget for tab integration"""
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        
        # Store reference to data manager
        self.data_manager = data_manager
        
        # Turn all LEDs on for the game
        if self.data_manager:
            for row in range(3):
                for col in range(3):
                    self.data_manager.set_selected_stim_state(row, col, True)
                    self.data_manager.set_activated_stim_state(row, col, True)
            self.data_manager.set_current_stim_mode("Static")
            self.data_manager.set_stim_running(True)
        
        # Main layout for the entire tab
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)  # Add margins around the entire content
        
        # Create a frame container for the game with a border
        game_frame = QFrame()
        game_frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        game_frame.setLineWidth(2)
        game_frame.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {COLORS['black']};
                border-radius: 8px;
                background-color: {COLORS['white']};
            }}
        """)
        
        # Layout for the frame (centers the game widget)
        frame_layout = QVBoxLayout()
        frame_layout.setContentsMargins(0, 0, 0, 0)  # Padding inside the frame
        frame_layout.setAlignment(Qt.AlignCenter)  # Center the game widget
        
        self.game_widget = BlockBreakerGameWidget(data_manager, self)
        # Don't auto-close the tab when game ends, just show game over
        # self.game_widget.game_over_signal.connect(self.close)
        
        # Add game widget to frame layout
        frame_layout.addWidget(self.game_widget, alignment=Qt.AlignCenter)
        game_frame.setLayout(frame_layout)
        
        # Add frame to main layout with centering
        main_layout.addStretch()  # Push content to center vertically
        main_layout.addWidget(game_frame, alignment=Qt.AlignCenter)
        main_layout.addStretch()  # Push content to center vertically
        
        self.setLayout(main_layout)
    
    def closeEvent(self, event):
        """Clean up when closing the game tab"""
        if hasattr(self, 'game_widget'):
            self.game_widget.closing = True
            self.game_widget.game_active = False
            self.game_widget.game_timer.stop()

        # Turn off all LEDs when closing the tab
        if hasattr(self, 'data_manager') and self.data_manager:
            self.data_manager.set_mode("lab")

        event.accept()

class ReboundGameWindow(QDialog):
    """Game window container"""
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("RetINaBox - Block Breaker")
        self.setModal(False)  # Allow interaction with main window
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.game_widget = BlockBreakerGameWidget(data_manager, self)
        self.game_widget.game_over_signal.connect(self.close)
        
        layout.addWidget(self.game_widget)
        self.setLayout(layout)
        
        # Size to fit game widget
        self.setFixedSize(self.game_widget.size())
    
    def closeEvent(self, event):
        """Clean up when closing the game window"""


        if hasattr(self, 'game_widget'):
            self.game_widget.closing = True
            self.game_widget.game_active = False
            self.game_widget.game_timer.stop()
        event.accept()

