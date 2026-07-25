# --- BACKGROUND WEBSOCKET THREAD ---
import json
import socket
import asyncio
import websockets
import struct
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
        self.send_queue = None

    def run(self):
        """Executed automatically when self.start() is called in PyQt"""
        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.send_queue = asyncio.Queue()
        self.loop.run_until_complete(self.main_loop())

    async def main_loop(self):
        self.status_signal.emit("CONNECTING...")
        try:
            async with websockets.connect(self.uri, ping_interval=None, close_timeout=1) as ws:
                self.websocket = ws
                self.status_signal.emit("CONNECTED")
                sock = ws.transport.get_extra_info('socket')
                if sock:
                    # Disable Nagle's Algorithm & Delayed ACKs
                    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    # Set receive buffer size
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
                
                # Run reader and writer concurrently
                await asyncio.gather(
                    self.receive_handler(ws),
                    self.send_handler(ws)
                )
        except Exception as e:
            self.status_signal.emit(f"OFFLINE: {str(e)}")
        finally:
            self.running = False

    async def receive_handler(self, ws):
        while self.running:
            try:
                msg = await ws.recv()
                if isinstance(msg, bytes):
                    if len(msg) == 10:
                        thrust, currentTestTime, continuityPin, sdState = struct.unpack("<fIBB", msg)

                        data = {
                            "thrust": thrust,
                            "time": currentTestTime,
                            "cont": continuityPin,
                            "SD": sdState
                        }

                        self.data_signal.emit(data)

                elif isinstance(msg, str):
                    try:
                        data = json.loads(msg)
                        self.data_signal.emit(data)
                    except json.JSONDecodeError:
                        pass
                await asyncio.sleep(0)
            except websockets.ConnectionClosed:
                break

    async def send_handler(self, ws):
        while self.running:
            cmd = await self.send_queue.get()
            if cmd:
                try:
                    await ws.send(cmd)
                    print(f"WS Transmitted Outbound: {cmd}")
                except Exception as e:
                    print(f"WS Transmit Error: {e}")
            self.send_queue.task_done()

    def send_command(self, cmd_string):
        """Thread-safe call from PyQt GUI thread to queue outbound payloads"""
        if self.loop and self.running and self.send_queue:
            asyncio.run_coroutine_threadsafe(self.send_queue.put(cmd_string), self.loop)

    def stop(self):
        self.running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
        self.wait()