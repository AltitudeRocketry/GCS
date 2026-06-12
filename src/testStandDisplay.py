import sys
import serial.tools.list_ports
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox, QGridLayout
from PyQt6.QtCore import pyqtSlot, Qt, QThread
from RocketDataAnalyzer import RocketDataAnalyzer
from SerialReader import SerialReader
from BoardConnector import ConnectionWindow
import pandas as pd
import pyqtgraph as pg
from WebSocket import WebSocketClientThread

class TestStand(QWidget):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        self.time = []
        self.thrust = []
        self.pressure = []

        self.initScreen()
        self.wsThread = None




    def initScreen(self):
        mainLayout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("STATIC TEST STAND DECK")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00FF66; letter-spacing: 1px;")

        self.lbl_ws_status = QLabel("STATUS: OFFLINE")
        self.lbl_ws_status.setStyleSheet("font-weight: bold; color: #FF3333; padding-right: 10px;")
        
        btn_back = QPushButton("MAIN MENU")
        if self.controller:
            btn_back.clicked.connect(lambda: self.controller.show_main_menu())
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.lbl_ws_status)
        header.addWidget(btn_back)
        mainLayout.addLayout(header)

        grid = QGridLayout()

        grid.setContentsMargins(10, 15, 10, 15)
        
        self.lbl_sd = self.create_readout("SD CARD", "---")
        self.lbl_cont = self.create_readout("LAUNCH CONTINUITY", "---")
        self.lbl_thrust = self.create_readout("LIVE THRUST", "0.000 KG")
        self.lbl_impulse = self.create_readout("TOTAL IMPULSE", "0.000 N·s")

        grid.addWidget(self.lbl_sd, 0, 0)
        grid.addWidget(self.lbl_cont, 0, 1)
        grid.addWidget(self.lbl_thrust, 0, 2)
        grid.addWidget(self.lbl_impulse, 0, 3)
        mainLayout.addLayout(grid)

        # 3. HIGH-SPEED PYQTGRAPH COMPONENT
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#181818')
        self.graph_widget.showGrid(x=True, y=True, alpha=0.15)
        
        # Labels and Styling
        self.graph_widget.setLabel('bottom', 'Time', units='s', color='#999999')
        self.graph_widget.setLabel('left', 'Thrust', units='kg', color='#999999')
        
        # Apply the fix from your earlier debugging session: Lock X axis auto-scaling
        self.graph_widget.getPlotItem().vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        
        # High-visibility neon green line mirroring your web UI scheme
        self.curve = self.graph_widget.plot(
            pen=pg.mkPen(color='#00FF66', width=2),
            symbol='o', symbolSize=4, symbolBrush='#006622'
        )
        mainLayout.addWidget(self.graph_widget)

        # 4. CONTROL ACTION BUTTONS (Bottom Layout)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_connect = QPushButton("LINK TELEMETRY")
        btn_connect.clicked.connect(self.connect_websocket)
        btn_connect.setStyleSheet("background-color: #1A2F4C; color: #81B2FA; border-color: #2A4F7C;")
        
        btn_set = QPushButton("SET")
        btn_calibrate = QPushButton("CALIBRATE")
        btn_test = QPushButton("TEST")
        
        # Safety Critical Commands get distinct coloring
        btn_ignite = QPushButton("IGNITE")
        btn_ignite.setStyleSheet("background-color: #2E1616; color: #FF4D4D; border-color: #5C2323;")
        
        btn_stop = QPushButton("STOP")
        btn_stop.setStyleSheet("background-color: #4A1515; color: #FF3333; border-color: #801818;")

        # Hook commands up to transmit back to the ESP32 via websocket
        btn_set.clicked.connect(lambda: self.send_command("CMD_SET"))
        btn_calibrate.clicked.connect(lambda: self.send_command("CMD_CALIBRATE"))
        btn_test.clicked.connect(lambda: self.send_command("CMD_TEST"))
        btn_ignite.clicked.connect(lambda: self.send_command("CMD_IGNITE"))
        btn_stop.clicked.connect(lambda: self.send_command("CMD_STOP"))

        actions_layout.addWidget(btn_connect)
        actions_layout.addWidget(btn_set)
        actions_layout.addWidget(btn_calibrate)
        actions_layout.addWidget(btn_test)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_ignite)
        actions_layout.addWidget(btn_stop)
        mainLayout.addLayout(actions_layout)

    def create_readout(self, label_text, default_value):
        """Helper to create modular dashboard digital displays"""
        container = QWidget()
        v_box = QVBoxLayout(container)
        v_box.setContentsMargins(5, 5, 5, 5)
        v_box.setSpacing(2)
        
        title = QLabel(label_text)
        title.setStyleSheet("color: #757575; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        
        value = QLabel(default_value)
        value.setStyleSheet("color: #FFFFFF; font-size: 20px; font-weight: bold; font-family: monospace;")
        
        v_box.addWidget(title)
        v_box.addWidget(value)
        container.setStyleSheet("background-color: #1E1E1E; border-radius: 4px; border: 1px solid #2D2D2D;")
        # Expose the inner display element so it can be updated by signals dynamically
        container.display_label = value 
        return container

    def connect_websocket(self):
        if self.wsThread and self.wsThread.isRunning():
            self.wsThread.stop()
        
        # SoftAP ESP32 Default Target Address
        self.wsThread = WebSocketClientThread("ws://192.168.4.1/ws")
        self.wsThread.status_signal.connect(self.update_status_bar)
        self.wsThread.data_signal.connect(self.handle_incoming_telemetry)
        self.wsThread.start()

    def update_status_bar(self, status_text):
        self.lbl_ws_status.setText(f"STATUS: {status_text}")
        if "CONNECTED" in status_text:
            self.lbl_ws_status.setStyleSheet("font-weight: bold; color: #00FF66;")
        else:
            self.lbl_ws_status.setStyleSheet("font-weight: bold; color: #FF3333;")

    def send_command(self, cmd):
        if self.wsThread and self.wsThread.isRunning():
            self.wsThread.send_command(cmd)

    def handle_incoming_telemetry(self, data):
        # Expecting structural JSON over WS from ESP32: 
        # {"time": 12.34, "thrust": 0.008, "sd": 1, "cont": 0, "impulse": 0.005}
        
        # Update Readouts
        if 'sd' in data: self.lbl_sd.display_label.setText(str(data['sd']))
        if 'cont' in data: self.lbl_cont.display_label.setText(str(data['cont']))
        if 'thrust' in data: self.lbl_thrust.display_label.setText(f"{data['thrust']:.4f} KG")
        if 'impulse' in data: self.lbl_impulse.display_label.setText(f"{data['impulse']:.4f} N·s")
        
        # Manage graph tracking arrays
        if 'time' in data and 'thrust' in data:
            self.time_history.append(data['time'])
            self.thrust_history.append(data['thrust'])
            
            # Limit trailing points to avoid rendering bog downs (keep last 300 values)
            if len(self.time_history) > 300:
                self.time_history.pop(0)
                self.thrust_history.pop(0)
            
            self.curve.setData(self.time_history, self.thrust_history)
            
            # Manually pan viewport to stick with running timeline window frame smoothly
            if self.time_history:
                self.graph_widget.getPlotItem().vb.setXRange(self.time_history[0], self.time_history[-1], padding=0)



        

