import sys
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication,QInputDialog, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
                              QFrame, QComboBox, QCheckBox, QDateTimeEdit, QSlider, QLabel, QMessageBox, QGridLayout, QButtonGroup)
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
        self.lbl_loadCell = self.create_readout("Load Cell", "---")
        self.lbl_cont = self.create_readout("LAUNCH CONTINUITY", "---")
        self.lbl_thrust = self.create_readout("LIVE THRUST", "0.000 KG")
        self.lbl_pressure = self.create_readout("LIVE PRESSURE", "0.0 PSI")

        grid.addWidget(self.lbl_sd, 0, 0)
        grid.addWidget(self.lbl_loadCell, 0, 1)
        grid.addWidget(self.lbl_cont, 0, 2)
        grid.addWidget(self.lbl_thrust, 0, 3)
        grid.addWidget(self.lbl_pressure, 0, 4)
        mainLayout.addLayout(grid)

        """
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
        """

        graph_layout = QHBoxLayout()

        self.btn_combined = QPushButton("COMBINED VIEW (DUAL AXIS)")
        self.btn_separated = QPushButton("SEPARATED PLOTS")
        self.btn_combined.setCheckable(True)
        self.btn_separated.setCheckable(True)
        self.btn_combined.setChecked(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.btn_combined)
        self.mode_group.addButton(self.btn_separated)

        self.btn_combined.clicked.connect(self.show_combined_view)
        self.btn_separated.clicked.connect(self.show_separated_view)

        graph_layout.addWidget(self.btn_combined)
        graph_layout.addWidget(self.btn_separated)
        graph_layout.addStretch()
        mainLayout.addLayout(graph_layout)

        pg.setConfigOptions(antialias=True)
        self.graph_layout = pg.GraphicsLayoutWidget()
        self.graph_layout.setBackground('#181818')
        mainLayout.addWidget(self.graph_layout)

        self.setup_graph_views()

        # 4. CONTROL ACTION BUTTONS (Bottom Layout)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_connect = QPushButton("LINK TELEMETRY")
        btn_connect.clicked.connect(self.connect_websocket)
        btn_connect.setStyleSheet("background-color: #1A2F4C; color: #81B2FA; border-color: #2A4F7C;")
        
        btn_set = QPushButton("SET")
        btn_calibrate = QPushButton("CALIBRATE")
        btn_test = QPushButton("TEST")
        btn_measure = QPushButton("MEASURE")
        
        # Safety Critical Commands get distinct coloring
        btn_ignite = QPushButton("IGNITE")
        btn_ignite.setStyleSheet("background-color: #2E1616; color: #FF4D4D; border-color: #5C2323;")
        
        btn_stop = QPushButton("STOP")
        btn_stop.setStyleSheet("background-color: #4A1515; color: #FF3333; border-color: #801818;")


        btn_set.clicked.connect(self.SetPromt)
        btn_calibrate.clicked.connect(self.CalibratePromt)
        btn_test.clicked.connect(self.TestPromt)
        # Hook commands up to transmit back to the ESP32 via websocket
        # btn_set.clicked.connect(lambda: self.send_command("CMD_SET"))
        # btn_calibrate.clicked.connect(lambda: self.send_command("CMD_CALIBRATE"))
        # btn_test.clicked.connect(lambda: self.send_command("CMD_TEST"))
        btn_measure.clicked.connect(lambda: self.send_command("CMD_MEASURE:"))
        btn_ignite.clicked.connect(lambda: self.send_command("CMD_GO:"))
        btn_stop.clicked.connect(lambda: self.send_command("CMD_STOP:"))

        actions_layout.addWidget(btn_connect)
        actions_layout.addWidget(btn_set)
        actions_layout.addWidget(btn_calibrate)
        actions_layout.addWidget(btn_test)
        actions_layout.addWidget(btn_measure)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_ignite)
        actions_layout.addWidget(btn_stop)
        mainLayout.addLayout(actions_layout)

    def setup_graph_views(self):
        """Builds both Combined (Dual-Axis) and Separated layout states."""
        
        # -------------------------------------------------------------
        # 1. COMBINED VIEW (Dual Y-Axis Overlay)
        # -------------------------------------------------------------
        self.p_combined = self.graph_layout.addPlot(row=0, col=0, title="Thrust & Pressure vs Time")
        self.p_combined.showGrid(x=True, y=True, alpha=0.15)
        self.p_combined.setLabel('bottom', 'Time', units='s', color='#999999')
        self.p_combined.setLabel('left', 'Thrust', units='kg', color='#00FF66')
        self.p_combined.vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)

        # Left Curve: Thrust (Neon Green)
        self.curve_thrust_comb = self.p_combined.plot(
            pen=pg.mkPen(color='#00FF66', width=2),
            symbol='o', symbolSize=4, symbolBrush='#006622'
        )

        # Secondary ViewBox overlay for Pressure on Right Axis
        self.vb_pressure = pg.ViewBox()
        self.p_combined.scene().addItem(self.vb_pressure)
        self.p_combined.getAxis('right').linkToView(self.vb_pressure)
        self.vb_pressure.setXLink(self.p_combined)
        self.p_combined.showAxis('right')
        self.p_combined.setLabel('right', 'Pressure', units='PSI', color='#00E5FF')

        # Right Curve: Pressure (Cyan)
        self.curve_press_comb = pg.PlotCurveItem(
            pen=pg.mkPen(color='#00E5FF', width=2),
            symbol='t', symbolSize=4, symbolBrush='#005577'
        )
        self.vb_pressure.addItem(self.curve_press_comb)

        # Sync geometry of overlay ViewBox on viewport resize
        self.p_combined.getViewBox().sigResized.connect(self.update_overlay_geometry)

        # -------------------------------------------------------------
        # 2. SEPARATED VIEW (Row 1: Thrust, Row 2: Pressure)
        # -------------------------------------------------------------
        self.p_thrust_sep = self.graph_layout.addPlot(row=1, col=0, title="Thrust Profile")
        self.p_thrust_sep.showGrid(x=True, y=True, alpha=0.15)
        self.p_thrust_sep.setLabel('left', 'Thrust', units='kg', color='#00FF66')
        self.p_thrust_sep.vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self.curve_thrust_sep = self.p_thrust_sep.plot(
            pen=pg.mkPen(color='#00FF66', width=2),
            symbol='o', symbolSize=4, symbolBrush='#006622'
        )

        self.p_press_sep = self.graph_layout.addPlot(row=2, col=0, title="Chamber Pressure Profile")
        self.p_press_sep.showGrid(x=True, y=True, alpha=0.15)
        self.p_press_sep.setLabel('bottom', 'Time', units='s', color='#999999')
        self.p_press_sep.setLabel('left', 'Pressure', units='PSI', color='#00E5FF')
        self.p_press_sep.vb.enableAutoRange(axis=pg.ViewBox.XAxis, enable=False)
        self.curve_press_sep = self.p_press_sep.plot(
            pen=pg.mkPen(color='#00E5FF', width=2),
            symbol='t', symbolSize=4, symbolBrush='#005577'
        )

        # Link X axes of separated graphs for synchronized scrolling/zooming
        self.p_press_sep.setXLink(self.p_thrust_sep)

        # Default View Mode
        self.show_combined_view()

    def update_overlay_geometry(self):
        """Keep overlay ViewBox aligned with main combined plot frame."""
        self.vb_pressure.setGeometry(self.p_combined.getViewBox().sceneBoundingRect())
        self.vb_pressure.linkedViewChanged(self.p_combined.getViewBox(), self.vb_pressure.XAxis)

    def show_combined_view(self):
        """Displays combined dual Y-axis plot and hides separated plots."""
        self.p_combined.setVisible(True)
        self.p_thrust_sep.setVisible(False)
        self.p_press_sep.setVisible(False)
        self.refresh_graph_data()

    def show_separated_view(self):
        """Displays stacked plots and hides combined plot."""
        self.p_combined.setVisible(False)
        self.p_thrust_sep.setVisible(True)
        self.p_press_sep.setVisible(True)
        self.refresh_graph_data()

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

    def SetPromt(self):
        """Asks the user for a tare/scale calibration factor float"""
        val, ok = QInputDialog.getDouble(
            self, 
            "Set Calibration Factor", 
            "Enter Scale Calibration Value:", 
            value=1000.0, 
            decimals=4
        )
        if ok:
            # Transmits formatted command matching ESP32 parser: CMD_SET:1234.56
            self.send_command(f"CMD_SET:{val}")

    def CalibratePromt(self):
        """Multi-step guided calibration flow using sequential dialog boxes."""
        
        # Step 1: Tare Prompt (Clear the scale)
        step1 = QMessageBox.question(
            self,
            "Calibration - Step 1: Tare",
            "Please remove all weight from the load cell.\n\nClick 'Yes' when the scale is empty to tare.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )

        if step1 != QMessageBox.StandardButton.Yes:
            print("Calibration Canceled")
            return

        self.send_command("CMD_CALIBRATE:START")

        weight, ok = QInputDialog.getDouble(
            self, 
            "Calibrate Load Cell", 
            "Enter Known Calibration Weight (g):", 
            value=1.000, 
            decimals=4
        )
        if not ok:
            print("Calibration Canceled")
            return
        
        # Step 3: Confirmation Box
        step3 = QMessageBox.information(
            self,
            "Calibration - Step 3: Calibrate",
            f"Load cell is loaded with {weight:.4f} g.\n\nClick 'OK' to calculate and save scale factor.",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )

        if step3 == QMessageBox.StandardButton.Ok:
            # Transmit the known weight value to ESP32: CMD_CALIBRATE:1.0000
            self.send_command(f"CMD_CALIBRATE:WEIGHT_{weight:.4f}")
            # QMessageBox.information(self, "Calibration Sent", f"Calibration payload ({weight:.4f} KG) sent to ESP32.")

    def TestPromt(self):
        """Asks the user for the target logging filename before test run"""
        filename, ok = QInputDialog.getText(
            self, 
            "Test Log Setup", 
            "Enter SD Storage Filename (e.g., test1):", 
            text="flight_log_1"
        )
        if ok and filename.strip():
            # Transmits formatted command matching ESP32 parser: CMD_TEST:flight_log_1.csv
            self.send_command(f"CMD_TEST:{filename.strip()}")


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
        """Sends payload string across WebSocket worker thread"""
        if self.wsThread and self.wsThread.isRunning():
            print(f"Transmitting Command: {cmd}")
            self.wsThread.send_command(cmd)
        else:
            QMessageBox.warning(self, "Telemetry Offline", "Cannot send command: WebSocket is not linked.")

    def handle_incoming_telemetry(self, data):
        # Expecting structural JSON over WS from ESP32: 
        # {"time": 12.34, "thrust": 0.008, "sd": 1, "cont": 0, "impulse": 0.005}
        print(data)

        if 'Calibration Value' in data: 
            QMessageBox.information(self, "Calibration Value", str(data["Calibration Value"]))
        # Update Readouts
        if 'SD' in data: self.lbl_sd.display_label.setText(str(data['SD']))
        if 'LoadCell' in data: self.lbl_loadCell.display_label.setText(str(data['LoadCell']))
        if 'cont' in data: self.lbl_cont.display_label.setText(str(data['cont']))
        if 'thrust' in data: self.lbl_thrust.display_label.setText(f"{data['thrust']:.4f} KG")
        if 'pressure' in data: self.lbl_pressure.display_label.setText(f"{data['pressure']:.4f} PSI")
        
        
        # Manage graph tracking arrays
        if 'time' in data:
            self.time.append(data['time'])

            if 'thrust' in data:
                self.thrust.append(data['thrust'])

            if 'pressure' in data:
                self.pressure.append(data['pressure'])
            # Limit trailing points to avoid rendering bog downs (keep last 300 values)
            if len(self.time) > 300:
                self.time.pop(0)
                self.thrust.pop(0)
                self.pressure.pop(0)


            self.refresh_graph_data()
            # self.curve.setData(self.time, self.thrust)
            
            # # Manually pan viewport to stick with running timeline window frame smoothly
            # if self.time:
            #     self.graph_widget.getPlotItem().vb.setXRange(self.time[0], self.time[-1], padding=0)


    def refresh_graph_data(self):
            """Pushes data arrays to current visible plot curves."""
            if not self.time:
                return

            if self.p_combined.isVisible():
                self.curve_thrust_comb.setData(self.time, self.thrust)
                self.curve_press_comb.setData(self.time, self.pressure)
                self.p_combined.vb.setXRange(self.time[0], self.time[-1], padding=0)
            else:
                self.curve_thrust_sep.setData(self.time, self.thrust)
                self.curve_press_sep.setData(self.time, self.pressure)
                self.p_thrust_sep.vb.setXRange(self.time[0], self.time[-1], padding=0)
        

