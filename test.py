import serial
import time

try:
    print("Testing connection...")
    test_ser = serial.Serial('COM4', 9600, timeout=1) # Change to your port
    print("Port Opened Successfully!")
    test_ser.close()
except Exception as e:
    print(f"Error: {e}")