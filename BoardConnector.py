from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QFileDialog, QLabel, QFrame,QMessageBox
from PyQt6.QtSerialPort import QSerialPortInfo
from PyQt6.QtCore import Qt, pyqtSignal



class ConnectionWindow(QWidget):
    connection_submitted = pyqtSignal(str, int, str)
    file_loaded = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.FilePath = None
        self.setWindowTitle("Board Connection & Data Import")
        self.setFixedSize(400,300)
        # self.sectionTop = QFrame()
        self.PopUp = QVBoxLayout()

        self.PopUp.addWidget(self.create_label("Select Flight computer Port & Baud Rate"))
        self.ComPorts = QComboBox()
        self.BaudRates = QComboBox()
        self.BaudRates.addItems(["9600", "115200"])
        self.SelectPorts()
        self.PopUp.addWidget(self.ComPorts)
        self.PopUp.addWidget(self.BaudRates)

        self.SaveBtn = self.CreateButton("File Save Location", "#3707b3")
        self.ConnectBtn = self.CreateButton("CONNECT BOARD", "#007acc")
        self.PopUp.addWidget(self.SaveBtn)
        self.PopUp.addWidget(self.ConnectBtn)
        self.ConnectBtn.clicked.connect(self.ConnectBoard)
        self.SaveBtn.clicked.connect(self.SetSaveLocation)

        # --- Divider ---
        line = QLabel("<hr>")
        self.PopUp.addWidget(line)
        self.PopUp.addStretch()

        self.PopUp.addWidget(self.create_label("File loader"))
        self.loadFileBtn = self.CreateButton("LOAD FILE", "#aa3629")
        self.PopUp.addWidget(self.loadFileBtn)
        self.loadFileBtn.clicked.connect(self.OpenFile)


        self.PopUp.addStretch()
        



        self.setLayout(self.PopUp)


    def SetSaveLocation(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, 
            "Create New Flight Log", 
            "", 
            "CSV Files (*.csv)"
        )
        
        if filePath:
            # Ensure it ends in .csv if the user didn't type it
            if not filePath.lower().endswith('.csv'):
                filePath += '.csv'
            
            self.FilePath = filePath
    def SelectPorts(self):

        self.ComPorts.clear()
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            self.ComPorts.addItem(port.portName())

    def ConnectBoard(self):
        DevicePort = self.ComPorts.currentText()
        DeviceBaud = int(self.BaudRates.currentText())

        if self.FilePath is None:
                msg = QMessageBox(self)
                msg.setWindowTitle("Data Import")
                msg.setText(f"File name not valid")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.show() # Use show() instead of exec() if you don't want to block the code
        else:
            self.connection_submitted.emit(DevicePort,DeviceBaud, self.FilePath)
            self.close()

    def OpenFile(self):
        filePath, _= QFileDialog.getOpenFileName(self, "Select Flight Log", "", "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)")
        if filePath:
                self.file_loaded.emit(filePath)
                self.close()

    def CreateButton(self, text, color):
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
    
    def create_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #666; font-weight: bold; font-size: 10px; margin-top: 10px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl