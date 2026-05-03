import serial
import csv
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot


class SerialReader(QObject):
    
# Signals to talk back to the UI
    finished = pyqtSignal()
    error = pyqtSignal(str)
    data_received = pyqtSignal(str) # Sends raw line to UI if needed

    def __init__(self, port, baud, path):
        super().__init__()
        self.port = str(port)
        self.baud = baud
        self.FilePath = path
        self.is_running = True

    @pyqtSlot()
    def StartDataDump(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            print("serial open")
            # 1. Send the command to start the dump immediately
            self.ser.write(b"START_DUMP\n")
            
            
            # 2. Open CSV for writing
            with open(self.FilePath, "w", newline='') as f:
                writer = csv.writer(f)
                
                while self.is_running:
                    if self.ser.in_waiting:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            # If board sends an "END_DUMP" flag, stop
                            if "END_DUMP" in line:
                                break
                            # Split CSV line and save to file
                            data = line.split(',')
                            writer.writerow(data)
                            
                            # Update UI (Optional: so you see it live)
                            self.data_received.emit(line)
                            
                                
            self.ser.close()
            self.finished.emit()
            
        except Exception as e:
            print(e)
            self.error.emit(str(e))

    def stop(self):
        self.is_running = False
