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
from NotifacationWindow import NotificationCenter
import UpdateCheck as UpdateCheck

class WindowSelector(QWidget):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        # self.setWindowTitle("Altitude Rocketry Mission Control")
        # self.resize(1200, 800)
        # self.setStyleSheet("background-color: #121212; color: white;")
        self.MasterLayout = QVBoxLayout(self)
        topFrame = QHBoxLayout()

        notificationsBtn = self.createBtn("Notifications", "#b73e0e")
        topFrame.addStretch()
        topFrame.addWidget(notificationsBtn)

        notificationsBtn.clicked.connect(self.toggle_drawer)

        self.MasterLayout.addLayout(topFrame)

        self.lay = QHBoxLayout()

        self.DataAnalyzerBtn = self.createBtn("Data Analyzer" , "#007acc")
        self.TestStandBtn = self.createBtn("Test Stand", "#e48209")

        self.lay.addWidget(self.DataAnalyzerBtn)
        self.lay.addWidget(self.TestStandBtn)
        self.MasterLayout.addLayout(self.lay)

        self.MasterLayout.addStretch()

        self.DataAnalyzerBtn.setCheckable(True)
        self.DataAnalyzerBtn.clicked.connect(lambda: self.controller.show_analyzer_screen())

        self.TestStandBtn.setCheckable(True)
        self.TestStandBtn.clicked.connect(lambda: self.controller.show_test_stand_screen())

        self.NotificationCenter = NotificationCenter(self.controller, close_callback=self.toggle_drawer)

        self.MasterLayout.addWidget(self.NotificationCenter)
        self.NotificationCenter.hide()
    
    def toggle_drawer(self):
            """Controls displaying or collapsing your custom drawer class"""
            print("hola?")
            if self.NotificationCenter.isVisible():
                self.NotificationCenter.hide()
            else:
                # Safely trigger data collection parsing before sliding open
                self.NotificationCenter.refresh_notifications()
                self.NotificationCenter.show()

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
        self.setWindowTitle("Ground Station")
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
        self.UpdateAvailable = UpdateCheck.CheckForUpdate()
        print(self.UpdateAvailable)
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
    window.show()
    sys.exit(app.exec())