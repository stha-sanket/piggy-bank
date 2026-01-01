import serial
import time

# Configure the serial port
# Replace 'COM3' with your Arduino's port
# On Windows: COM3, COM4, etc.
# On Linux/Mac: /dev/ttyUSB0, /dev/ttyACM0, etc.
port = 'COM3'  # Change this to your Arduino port
baudrate = 115200  # Must match Arduino's Serial.begin() rate

try:
    # Open serial port
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
    
    print(f"Connected to {port} at {baudrate} baud")
    print("Reading load cell data...\n")
    
    while True:
        if ser.in_waiting > 0:
            # Read a line from serial
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            
except serial.SerialException as e:
    print(f"Serial error: {e}")
    print("\nCommon troubleshooting:")
    print("1. Check if Arduino is connected")
    print("2. Check port name (COM port)")
    print("3. Make sure no other program is using the port (like Arduino IDE)")
except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed")