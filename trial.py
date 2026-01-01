import serial
import time

# Change this to the correct port for your system
# On Windows it might be 'COM3', 'COM4', etc.
# On macOS/Linux it will be something like '/dev/ttyUSB0', '/dev/ttyACM0', etc.
port = "/dev/ttyUSB0"  # Update this with your Arduino's port
baudrate = 115200      # Match the baud rate in your Arduino sketch

# Set up the serial connection
ser = serial.Serial(port, baudrate)

# Give some time for the connection to establish
time.sleep(2)

print("Reading weight data...")

while True:
    if ser.in_waiting > 0:
        data = ser.readline().decode('utf-8').strip()  # Read and decode the serial data
        print(data)
