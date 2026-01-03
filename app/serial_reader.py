import serial
import serial.tools.list_ports
import time
from .database import save_weight
from .telegram_alerts import telegram_bot

class CoinTracker:
    def __init__(self):
        self.ser = None
        self.current_weight = 0.0
        self.connected = False
        self.port = None
        self.last_stable_weight = 0.0
        
    def find_arduino_port(self):
        """Try to find Arduino port automatically"""
        ports = list(serial.tools.list_ports.comports())
        
        print("Searching for Arduino...")
        if not ports:
            print("No serial ports found!")
            return None
            
        for port in ports:
            print(f"Found: {port.device} - {port.description}")
            if 'Arduino' in port.description:
                print(f"✓ Found Arduino on {port.device}")
                return port.device
        
        return '/dev/ttyACM1'  # Default to your Arduino port
    
    def connect(self):
        """Connect to Arduino"""
        try:
            self.port = self.find_arduino_port()
            
            print(f"Connecting to {self.port} at 115200 baud...")
            self.ser = serial.Serial(
                port=self.port,
                baudrate=115200,
                timeout=2
            )
            time.sleep(3)
            self.ser.flushInput()
            
            self.connected = True
            print(f"✓ Connected to Arduino on {self.port}")
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def read_weight(self):
        """Read weight from Arduino and check for DECREASES only"""
        if not self.connected or not self.ser or not self.ser.is_open:
            return None
        
        try:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    return None
                
                # Try to extract weight
                weight = None
                
                # Method 1: Look for number with "g"
                if 'g' in line:
                    parts = line.split('g')[0].strip()
                    try:
                        weight = float(parts)
                    except:
                        pass
                
                # Method 2: Look for any floating point number
                if weight is None:
                    import re
                    numbers = re.findall(r'[-+]?\d*\.\d+|\d+', line)
                    if numbers:
                        try:
                            weight = float(numbers[0])
                        except:
                            pass
                
                if weight is not None:
                    weight = round(weight, 3)
                    old_weight = self.current_weight
                    
                    # Only update if weight changed significantly
                    if abs(weight - old_weight) > 0.001:
                        self.current_weight = weight
                        save_weight(weight)
                        
                        # Check for DECREASE (not increase)
                        if weight < old_weight:
                            print(f"🔻 Weight DECREASE: {old_weight:.3f}g -> {weight:.3f}g")
                            # Send to Telegram for anomaly detection
                            telegram_bot.update_weight(weight, old_weight)
                        elif weight > old_weight:
                            print(f"🔺 Weight increase: {old_weight:.3f}g -> {weight:.3f}g")
                        
                        return weight
                        
        except Exception as e:
            print(f"Serial read error: {e}")
            
        return None
    
    def calculate_rs2_coins(self):
        """Calculate ONLY Rs.2 coins from weight"""
        weight = self.current_weight
        
        # Rs.2 coin weight: 8mg = 0.008g
        RS2_WEIGHT = 0.008
        
        if weight <= 0.001:
            return {
                'rs2_count': 0,
                'rs2_value': 0,
                'weight_used': 0.0,
                'remaining_weight': 0.0,
                'total_weight': 0.0
            }
        
        rs2_count = int(weight / RS2_WEIGHT)
        weight_used = rs2_count * RS2_WEIGHT
        rs2_value = rs2_count * 2
        remaining_weight = weight - weight_used
        
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