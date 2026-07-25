import sys
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox
from PyQt6.QtCore import pyqtSlot, Qt, QThread
from RocketDataAnalyzer import RocketDataAnalyzer
from SerialReader import SerialReader
from BoardConnector import ConnectionWindow
import pandas as pd


dataValues = [
    "Rocket State", "Kalman Altitude", "Baro Altitude",
    "Accel X", "Accel Y", "Accel Z", "Accel Mag",
    "Gyro X", "Gyro Y", "Gyro Z", "Gyro Mag",
    "Mag X", "Mag Y", "Mag Z", "Mag Mag",
    "Vertical Velocity", "Vertical Accel",
    "Drogue Cont", "Drogue Deploy", "Main Cont", "Main Deploy"
]

class MissionControl(QWidget):
    
    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.requestedSensors = []
        self.DevicePort = None
        self.DeviceBaud = None
        self.FilePath = None

        # self.setWindowTitle("Altitude Rocketry Mission Control")
        # self.resize(1200, 800)
        # self.setStyleSheet("background-color: #121212; color: white;")

        # self.Central_Widget = QWidget()
        # self.setCentralWidget(self.Central_Widget)
        self.MainLayout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("DATA ANALYZR")

        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00FF66; letter-spacing: 1px;")

        btn_back = QPushButton("MAIN MENU")
        if self.controller:
            btn_back.clicked.connect(lambda: self.controller.show_main_menu())

        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_back)
        self.MainLayout.addLayout(header)
        

        self.ContentLayout = QHBoxLayout()
        # --- SIDEBAR (Left) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #1e1e1e; border-right: 1px solid #333;")

        # The master layout for the sidebar that holds the two sections
        self.sidebar_master_layout = QVBoxLayout(self.sidebar)
        self.sidebar_master_layout.setContentsMargins(0, 0, 0, 0)
        self.sidebar_master_layout.setSpacing(0)

        # ---------------------------------------------------------
        # SECTION 1: TOP HALF
        # ---------------------------------------------------------
        self.section_top = QFrame()
        # Adding a border-bottom to visually divide the two halves
        self.section_top.setStyleSheet("border-bottom: 1px solid #333;")
        self.top_lay = QVBoxLayout(self.section_top)
        
        self.top_lay.addWidget(self.create_label("FLIGHT CONTROLS"))
        # self.SerialSelector = QComboBox()

        # self.updatePorts()

        # self.SerialSelector.currentTextChanged.connect(self.SerialSelector)
        # self.BaudSelector = QComboBox()
        # self.BaudSelector.addItems(["9600", "115200"])

        self.ConnectBoardBtn = self.create_sidebar_button("CONNECT BOARD", "#007acc")
        self.FlashDumpBtn = self.create_sidebar_button("FLASH DUMP", "#444")
        # self.top_lay.addWidget(self.SerialSelector)
        # self.top_lay.addWidget(self.BaudSelector)
        self.top_lay.addWidget(self.ConnectBoardBtn)
        self.top_lay.addWidget(self.FlashDumpBtn)

        self.ConnectBoardBtn.setCheckable(True)
        self.ConnectBoardBtn.clicked.connect(self.ConnectionManager)
        self.ConnectionWindow = None

        self.FlashDumpBtn.setCheckable(True)
        self.FlashDumpBtn.clicked.connect(self.DumpClicked)
        
        # This stretch pins the buttons above it to the top of the TOP HALF
        self.top_lay.addStretch()

        # ---------------------------------------------------------
        # SECTION 2: BOTTOM HALF
        # ---------------------------------------------------------
        self.section_bottom = QFrame()
        self.bottom_lay = QVBoxLayout(self.section_bottom)
        
        self.bottom_lay.addWidget(self.create_label("Data"))

        self.checkboxes = {}
        for name in dataValues:
            cb = QCheckBox(text=name)
            self.checkboxes[name] = cb
            self.bottom_lay.addWidget(cb) # Or whichever layout you prefer
        
        # This stretch pins the buttons above it to the top of the BOTTOM HALF
        self.bottom_lay.addStretch()

        self.UpadteBtn = self.create_sidebar_button("Update","#00a0cc")
        self.ResetBtn = self.create_sidebar_button("Reset","#cc1f00")

        self.bottom_lay.addWidget(self.UpadteBtn)
        self.bottom_lay.addWidget(self.ResetBtn)

        self.UpadteBtn.setCheckable(True)
        self.UpadteBtn.clicked.connect(self.UpdateGraphVariables)
        self.ResetBtn.setCheckable(True)
        self.ResetBtn.clicked.connect(self.DumpClicked)

        # Add both sections to the master sidebar layout
        self.sidebar_master_layout.addWidget(self.section_top,1)
        self.sidebar_master_layout.addWidget(self.section_bottom,3)
        # self.sidebar_layout = QVBoxLayout(self.sidebar)
        # self.sidebar_layout.setContentsMargins(15,20,15,20)

        
        # self.btn_dump = QPushButton("START DUMP")
        # self.btn_dump.setStyleSheet("""
        #     QPushButton { background-color: #007acc; border-radius: 5px; padding: 10px; font-weight: bold; }
        #     QPushButton:hover { background-color: #005f99; }
        # """)
        # self.btn_dump.setCheckable(True)
        # self.btn_dump.clicked.connect(self.buttonClicked)
        # self.btn_dump.clicked.connect(self.the_button_was_toggled)
        # self.SerialSelector = QComboBox()

        # self.updatePorts()

        # # self.SerialSelector.currentTextChanged.connect(self.SerialPortSelector)


        # self.sidebar_layout.addWidget(self.btn_dump)
        # self.sidebar_layout.addWidget(self.SerialSelector)
        # self.sidebar_layout.addStretch() # Pushes button to top

        # --- CONTENT AREA (Right) ---
        self.analyzer = RocketDataAnalyzer()
        
        # Add Widgets to Main Layout
        self.ContentLayout.addWidget(self.sidebar)
        self.ContentLayout.addWidget(self.analyzer)

        self.MainLayout.addLayout(self.ContentLayout)

    def ConnectionManager(self):
        
        if self.ConnectionWindow is None:
             self.ConnectionWindow = ConnectionWindow()
        
        self.ConnectionWindow.connection_submitted.connect(self.GetPopUpData)
        self.ConnectionWindow.file_loaded.connect(self.GetFile)

        self.ConnectionWindow.show()


    def UpdateGraphVariables(self):
        self.requestedSensors = [name for name, cb in self.checkboxes.items() if cb.isChecked()]
        # print(self.requestedSensors)
        try:
            self.analyzer.updateGraphVariables(self.requestedSensors, self.FilePath)
        except:
            if self.FilePath is None:
                msg = QMessageBox(self)
                msg.setWindowTitle("Data Import")
                msg.setText(f"File Path not empty")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.show() # Use show() instead of exec() if you don't want to block the code
    def GetFile(self,path):
        self.FilePath = path
        try:
            # Load the data from the chosen directory
            df = pd.read_csv(path)
            
            # Validation for your new 19-variable structure
            if len(df.columns) == 19:
                # This shows the message for 5000 milliseconds (5 seconds) then clears itself
                # self.statusBar().showMessage(f"Successfully loaded: {path.split('/')[-1]}", 5000)
                msg = QMessageBox(self)
                msg.setWindowTitle("Data Import")
                msg.setText(f"Flight log imported correctly.\nRows detected: {len(df)}")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.show() # Use show() instead of exec() if you don't want to block the code

            else:
                msg = QMessageBox(self)
                msg.setWindowTitle("Data Import")
                msg.setText(f"Flight log Import Failed")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.show() # Use show() instead of exec() if you don't want to block the code
        except Exception as e:
            # self.statusBar().showMessage("File Load Failed!", 3000)
            msg = QMessageBox(self)
            msg.setWindowTitle("Data Import")
            msg.setText(f"Flight log Failed")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.show() # Use show() instead of exec() if you don't want to block the code

    def GetPopUpData(self, port, baud, path):
        self.DevicePort = port
        self.DeviceBaud = baud
        self.FilePath = path

        print(path)

    def ResetAll(self):
         pass
    def create_label(self, text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #666; font-weight: bold; font-size: 10px; margin-top: 10px;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return lbl
    
    def create_sidebar_button(self, text, color):
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 4px;
                    padding: 11px;
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
    def updatePorts(self):
        self.SerialSelector.clear()
        
        ports = serial.tools.list_ports.comports()

        for port in ports:
            displayText = f"{port.device}"
            self.SerialSelector.addItem(displayText)

    def buttonClicked(self):
        self.DevicePort = self.SerialSelector.currentText()
        self.DeviceBaud = int(self.BaudSelector.currentText())


        # self.ser.data_received.connect(self.process_incoming_data)
        # self.ser.error.connect(self.handle_serial_error)

        self.ConnectBoardBtn.setEnabled(False) # Prevent double connection

    def DumpClicked(self):
        
        try:
            if type(self.DevicePort)  is not str and type(self.DeviceBaud)  is not int :
                msg = QMessageBox(self)
                msg.setWindowTitle("Failure")
                msg.setText(f"No Device Port and Baud rate")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.show() # Use show() instead of exec() if you don't want to block the code
            else:
                self.thread = QThread()
                self.ser = SerialReader(self.DevicePort, self.DeviceBaud, self.FilePath)
                self.ser.moveToThread(self.thread)
                self.thread.started.connect(self.ser.StartDataDump)
                self.ser.finished.connect(self.thread.quit)
                self.ser.finished.connect(self.ser.deleteLater)
                self.thread.finished.connect(self.thread.deleteLater)
                self.ser.finished.connect(self.DumpComplete)
                self.thread.start()
        except Exception as e:
            if type(self.DevicePort)  is not str and type(self.DeviceBaud)  is not int :
                msg = QMessageBox(self)
                msg.setWindowTitle("Failure")
                msg.setText(f"No Device Port and Baud rate")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.show() # Use show() instead of exec() if you don't want to block the code

    def DumpComplete(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Dump Status")
        msg.setText(f"Dump finished. Analyzing file...")
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.show() # Use show() instead of exec() if you don't want to block the code
        # print("Dump finished. Analyzing file...")
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MissionControl()
    window.show()
    sys.exit(app.exec())