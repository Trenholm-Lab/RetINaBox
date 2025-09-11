from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
import numpy as np
import json
import copy
from data_manager import *
from interaction_manager import *
from graphing_manager import *
from presets_manager import * 
import os 
from styles import * 



    
class StimWidget(QWidget):
    def __init__(self, stim_code_array):
        super().__init__()
        
        # Create a group box container for shading
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)  
        main_layout.setSpacing(0)
        self.setLayout(main_layout)
        
        # Create the group box for shading
        group_box = QGroupBox()
        group_box.setStyleSheet(f"""
            QGroupBox {{
                background-color: {COLORS['lightGray']};
                border: 1px solid #dddddd;
                border-radius: 3px;
                margin: 1px;
            }}
        """)
        
        # Create the grid layout inside the group box
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(1, 1, 1, 1)  # Minimal margins
        group_box.setLayout(grid)
        
        self.setFixedSize(55, 55)  
        self.btn_styles = []

        arr = np.array(stim_code_array).reshape(3, 3)
        for row in range(3):
            for col in range(3):
                btn = QPushButton()
                btn.setFixedSize(10, 10)
                btn.setStyleSheet(BUTTON_STYLES['code_breaker'])
                btn.setCheckable(True)
                state = arr[row, col]
                btn.setChecked(state)
                btn.setEnabled(False) # keeps buttons from being toggled by user
                grid.addWidget(btn, row, col)
        
        # Add the group box to the main layout
        main_layout.addWidget(group_box)

class StimCodeWidget(QWidget):
    def __init__(self, stim_code_array, answer, parent=None):
        super().__init__()
        '''
        stim_code_array: 1,9 binary int array containing the pattern to be visualized on the StimWidget
        answer: the correct letter for this particular stimCode as a str
        '''
        self.setStyleSheet("background-color: transparent;")
        
        self.letter_solution = answer
        self.stim_widget = StimWidget(stim_code_array)
        self.comboBox = QComboBox()
        
        self.comboBox.setFixedSize(50, 20)  
        self.comboBox.setStyleSheet(f"""background-color: {COLORS['white']};""")
        self.comboBox.addItems(parent.possible_letters)
        self.comboBox.setCurrentIndex(-1)  # No initial selection
        
        self.setFixedSize(80, 80)  
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)  
        self.layout.setSpacing(15) 
        self.layout.addWidget(self.stim_widget, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.comboBox, alignment=Qt.AlignCenter)
        
        self.layout.addStretch()
        self.setLayout(self.layout)

    def check_user_selection(self):
        selected_letter = self.comboBox.currentText()
        if selected_letter == self.letter_solution:
            return 1
        else:
            return 0

class StimCharWidget(QLabel):
    def __init__(self, char):
        super().__init__()
        self.setText(char)
        self.setFixedSize(80, 80)  # Match StimCodeWidget size
        # Align text to center-top to match the grid positioning
        self.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.setStyleSheet(f"""
            padding-top: 10px; 
            font-size: 16px; 
            font-weight: bold;
            background-color: transparent;
            color: {COLORS['black']};
            font-family: '{FONTS['family']}';
        """)


class CypherWidget(QGroupBox):
    def __init__(self, RGC_1_pref_stim, RGC_2_pref_stim, RetinaBox_output):
        super().__init__()
        '''
        RGC_1_pref_stim: 1x9 binary int array for the first RGC's preferred stimulus
        RGC_2_pref_stim: 1x9 binary int array for the second RGC's preferred stimulus
        RetinaBox_output: 1x4 list of str letters corresponding to (0,0), (1,0), (0,1), and (1,1)
        '''
        self.setTitle("Cipher")
        self.setObjectName("SecretCodeGroupBox")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(3, 3, 3, 3)  
        self.layout.setSpacing(5)  
        self.setLayout(self.layout)
        self.setFixedWidth(265)  
        
        self.setStyleSheet(GROUP_BOX_STYLES['default'])

        pref_visual_stim_box = QGroupBox("Preferred Visual Stimuli")
        pref_visual_stim_box.setFixedHeight(150) 
        pref_visual_stim_layout = QHBoxLayout()
        pref_visual_stim_layout.setContentsMargins(2, 2, 2, 2)  
        pref_visual_stim_layout.setSpacing(3)
        pref_visual_stim_box.setLayout(pref_visual_stim_layout)
        
        pref_visual_stim_box.setStyleSheet(GROUP_BOX_STYLES['cypher'])
        
        GC1 = QGroupBox("RGC 1")
        GC1.setFixedSize(95, 95)  
        GC1_layout = QVBoxLayout()
        GC1_layout.setContentsMargins(0, 0, 0, 0)  
        GC1.setLayout(GC1_layout)
        GC1.setStyleSheet("""border: 1px transparent;""")
        
        GC1_layout.addWidget(StimWidget(RGC_1_pref_stim), alignment=Qt.AlignCenter)
        GC2 = QGroupBox("RGC 2")
        GC2.setFixedSize(95, 95)  
        GC2_layout = QVBoxLayout()
        GC2_layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        GC2.setLayout(GC2_layout)
        
        GC2.setStyleSheet("""border: 1px transparent;""")
        GC2_layout.addWidget(StimWidget(RGC_2_pref_stim), alignment=Qt.AlignCenter)
        pref_visual_stim_layout.addWidget(GC1, alignment=Qt.AlignCenter)
        pref_visual_stim_layout.addWidget(GC2, alignment=Qt.AlignCenter)
        self.layout.addWidget(pref_visual_stim_box)

        retinaBox_output_box = QGroupBox("Code Book")
        retinaBox_output_box.setFixedHeight(250)
        output_layout = QVBoxLayout()  
        output_layout.setContentsMargins(3, 3, 3, 3)  
        output_layout.setAlignment(Qt.AlignCenter)  
        retinaBox_output_box.setLayout(output_layout)
        
        # Style the Code Book box
        retinaBox_output_box.setStyleSheet(GROUP_BOX_STYLES['default'])
        retinaBox_output_box.setStyleSheet("""border: 1px transparent;""")


        table = QTableWidget(4,3) 
        table.setFixedHeight(185)  
        table.setHorizontalHeaderLabels(['RGC1', 'RGC2', 'Letter'])
        table.verticalHeader().setVisible(False)  
    
        table.setStyleSheet(TABLE_STYLES['cypher'])
        
        for i in range(4):
            table.setRowHeight(i, 30)  
        table.setColumnWidth(0, 65)  # RGC1 column 
        table.setColumnWidth(1, 65)  # RGC2 column   
        table.setColumnWidth(2, 85)  # Letter column 
        
        # Disable scrollbars to prevent extra space
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
        # Create the table data showing the mapping clearly
        table_data = [
            ['0', '0', RetinaBox_output[0]],  # (0,0) -> first letter
            ['1', '0', RetinaBox_output[1]],  # (1,0) -> second letter  
            ['0', '1', RetinaBox_output[2]],  # (0,1) -> third letter
            ['1', '1', RetinaBox_output[3]]   # (1,1) -> fourth letter
        ]
        
        for row in range(4):
            for col in range(3):
                item = QTableWidgetItem(table_data[row][col])
                item.setTextAlignment(Qt.AlignCenter)
                if col == 2:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                table.setItem(row, col, item)

        output_layout.addWidget(table, alignment=Qt.AlignCenter)  
        self.layout.addWidget(retinaBox_output_box)

class CodeBreakerWidget(QWidget):
    """Code Breaker as a widget for tab integration"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['white']};
                font-family: '{FONTS['family']}';
            }}
        """)
        
        # Current challenge data
        self.current_challenge = "Challenge 1"
        self.possible_letters = None
        
        # Create main layout once
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5,3,5,5)
        self.main_layout.setSpacing(2)
        self.setLayout(self.main_layout)
        
        # Setup toolbar and initial content
        self.setup_toolbar()
        self.load_challenge(self.current_challenge)
        
    def setup_toolbar(self):
        """Setup the toolbar with challenge selector"""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Challenge selector
        challenge_label = QLabel("Challenge:")
        challenge_label.setStyleSheet(f"""
            color: {COLORS['black']};
            font-family: '{FONTS['family']}';
            font-size: 15px;
            background-color: transparent;
            padding: 5px;
        """)
        
        self.challenge_combo = QComboBox()
        self.challenge_combo.setFixedSize(160, 30)
        self.challenge_combo.addItems(["Challenge 1", "Challenge 2", "Challenge 3", "Challenge 4", "Challenge 5", "Challenge 6"])
        self.challenge_combo.currentTextChanged.connect(self.load_challenge)
        
        toolbar_layout.addWidget(challenge_label)
        toolbar_layout.addWidget(self.challenge_combo)
        toolbar_layout.addStretch() 
        
        toolbar_widget.setLayout(toolbar_layout)
        self.main_layout.addWidget(toolbar_widget)

    def load_challenge_data(self):
        """Load challenge data from JSON file"""
        try:
            GUI_path = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(GUI_path, ".default_code", ".default_codeBreaker_challenges.json")
            with open(json_path, 'r') as f:
                data = json.load(f)
                return data[self.current_challenge]
            
        except Exception as e:
            print(f"Error loading challenges from JSON: {e}")
        
        return 0
        
    def parse_solution_string(self, solution_string, possible_letters):
        """
        Parse solution string considering multi-character letters in possible_letters.
        
        Args:
            solution_string: The string to parse (e.g., "Bake a cake")
            possible_letters: List of possible letters/tokens (e.g., ["A", "B", "C", "KE"])
        
        Returns:
            List of tokens where multi-character letters are treated as single units
        """
        # Sort possible letters by length (longest first) to prioritize multi-character matches
        sorted_letters = sorted(possible_letters, key=len, reverse=True)
        
        tokens = []
        i = 0
        
        while i < len(solution_string):
            char = solution_string[i]
            
            if char == ' ':
                tokens.append(' ')
                i += 1
                continue
                
            # Try to match multi-character letters first
            matched = False
            for letter in sorted_letters:
                if len(letter) > 1 and i + len(letter) <= len(solution_string):
                    if solution_string[i:i+len(letter)].upper() == letter.upper():
                        tokens.append(letter.upper())
                        i += len(letter)
                        matched = True
                        break
            
            # If no multi-character match, try single characters
            if not matched:
                if char.upper() in [letter.upper() for letter in sorted_letters]:
                    tokens.append(char.upper())
                else:
                    tokens.append(char)  # Keep unknown characters as-is
                i += 1
        
        return tokens
        
    def load_challenge(self, challenge_name):
        """Safely clear current content and load new challenge""" 
        # Store current challenge
        self.current_challenge = challenge_name
        challenge_data = self.load_challenge_data()
        
        # Clear existing content safely
        self.clear_content()
        
        # Create new content based on challenge
        self.build_challenge_content(challenge_data)
        
    def clear_content(self):
        """Safely remove all current widgets except toolbar"""
        # Clear all widgets from main layout except the toolbar (first item)
        while self.main_layout.count() > 1:  # Keep toolbar, remove everything else
            child = self.main_layout.takeAt(1)  # Always take the second item (after toolbar)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
                
    def clear_layout(self, layout):
        """Helper method to recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())
            
    def build_challenge_content(self, challenge_data):
        """Build the challenge interface based on challenge data"""
        # Create the main content layout
        main_content_widget = QWidget()
        main_content_widget.setStyleSheet("background-color: transparent;")
        main_layout = QHBoxLayout()
        main_content_widget.setLayout(main_layout)

        # Create code container with stim codes
        code_container = QGroupBox("Secret Code")
        code_container.setFixedWidth(700)
        code_container.setStyleSheet(GROUP_BOX_STYLES['default'])

        code_layout = QGridLayout()
        code_layout.setSpacing(3) 
        code_layout.setContentsMargins(2,2,2,2)  
        code_container.setLayout(code_layout)

        # Add stim code widgets based on challenge
        self.possible_letters = challenge_data['RetinaBox_output']
        stim_code_copy = copy.deepcopy(challenge_data['stim_codes'])  

        # Parse solution string considering multi-character letters
        solution_tokens = self.parse_solution_string(challenge_data['Solution_string'], self.possible_letters)
        grid_coordinates = self.get_grid_layout(solution_tokens)

        for i, token in enumerate(solution_tokens):
            if token.upper() in [letter.upper() for letter in self.possible_letters]:  # Case-insensitive check
                if token.upper() in stim_code_copy and len(stim_code_copy[token.upper()]) > 0:
                    stim_widget = StimCodeWidget(stim_code_copy[token.upper()].pop(0), token.upper(), self)
                else:
                    stim_widget = StimCodeWidget([0,0,0,0,0,0,0,0,0], token.upper(), self)
            elif token == ' ': 
                stim_widget = StimCharWidget(' ')
            else:
                stim_widget = StimCharWidget(token)
            code_layout.addWidget(stim_widget, *grid_coordinates[i])  # Unpack coordinates tuple

        main_layout.addWidget(code_container)

        # Create cypher widget
        cypher_widget = CypherWidget(
            challenge_data["RGC_1_pref_stim"],
            challenge_data["RGC_2_pref_stim"], 
            challenge_data["RetinaBox_output"]
        )
        container = QVBoxLayout()
        container.addWidget(cypher_widget)

        # Add submit/check button
        check_button = QPushButton("Check Answers")
        check_button.setStyleSheet(BUTTON_STYLES['primary'])
        check_button.clicked.connect(self.check_all_answers)
        container.addWidget(check_button)

        main_layout.addLayout(container)

        # Add main content to the persistent main layout
        self.main_layout.addWidget(main_content_widget)
    
    def get_grid_layout(self, tokens):
        """
        Calculate grid coordinates for widgets, keeping words intact.
        
        Args:
            tokens: List of tokens (letters/multi-character letters and spaces)
        
        Returns: List of (row, col) tuples for each token
        """
        widgets_per_row = 700 // 80   
        
        coordinates = []
        row, col = 0, 0
        
        # Process each token directly to ensure we get coordinates for all tokens
        i = 0
        while i < len(tokens):
            if tokens[i] == ' ':
                # Check if space fits on current row
                if col >= widgets_per_row:
                    row += 1
                    col = 0
                # Add coordinate for space
                coordinates.append((row, col))
                col += 1
                i += 1
            else:
                # Start of a word - collect all non-space tokens
                word_start = i
                word_tokens = []
                while i < len(tokens) and tokens[i] != ' ':
                    word_tokens.append(tokens[i])
                    i += 1
                
                # Check if ENTIRE word fits on current row (including current position)
                if col + len(word_tokens) > widgets_per_row:
                    row += 1
                    col = 0
                
                # Add coordinates for each token in the word
                for token in word_tokens:
                    coordinates.append((row, col))
                    col += 1
        
        # Optional: warn if too many rows
        if row >= 5:  # ~5 rows max for 500px height
            print(f"Warning: {row + 1} rows needed, may not fit on screen")
        
        return coordinates 

    def check_all_answers(self):
        """Check all user answers in current challenge"""
        # Find all StimCodeWidget instances
        stim_widgets = self.findChildren(StimCodeWidget)
        
        correct_count = 0
        total_count = len(stim_widgets)
        
        for widget in stim_widgets:
            if widget.check_user_selection():
                correct_count += 1
                
        # Show result
        QMessageBox.information(self, "Results", 
                              f"Correct letters: {correct_count}/{total_count}")
                              
    def get_current_challenge(self):
        """Get the currently selected challenge name"""
        return self.current_challenge