# --- BACKGROUND WEBSOCKET THREAD ---
import json
import asyncio
import websockets
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont

class WebSocketClientThread(QThread):
    data_signal = pyqtSignal(dict)
    status_signal = pyqtSignal(str)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.running = False
        self.websocket = None
        self.loop = None

    def run(self):
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen())

    async def listen(self):
        self.status_signal.emit("CONNECTING...")
        try:
            async with websockets.connect(self.uri) as ws:
                self.websocket = ws
                self.status_signal.emit("CONNECTED")
                while self.running:
                    msg = await ws.recv()
                    try:
                        data = json.loads(msg)
                        self.data_signal.emit(data)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            self.status_signal.emit(f"OFFLINE: {str(e)}")

    def send_command(self, cmd_string):
        """Allows outbound button clicks to send commands over the WebSocket"""
        if self.websocket and self.loop and not self.websocket.close:
            asyncio.run_coroutine_threadsafe(self.websocket.send(cmd_string), self.loop)

    def stop(self):
        self.running = False
        if self.loop:
            self.loop.stop()
        self.wait()