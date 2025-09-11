COLORS = {
    'blue': '#1A83C9',
    'red': '#CD1916',
    'orange': '#E94D15',
    'lightGreen': '#3D783F',
    'darkGreen': '#1D341E',
    'black': '#000000',
    'darkBrown': '#593B25',
    'lightBrown': '#B67E54',
    'yellow': '#DEB33D',
    'gray': '#BDBFB6',
    'lightGray': '#E0E0E0',
    'lighterGray': "#F2F2F2",
    'white': '#F5F3F3'
}


FONTS = {
    'family': 'Asap',
    'sizes': {
        'small': 14,
        'medium': 25,
        'large': 48
    },
    'weights': {
        'extraLight': 25,
        'thin': 25,
        'regular': 50,
        'medium': 57,
        'semiBold': 63,
        'bold': 75,
        'extraBold': 87
    }
}

BUTTON_STYLES = {
    'primary': f"""
        QPushButton {{
            background-color: {COLORS['gray']};
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-family: '{FONTS['family']}';
        }}
        QPushButton:hover {{
            background-color: {COLORS['lightGray']};
        }}
    """, 
    'secondary': f"""
    QPushButton {{
        background-color: {COLORS['lighterGray']};
        border: 1px solid {COLORS['gray']};
        border-radius: 5px;
        padding: 4px;
        font-family: '{FONTS['family']}';
        font-size: {FONTS['sizes']['small']}px;
        color: {COLORS['black']};
    }}
    QPushButton:hover {{
        background-color: {COLORS['lightGray']};
    }}
    QPushButton:pressed,
    QPushButton:checked {{
        background-color: {COLORS['blue']};      
        color: {COLORS['white']};                 
    }}
""",
    'third': f"""
        QPushButton {{
            background-color: {COLORS['lighterGray']};
            border: 1px solid {COLORS['gray']};
            border-radius: 5px;
            padding: 4px;
            font-family: '{FONTS['family']}';
            font-size: 12px;
            color: {COLORS['black']};
        }}
        QPushButton:hover {{
            background-color: {COLORS['lightGray']};
        }}
        QPushButton:pressed,
        QPushButton:checked {{
            background-color: {COLORS['blue']};      
            color: {COLORS['white']};                 
            border: 1px solid {COLORS['darkGreen']};  
        }}
    """,
    'code_breaker': f"""
    QPushButton {{
        background-color: {COLORS['gray']};
        border: none;
        border-radius: 5px;
    }}
    QPushButton:checked {{
        background-color: {COLORS['yellow']};
    }}
""",
    'discovery_test': f"""
        QPushButton {{
            font-family: '{FONTS['family']}';
            font-size: 12px;
            font-weight: bold;
            background-color: {COLORS['lightGray']};
            color: {COLORS['black']};
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
        }}
        QPushButton:hover {{
            background-color: {COLORS['blue']};
            color: {COLORS['white']};
        }}
        QPushButton:pressed {{
            background-color: {COLORS['darkGreen']};
        }}
    """,
    'stim_off': f"""
        QPushButton {{
            background-color: gray;
            border-radius: 15px;
        }}
    """,
    'stim_excitatory': f"""
        QPushButton {{
            background-color: red;
            color: white;
            font-weight: bold;
            border-radius: 15px;
        }}
    """,
    'stim_inhibitory': f"""
        QPushButton {{
            background-color: blue;
            color: white;
            font-weight: bold;
            border-radius: 15px;
        }}
    """,
    'discovery_grid': f"""
        QPushButton {{
            font-family: '{FONTS['family']}';
            background-color: #808080;
            border: 2px solid #606060;
            border-radius: 8px;
            padding: 2px;
            color: {COLORS['white']};
        }}
        QPushButton:hover {{
            background-color: #a0a0a0;
            border: 2px solid #707070;
        }}
        QPushButton:checked {{
            background-color: #FDFF6E;
            border: 2px solid {COLORS['gray']};
            color: {COLORS['black']};
        }}
        QPushButton:pressed {{
            background-color: #d0d0d0;
        }}
    """
}

GROUP_BOX_STYLES = {  
    'default': """
        QGroupBox {
            border: 1px solid #aaaaaa;
            border-radius: 4px;
            margin-top: 1em;
            padding: 8px;
            background-color: #F2F2F2;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 8px;
            background-color: transparent;
            font-size: 14px;
            color: #333333;
        }
    """, 
    'LED_container': """
        QWidget {
            background-color: #f5f5f5;
            border: 2px solid #dddddd;  /* Light gray border */
            border-radius: 10px;
            padding: 10px;
        }
    """,
    'cypher': f"""
        QGroupBox#SecretCodeGroupBox {{
            font-family: '{FONTS['family']}';
            border: 2px solid {COLORS['gray']};      
            border-radius: 6px;
            text-align: center;
            background-color: transparent;
        }}
        QGroupBox::title#SecretCodeGroupBox {{
            font-family: '{FONTS['family']}';
            text-align: center;
            font-size: {FONTS['sizes']['small']}px;
            background-color: transparent;
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 2 5px 2 5px;
        }}
    """,
    'discovery_panel': f"""
        QGroupBox {{
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
            font-weight: bold;
            color: {COLORS['black']};
            border: 2px solid {COLORS['lightGray']};
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 15px;
            background-color: {COLORS['white']};
        }}
        QGroupBox::title {{
            font-family: '{FONTS['family']}';
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px 10px 0;
            background-color: transparent;
            font-weight: bold;
        }}
    """,
    'discovery_instructions': f"""
        QGroupBox {{
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
            font-weight: bold;
            color: {COLORS['black']};
            border: 2px solid {COLORS['lightGray']};
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 5px;
            background-color: {COLORS['lighterGray']};
        }}
        QGroupBox::title {{
            font-family: '{FONTS['family']}';
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px 0 10px;
            background-color: transparent;
            font-weight: bold;
        }}
    """,
    'discovery_sub_panel': f"""
        QGroupBox {{
            font-family: '{FONTS['family']}';
            font-size: 12px;
            font-weight: bold;
            color: {COLORS['black']};
            margin-top: 15px;
            border: 1px solid {COLORS['gray']};
            border-radius: 5px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            font-family: '{FONTS['family']}';
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
    """,
    'discovery_controls_panel': f"""
        QWidget {{
            font-family: '{FONTS['family']}';
            background-color: #404040;
            border: 2px solid #505050;
            border-radius: 10px;
            padding: 10px;
        }}
        QLabel {{
            color: white;
            background-color: transparent;
        }}
    """
}

LEGEND_STYLES = {
    'stim_legend': """
            QLabel {
                font-size: 11px;
                background-color: transparent;
                color: #333333;
            }
        """,
    'discovery_instructions': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            font-size: 15px;
            color: {COLORS['black']};
            background-color: transparent;
            padding: 0px;
            line-height: 1.0;
        }}
    """,
    'discovery_title': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            font-size: 12px;
            font-weight: bold;
            color: {COLORS['black']};
        }}
    """,
    'discovery_legend': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            font-size: 10px;
            color: {COLORS['black']};
        }}
    """,
    'discovery_legend_white': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            font-size: 10px;
            font-weight: bold;
            color: white;
            padding: 1px;
        }}
    """,
    'discovery_controls_title': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            font-size: 11px;
            font-weight: bold;
            color: #F5F3F3;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 2px;
        }}
    """,
    'toolbar_lives': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            color: #28a745;
            font-weight: bold;
            padding: 8px 15px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}
    """,
    'toolbar_lives_warning': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            color: #dc3545;
            font-weight: bold;
            padding: 8px 15px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
        }}
    """,
    'toolbar_lives_white': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            color: #28a745;
            font-weight: bold;
            padding: 8px 15px;
            background-color: #505050;
            border: 1px solid #606060;
            border-radius: 4px;
        }}
    """,
    'toolbar_lives_warning_white': f"""
        QLabel {{
            font-family: '{FONTS['family']}';
            color: #ff6b6b;
            font-weight: bold;
            padding: 8px 15px;
            background-color: #505050;
            border: 1px solid #606060;
            border-radius: 4px;
        }}
    """
}

DROPDOWN_STYLES = {
    'default': f"""
        QComboBox {{
            background-color: {COLORS['gray']};
            border: none;
            border-radius: 5px;
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
            color: {COLORS['black']};
        }}
        QComboBox:hover {{
            background-color: {COLORS['lightGray']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox::down-arrow {{
            width: 12px;
            height: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['white']};
            border: 1px solid {COLORS['lightGray']};
            selection-background-color: {COLORS['blue']};
            selection-color: {COLORS['white']};
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
        }}
    """, 
    'secondary': f"""
        QComboBox {{
            background-color: {COLORS['lighterGray']};  
            border: 1px solid {COLORS['gray']};
            border-radius: 5px;
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
        }}
        QComboBox:hover {{
            background-color: {COLORS['lightGray']};    
        }}
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['white']};
            selection-background-color: {COLORS['white']};
            selection-color: {COLORS['black']};
            border: 1px solid {COLORS['gray']};
        }}
    """,
    'dark_panel': f"""
        QComboBox {{
            background-color: {COLORS['lighterGray']};  
            border: 1px solid {COLORS['gray']};
            border-radius: 5px;
            font-family: '{FONTS['family']}';
            font-size: 12px;
            padding: 2px 5px;
            margin: 0px;
        }}
        QComboBox:hover {{
            background-color: {COLORS['lightGray']};    
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            padding: 0px;
            margin: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {COLORS['white']};
            selection-background-color: {COLORS['blue']};
            selection-color: {COLORS['white']};
            border: 1px solid {COLORS['gray']};
            padding: 1px;
            margin: 0px;
        }}
    """
}   

TABLE_STYLES = {
    'cypher': f"""
        QTableWidget {{
            font-family: '{FONTS['family']}';
            gridline-color: #cccccc;
            background-color: {COLORS['white']};
            alternate-background-color: {COLORS['lighterGray']};
            border: 1px solid #cccccc;
            border-radius: 4px;
        }}
        QTableWidget::item {{
            text-align: center;
            font-family: '{FONTS['family']}';
            padding: 4px;
            border: none;
        }}
        QTableWidget::item:selected {{
            background-color: {COLORS['blue']};
            color: {COLORS['white']};
        }}
        QHeaderView::section {{
            font-family: '{FONTS['family']}';
            text-align: center;
            background-color: {COLORS['lightGray']};
            padding: 6px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }}
    """
}


TOOLBARS = {
    'retinaLab': f"""
        QToolBar {{
            background-color: {COLORS['lightGray']};
            border: 1px solid {COLORS['lightGray']};
            spacing: 0px;
        }}
    """
}

MENU_STYLES = {
    'default': f"""
        QMenu {{
            font-family: '{FONTS['family']}';
        }}
        QMenu::item {{
            font-family: '{FONTS['family']}';
            padding: 6px 10px;
            color: black;
        }}
        QMenu::item:selected {{
            background-color: {COLORS['blue']};
            color: white;
        }}
        QMenu::item:hover {{
            background-color: {COLORS['blue']};
            color: white;
        }}
    """
}

TOOLBAR_BUTTON_STYLES = {
    'default': f"""
        QToolButton {{
            background-color: transparent;
            border: 1px solid {COLORS['gray']};
            border-radius: 6px;
            padding: 3px 8px;
            margin: 1px;
            font-family: '{FONTS['family']}';
            font-size: 10px;
            color: {COLORS['black']};
        }}
        QToolButton:hover {{
            background-color: {COLORS['gray']};
        }}
        QToolButton:pressed {{
            background-color: {COLORS['lighterGray']};
        }}
        QToolButton::menu-indicator {{
            image: none;
            width: 0px;
            height: 0px;
        }}
        QToolButton::menu-arrow {{
            image: none;
            width: 0px;
            height: 0px;
        }}
    """
}

TAB_STYLES = {
    'default': f"""
        QTabWidget::pane {{
            border: 1px solid {COLORS['gray']};
            background-color: {COLORS['white']};
            top: -1px;
        }}
        
        QTabBar::tab {{
            background-color: {COLORS['lightGray']};
            border: 1px solid {COLORS['gray']};
            border-bottom: none;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 120px;
            min-height: 24px;
            max-height: 24px;
            padding: 6px 16px;
            margin-right: 2px;
            font-family: '{FONTS['family']}';
            font-size: {FONTS['sizes']['small']}px;
            font-weight: {FONTS['weights']['medium']};
            color: {COLORS['black']};
        }}
        
        QTabBar::tab:selected {{
            background-color: {COLORS['white']};
            border-bottom: 1px solid {COLORS['white']};
            margin-bottom: -1px;
            font-weight: {FONTS['weights']['bold']};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: #E8E8E8;
        }}
    """
}