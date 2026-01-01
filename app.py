from flask import Flask, jsonify
import serial
import threading
import time
from datetime import datetime
import glob

app = Flask(__name__)

# Configuration
def find_arduino_port():
    """Find Arduino port automatically"""
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            return port
        except:
            pass
    return None

ARDUINO_PORT = find_arduino_port() or '/dev/ttyUSB0'
BAUD_RATE = 115200

# Global variables
current_data = {
    'weight': 0.0,
    'max_2rs': 0,
    'max_1rs': 0,
    'total_2rs': 0,
    'total_1rs': 0,
    'last_update': None,
    'connected': False
}

COIN_2RS_WEIGHT = 0.008
COIN_1RS_WEIGHT = 0.006

ser = None
serial_thread = None
running = False

def calculate_coins(weight):
    """Calculate coin counts based on weight"""
    if weight <= 0.001:
        return 0, 0, 0, 0
    
    max_2rs = int(weight / COIN_2RS_WEIGHT)
    max_1rs = int(weight / COIN_1RS_WEIGHT)
    total_2rs = max(0, int(round(weight / COIN_2RS_WEIGHT)))
    total_1rs = max(0, int(round(weight / COIN_1RS_WEIGHT)))
    
    return max_2rs, max_1rs, total_2rs, total_1rs

def parse_arduino_output(line):
    """Parse Arduino serial output"""
    try:
        if "Weight:" in line:
            parts = line.split("|")
            
            if len(parts) >= 1:
                # Extract weight (first part before "g")
                weight_part = parts[0].replace("Weight:", "").split("g")[0].strip()
                weight = float(weight_part)
                
                # Calculate coins
                max_2rs, max_1rs, total_2rs, total_1rs = calculate_coins(weight)
                
                # Update data
                current_data.update({
                    'weight': weight,
                    'max_2rs': max_2rs,
                    'max_1rs': max_1rs,
                    'total_2rs': total_2rs,
                    'total_1rs': total_1rs,
                    'last_update': datetime.now().strftime("%H:%M:%S"),
                    'connected': True
                })
                
    except Exception as e:
        print(f"Parse error: {e}")

def serial_read_thread():
    """Read from serial port"""
    global ser, running
    
    while running:
        try:
            if ser and ser.is_open and ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Arduino: {line}")
                    parse_arduino_output(line)
        except Exception as e:
            print(f"Serial error: {e}")
            current_data['connected'] = False
            time.sleep(2)
        
        time.sleep(0.1)

def start_serial_connection():
    """Start serial connection"""
    global ser, serial_thread, running
    
    try:
        ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)
        ser.reset_input_buffer()
        
        running = True
        serial_thread = threading.Thread(target=serial_read_thread)
        serial_thread.daemon = True
        serial_thread.start()
        
        print(f"Connected to Arduino on {ARDUINO_PORT}")
        current_data['connected'] = True
        return True
        
    except Exception as e:
        print(f"Failed to connect to {ARDUINO_PORT}: {e}")
        current_data['connected'] = False
        return False

@app.route('/')
def index():
    """Main page - inline HTML"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Piggy Bank Coin Counter</title>
    </head>
    <body>
        <h1>Piggy Bank Coin Counter</h1>
        
        <h2>Current Weight: <span id="weight">0.000</span> grams</h2>
        
        <h3>2 Rupees Coin (0.008g each):</h3>
        <p>Maximum Possible Coins: <span id="max-2rs">0</span></p>
        <p>Total Coins (Rounded): <span id="total-2rs">0</span></p>
        
        <h3>1 Rupee Coin (0.006g each):</h3>
        <p>Maximum Possible Coins: <span id="max-1rs">0</span></p>
        <p>Total Coins (Rounded): <span id="total-1rs">0</span></p>
        
        <p>Last Update: <span id="last-update">--:--:--</span></p>
        <p>Status: <span id="status">Disconnected</span></p>
        
        <script>
            function updateData() {
                fetch('/api/data')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('weight').textContent = data.weight.toFixed(3);
                        document.getElementById('max-2rs').textContent = data.max_2rs;
                        document.getElementById('total-2rs').textContent = data.total_2rs;
                        document.getElementById('max-1rs').textContent = data.max_1rs;
                        document.getElementById('total-1rs').textContent = data.total_1rs;
                        document.getElementById('last-update').textContent = data.last_update;
                        document.getElementById('status').textContent = data.connected ? 'Connected to Arduino' : 'Disconnected';
                    });
            }
            
            // Update every second
            setInterval(updateData, 1000);
            updateData();
        </script>
    </body>
    </html>
    '''

@app.route('/api/data')
def get_data():
    """API endpoint for data"""
    return jsonify(current_data)

if __name__ == '__main__':
    print("=== Piggy Bank Coin Counter ===")
    print(f"Looking for Arduino on: {ARDUINO_PORT}")
    
    if start_serial_connection():
        print("✓ Connected to Arduino")
    else:
        print("✗ Arduino not found")
        print("Available ports:", glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'))
    
    print(f"\nOpen: http://localhost:5000")
    print("================================\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)