import serial
import serial.tools.list_ports
import time
from database import save_weight

class CoinTracker:
    def __init__(self):
        self.ser = None
        self.current_weight = 15.456  # Start with simulated weight
        self.connected = False
        self.port = None
        
    def find_arduino_port(self):
        """Try to find Arduino port automatically"""
        ports = list(serial.tools.list_ports.comports())
        
        print("Searching for Arduino...")
        if not ports:
            print("No serial ports found!")
            return None
            
        for port in ports:
            print(f"Found: {port.device} - {port.description}")
            
            # Try common ports
            if 'USB' in port.description or 'ACM' in port.device:
                return port.device
        
        # Return first port if none matched
        return ports[0].device if ports else None
    
    def connect(self):
        """Connect to Arduino"""
        try:
            self.port = self.find_arduino_port()
            
            if not self.port:
                print("No Arduino found. Using simulated data.")
                return False
            
            print(f"Connecting to {self.port} at 115200 baud...")
            self.ser = serial.Serial(
                port=self.port,
                baudrate=115200,
                timeout=1
            )
            time.sleep(2)
            self.ser.flushInput()
            
            self.connected = True
            print(f"✓ Connected to Arduino on {self.port}")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            print("Using simulated data...")
            return False
    
    def read_weight(self):
        """Read weight from Arduino"""
        if not self.connected or not self.ser or not self.ser.is_open:
            # Return simulated data
            self.current_weight = 15.456  # Simulated weight
            return self.current_weight
            
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                # Debug
                print(f"Raw from Arduino: {line}")
                
                if line:
                    # Remove 'g' if present
                    if 'g' in line:
                        line = line.replace('g', '').strip()
                    
                    try:
                        weight = float(line)
                        weight = round(weight, 3)
                        
                        self.current_weight = weight
                        save_weight(weight)
                        
                        print(f"✓ Weight: {weight} g")
                        return weight
                    except ValueError:
                        print(f"Could not parse weight: {line}")
                        
        except Exception as e:
            print(f"Serial error: {e}")
            
        return self.current_weight
    
    def calculate_rs2_coins(self):
        """Calculate ONLY Rs.2 coins from weight"""
        weight = self.current_weight
        
        # Rs.2 coin weight: 8mg = 0.008g
        RS2_WEIGHT = 0.008
        
        print(f"Calculating Rs.2 coins for weight: {weight}g")
        
        # Handle zero or negative weight
        if weight <= 0.001:
            print("Weight too small, returning zero coins")
            return {
                'rs2_count': 0,
                'rs2_value': 0,
                'weight_used': 0.0,
                'remaining_weight': weight,
                'total_weight': weight
            }
        
        # Simple calculation: weight / coin_weight
        rs2_count = int(weight / RS2_WEIGHT)
        weight_used = rs2_count * RS2_WEIGHT
        rs2_value = rs2_count * 2
        remaining_weight = weight - weight_used
        
        print(f"Rs.2 Coins: {rs2_count}, Value: ₹{rs2_value}")
        
        return {
            'rs2_count': rs2_count,
            'rs2_value': rs2_value,
            'weight_used': round(weight_used, 3),
            'remaining_weight': round(remaining_weight, 3),
            'total_weight': round(weight, 3)
        }
    
    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

# Global instance
coin_tracker = CoinTracker()