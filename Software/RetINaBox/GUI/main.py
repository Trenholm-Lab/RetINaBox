import sys
import os
from gui_app import *


if __name__ == "__main__":
    retinaBox_GUI = QApplication([])
    retinaBox_GUI.setStyle("Fusion")
    
    homeWindow = HomeWindow()
    homeWindow.show()
    sys.exit(retinaBox_GUI.exec_())