import sys
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox, QStackedWidget
from PyQt6.QtCore import pyqtSlot, Qt, QThread
from RocketDataAnalyzer import RocketDataAnalyzer
from SerialReader import SerialReader
from BoardConnector import ConnectionWindow
import pandas as pd
from FileAnalyzer import MissionControl
from testStandDisplay import TestStand
import UpdateCheck as UpdateCheck

class WindowSelector(QWidget):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        # self.setWindowTitle("Altitude Rocketry Mission Control")
        # self.resize(1200, 800)
        # self.setStyleSheet("background-color: #121212; color: white;")

    

        self.lay = QHBoxLayout(self)

        self.DataAnalyzerBtn = self.createBtn("Data Analyzer" , "#007acc")
        self.TestStandBtn = self.createBtn("Test Stand", "#e48209")

        self.lay.addWidget(self.DataAnalyzerBtn)
        self.lay.addWidget(self.TestStandBtn)

        self.DataAnalyzerBtn.setCheckable(True)
        self.DataAnalyzerBtn.clicked.connect(lambda: self.controller.show_analyzer_screen())

        self.TestStandBtn.setCheckable(True)
        self.TestStandBtn.clicked.connect(lambda: self.controller.show_test_stand_screen())



    def createBtn(self, text, color):
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 10px;
                    padding: 20px;
                    font-size: 10px;
                    font-weight: bold;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #555;
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            return btn

class WindowController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vanguard Ground Station")
        self.resize(1200, 800)
        
        # Create the central layout container
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Instantiate views, passing 'self' (the controller) so they can trigger switches
        self.MenuView = WindowSelector(self)
        self.DataAnalyzer = MissionControl(self)
        self.TestStand = TestStand(self)
        
        # Add views to the stack (PyQt assigns them indices: 0, 1, 2)
        self.stacked_widget.addWidget(self.MenuView)       # Index 0
        self.stacked_widget.addWidget(self.DataAnalyzer)   # Index 1
        self.stacked_widget.addWidget(self.TestStand) # Index 2
        
        # Start at the Main Menu
        self.show_main_menu()

    # View Switcher Functions
    def show_main_menu(self):
        self.stacked_widget.setCurrentIndex(0)
    
    def show_analyzer_screen(self):
        self.stacked_widget.setCurrentIndex(1)
        
    def show_test_stand_screen(self):
        self.stacked_widget.setCurrentIndex(2)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WindowController()
    UpdateCheck.CheckForUpdate()
    window.show()
    sys.exit(app.exec())