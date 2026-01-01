import serial
import time

port = '/dev/ttyACM0'  # This is your Arduino port
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    time.sleep(2)  # Wait for Arduino to reset
    
    print(f"Connected to {port} at {baudrate} baud")
    print("Reading load cell data...\n")
    
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            
except serial.SerialException as e:
    print(f"Serial error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Arduino IDE Serial Monitor is CLOSED")
    print("2. Check if Arduino is properly connected")
    print("3. You might need permission: sudo chmod a+rw /dev/ttyACM0")
    print("   OR add yourself to dialout group: sudo usermod -a -G dialout $USER")
except KeyboardInterrupt:
    print("\nProgram terminated by user")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("Serial port closed")