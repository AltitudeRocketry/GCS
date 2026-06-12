from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pyqtgraph as pg
import pandas as pd
from PyQt6.QtGui import QColor

class RocketDataAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # 1. Digital Display Area (Top Bar)
        self.stats_layout = QHBoxLayout()
        self.state_display = self.create_stat_widget("State", "0")
        self.alt_display = self.create_stat_widget("ALTITUDE", "0.0 m")
        self.vel_display = self.create_stat_widget("VELOCITY", "0.0 m/s")
        self.accel_display = self.create_stat_widget("ACCELERATION", "0.0 m/s^2")

        self.layout.addLayout(self.stats_layout)


        self.setupPlot()
        # 2. Matplotlib Figure
        # self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='#121212')
        # self.canvas = FigureCanvas(self.fig)
        # self.ax = self.fig.add_subplot(111)
        # self.ax.set_facecolor('#1e1e1e')
        # self.ax.tick_params(colors='white')
        # self.ax.grid(True, color='#333333')
        
        # self.line, = self.ax.plot([], [], color='#00d4ff', linewidth=2)
        # self.layout.addWidget(self.canvas)

        self.requestedSensors = []
        self.views = []
        self.axis = []

    def setupPlot(self):
        self.graph = pg.PlotWidget()
        self.layout.addWidget(self.graph)

        self.graph.setBackground("k")
        self.graph.showGrid(x=True, y=True, alpha=0.3)

        # 3. Create the Crosshair lines
        # self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('w', width=1))
        # self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('w', width=1))
        # self.graph.addItem(self.vLine, ignoreBounds=True)
        # self.graph.addItem(self.hLine, ignoreBounds=True)

        # 4. Text item for displaying the 19-variable data context
        # self.cursorLabel = pg.TextItem(anchor=(0, 1), color='y')
        # self.graph.addItem(self.cursorLabel)

        # 5. Data storage for plotting (using lists or numpy arrays)
        self.timeData = []
        self.sensorData = [] # Example for one of the 19 vars
        # self.curve = self.graph.plot(pen='c', name="Acceleration")

        # 6. Set up the Mouse Move Proxy
        # SignalProxy allows high-frequency mouse tracking without freezing the UI
        self.proxy = pg.SignalProxy(self.graph.scene().sigMouseMoved, 
                                    rateLimit=60, slot=self.mouseMoved)
    def mouseMoved(self, evt):
            pos = evt[0]  # Get coordinates from signal proxy
            if self.graph.sceneBoundingRect().contains(pos):
                mousePoint = self.graph.getPlotItem().vb.mapSceneToView(pos)
                
                # Update Crosshair Position
                # self.vLine.setPos(mousePoint.x())
                # self.hLine.setPos(mousePoint.y())
                
                # Update Label (Displaying multiple variables)
                # Here you can logic-check the closest data point in your 19-variable list
                text = (f"<div style='background-color: rgba(0,0,0,150); padding: 5px; border: 1px solid yellow;'>"
                        f"<span style='color: yellow;'>T: {mousePoint.x():.3f} s</span><br>"
                        f"<span style='color: white;'>Val: {mousePoint.y():.3f}</span>"
                        f"</div>")
                
                # self.cursorLabel.setHtml(text)
                # self.cursorLabel.setPos(mousePoint.x(), mousePoint.y())
    def create_stat_widget(self, title, value):
        container = QWidget()
        lay = QVBoxLayout(container)
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #aaaaaa; font-weight: bold; font-size: 10px;")
        v_label = QLabel(value)
        v_label.setStyleSheet("color: white; font-size: 14px; font-family: 'Consolas';")
        lay.addWidget(t_label)
        lay.addWidget(v_label)
        self.stats_layout.addWidget(container)
        lay.addStretch()
        return v_label

    def loadSensors(self, path):
        # 1. Load the whole CSV
        df = pd.read_csv(path)
        
        # # 2. Extract time (Assuming your first column is named 'Time')
        # time_data = df['Time'] 
        # print(time_data)
        
        # # 3. Filter only the columns the user checked
        # # Pandas handles the "Index Matching" internally by column name
        # filtered_data = df[self.requestedSensors]
        # self.ax.clear()
        # self.ax.clear()
        # for sensor in self.requestedSensors:
        #     self.ax.plot(time_data, filtered_data[sensor], label=sensor)
    
        # self.ax.legend()
        # 2. Process the Packed 'Parachutes' Column
    # Convert hex to int, then extract bits into separate columns
        if 'Parachutes' in df.columns:
            # Fill NaN with 0 and convert to string to ensure int(x, 16) works
            df['p_int'] = df['Parachutes'].fillna('0').apply(lambda x: int(str(x), 16))
            
            # Create columns that match your CheckBox text exactly
            df['Drogue Cont']   = (df['p_int'] & 0x08).astype(bool)
            df['Drogue Deploy'] = (df['p_int'] & 0x04).astype(bool)
            df['Main Cont']     = (df['p_int'] & 0x02).astype(bool)
            df['Main Deploy']   = (df['p_int'] & 0x01).astype(bool)

        # 3. Prepare the Plot
            # self.ax.clear()
            # self.ax.set_title("Flight Data Analysis")
            # self.ax.set_xlabel("Time (s)")
            # self.ax.grid(True, linestyle='--', alpha=0.6, color='#444444')
            self.graph.clear()
            for v in self.views:
                self.graph.scene().removeItem(v)
                self.views = []
            for ax in self.axis:
                self.graph.scene().removeItem(ax)
                self.axis = []
            colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w'] # Cycle through colors
            # 4. The Unified Plotting Loop
            # This handles both regular values and our new 'virtual' boolean columns
            time_data = df['Time'] if 'Time' in df.columns else df.index


            for i, sensor in enumerate(self.requestedSensors):
                
                if sensor not in df.columns:
                    continue
            
                
                y_data = df[sensor]
                color = colors[i % len(colors)]

                if y_data.dtype == bool or sensor in ['Drogue Cont', 'Drogue Deploy', 'Main Cont', 'Main Deploy']:
                        # Convert to float and potentially scale for visibility
                        # Example: scale to 10 so it's visible against small values
                        y_data = y_data.astype(float) 
                        # self.ax.step(time_data, plot_y, label=f"{sensor} (Flag)", where='post')
                        # self.graph.plot(time_data, plot_y, pen=pg.mkPen(color, width=2), name=f"{sensor}")
                    # Logic for Regular Sensors (Floats)

                p1 = self.graph.getPlotItem()
                if i == 0:
                    self.graph.plot(time_data, y_data, 
                                                pen=pg.mkPen(color, width=1.5), 
                                                name=sensor)
                    p1.getAxis("left").setLabel('axis 1 in ViewBox of PlotItem', color='#FFFFFF')
                    p1.vb.enableAutoRange(pg.ViewBox.XYAxes, False)
                else:
                    v2 = pg.ViewBox()
                    p1.scene().addItem(v2)

                
                    axis = pg.AxisItem("right")
                    p1.layout.addItem(axis, 2, i + 1)

                    # v2.disableAutoRange()
                    axis.linkToView(v2)
                    v2.setXLink(p1)
                    v2.enableAutoRange(pg.ViewBox.XAxis, False)
                    v2.enableAutoRange(v2.XAxis, False)
                    v2.enableAutoRange(v2.YAxis, True)
                    

                    axis.setLabel(str(sensor), color='#2E2EFE')


                    # curve = pg.PlotCurveItem(time_data, y_data, pen=pg.mkPen(color, width=1.5))
                    curve = self.graph.plot(time_data, y_data, 
                                                pen=pg.mkPen(color, width=1.5), 
                                                name=sensor)
                    v2.addItem(curve)
                    self.views.append(v2)  
                    self.axis.append(axis)
                    # Update view on resize
                    def updateViews():
                        v2.setGeometry(p1.vb.sceneBoundingRect())
                    p1.vb.sigResized.connect(updateViews)
                    updateViews()
                    # Add to Legend manually for secondary views
                    # self.legend.addItem(curve, sensor)
                                      # Logic for Booleans (0 or 1)
                    # if y_data.dtype == bool or sensor in ['Drogue Cont', 'Drogue Deploy', 'Main Cont', 'Main Deploy']:
                    #     # Convert to float and potentially scale for visibility
                    #     # Example: scale to 10 so it's visible against small values
                    #     y_data = y_data.astype(float) 
                    #     # self.ax.step(time_data, plot_y, label=f"{sensor} (Flag)", where='post')
                    #     self.graph.plot(time_data, plot_y, pen=pg.mkPen(color, width=2), name=f"{sensor}")
                    # # Logic for Regular Sensors (Floats)
                    # else:
                    #     # self.ax.plot(time_data, y_data, label=sensor, linewidth=1.5)
                    #     self.graph.plot(time_data, y_data, 
                    #                         pen=pg.mkPen(color, width=1.5), 
                    #                         name=sensor)
                # self.graph.autoRange()
                

    def updateGraphVariables(self, requestedSensors, path):
        self.requestedSensors = requestedSensors
        self.loadSensors(path)
        # self.graph.autoRange()



