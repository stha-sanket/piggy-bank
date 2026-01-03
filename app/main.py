from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import threading
import time
from werkzeug.utils import secure_filename
from datetime import datetime
from .serial_reader import coin_tracker
from .database import get_db_connection
from .telegram_alerts import telegram_bot

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production!
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Background thread for reading serial data
def serial_reader_thread():
    """Background thread to continuously read from Arduino"""
    print("Starting serial reader thread...")
    if not coin_tracker.connect():
        print("Arduino not connected. Will try to read anyway...")
    print("Serial reader started - monitoring for weight drops...")
    while True:
        try:
            weight = coin_tracker.read_weight()
            if weight is not None and weight > 1.0:
                print(f"Current weight: {weight:.3f}g")
            time.sleep(0.5)
        except Exception as e:
            print(f"Error in serial thread: {e}")
            time.sleep(1)

# Start the serial reader thread
serial_thread = threading.Thread(target=serial_reader_thread, daemon=True)
serial_thread.start()

@app.route('/')
def index():
    weight = coin_tracker.current_weight
    coins_data = coin_tracker.calculate_rs2_coins()

    conn = get_db_connection()
    goals_result = conn.execute('SELECT * FROM goals ORDER BY created_at DESC').fetchall()
    conn.close()

    goals = []
    for row in goals_result:
        goal = dict(row)
        try:
            prize = float(goal['prize'])
        except:
            prize = 0.0

        current_rs2 = coins_data['rs2_count']
        current_value = coins_data['rs2_value']

        if prize > 0:
            progress = min(100, (current_value / prize) * 100)
            remaining_value = max(0, prize - current_value)
            rs2_needed = int(remaining_value / 2)
            if remaining_value % 2 > 0:
                rs2_needed += 1
        else:
            progress = 0
            rs2_needed = 0

        goal['progress'] = round(progress, 1)
        goal['rs2_needed'] = rs2_needed
        goal['current_rs2'] = current_rs2
        goal['current_value'] = current_value
        goals.append(goal)

    if 'remaining_weight' not in coins_data:
        coins_data['remaining_weight'] = 0.0

    return render_template('index.html',
                           weight=coins_data.get('total_weight', 0),
                           coins_data=coins_data,
                           goals=goals)

@app.route('/api/current_data')
def api_current_data():
    weight = coin_tracker.current_weight
    coins_data = coin_tracker.calculate_rs2_coins()

    conn = get_db_connection()
    goals_result = conn.execute('SELECT * FROM goals ORDER BY created_at DESC').fetchall()
    conn.close()

    goals = []
    for row in goals_result:
        goal = dict(row)
        try:
            prize = float(goal['prize'])
        except:
            prize = 0.0

        current_rs2 = coins_data['rs2_count']
        current_value = coins_data['rs2_value']

        if prize > 0:
            progress = min(100, (current_value / prize) * 100)
            remaining_value = max(0, prize - current_value)
            rs2_needed = int(remaining_value / 2)
            if remaining_value % 2 > 0:
                rs2_needed += 1
        else:
            progress = 0
            rs2_needed = 0

        goal['progress'] = round(progress, 1)
        goal['rs2_needed'] = rs2_needed
        goal['current_rs2'] = current_rs2
        goals.append(goal)

    if 'remaining_weight' not in coins_data:
        coins_data['remaining_weight'] = 0.0

    return jsonify({
        'success': True,
        'weight': coins_data.get('total_weight', 0),
        'coins_data': coins_data,
        'goals': goals
    })

@app.route('/goals', methods=['GET', 'POST'])
def manage_goals():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        prize = request.form.get('prize', '0').strip()
        image = request.files.get('image')

        if not name:
            flash('Goal name is required!', 'error')
            return redirect(url_for('manage_goals'))
        try:
            prize = float(prize)
            if prize <= 0:
                raise ValueError
        except:
            flash('Prize amount must be greater than 0!', 'error')
            return redirect(url_for('manage_goals'))

        image_path = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_path = f'uploads/{filename}'
            image.save(os.path.join('static', image_path))

        conn.execute('INSERT INTO goals (name, prize, image_path) VALUES (?, ?, ?)',
                     (name, prize, image_path))
        conn.commit()
        flash('Goal added successfully!', 'success')
        return redirect(url_for('manage_goals'))

    goals = conn.execute('SELECT * FROM goals ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('goals.html', goals=goals)

@app.route('/goal/delete/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    conn = get_db_connection()
    goal = conn.execute('SELECT image_path FROM goals WHERE id = ?', (goal_id,)).fetchone()
    if goal and goal['image_path']:
        image_path = os.path.join('static', goal['image_path'])
        if os.path.exists(image_path):
            os.remove(image_path)

    conn.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    flash('Goal deleted successfully!', 'success')
    return redirect(url_for('manage_goals'))

# ===== TELEGRAM ALERT TEST ROUTES =====
@app.route('/test/telegram/<message>')
def test_telegram_message(message):
    success = telegram_bot.send_message(f"Test message: {message}")
    return jsonify({'success': success, 'message': f'Telegram test sent: {message}'})

@app.route('/test/anomaly/<float:old_weight>/<float:new_weight>')
def test_anomaly(old_weight, new_weight):
    drop_grams = old_weight - new_weight
    alert_triggered = telegram_bot.update_weight(new_weight, old_weight)
    return jsonify({
        'success': True,
        'old_weight': old_weight,
        'new_weight': new_weight,
        'drop_grams': round(drop_grams, 3),
        'coins_removed_est': int(drop_grams / 0.008),
        'alert_triggered': alert_triggered,
        'alert_threshold_grams': 0.016,
        'alert_threshold_coins': 2
    })

@app.route('/force_alert')
def force_alert():
    message = (
        "🚨 <b>TEST ALERT - Piggy Bank Tracker</b> 🚨\n\n"
        "This is a test alert to verify Telegram integration.\n"
        "Your piggy bank monitoring system is working correctly!\n\n"
        f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "✅ System Status: Operational"
    )
    success = telegram_bot.send_message(message)
    return jsonify({
        'success': success,
        'message': 'Test alert sent successfully!' if success else 'Failed to send test alert'
    })

@app.route('/telegram/status')
def telegram_status():
    return jsonify({
        'chat_id': telegram_bot.chat_id,
        'has_token': bool(telegram_bot.bot_token),
        'last_alert_time': telegram_bot.last_alert_time,
        'time_since_last_alert': round(time.time() - telegram_bot.last_alert_time, 1) if telegram_bot.last_alert_time > 0 else 'Never',
        'alert_cooldown_seconds': telegram_bot.alert_cooldown,
        'alert_threshold_grams': 0.016,
        'alert_threshold_coins': 'More than 2 Rs.2 coins removed'
    })

@app.route('/simulate/weight/<float:weight>')
def simulate_weight(weight):
    old_weight = coin_tracker.current_weight
    coin_tracker.current_weight = weight
    if weight < old_weight:
        drop = old_weight - weight
        print(f"Simulated weight drop: {old_weight:.3f}g → {weight:.3f}g (-{drop:.3f}g)")
    return jsonify({
        'success': True,
        'old_weight': old_weight,
        'new_weight': weight,
        'coins': coin_tracker.calculate_rs2_coins()
    })

@app.route('/debug/weight')
def debug_weight():
    return jsonify({
        'current_weight': coin_tracker.current_weight,
        'connected': coin_tracker.connected,
        'port': coin_tracker.port,
        'coins_data': coin_tracker.calculate_rs2_coins()
    })

@app.route('/arduino/test')
def arduino_test():
    readings = []
    for i in range(5):
        weight = coin_tracker.read_weight()
        if weight is not None:
            readings.append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'weight': weight,
                'coins': coin_tracker.calculate_rs2_coins()
            })
        time.sleep(0.5)
    return jsonify({
        'connected': coin_tracker.connected,
        'port': coin_tracker.port,
        'readings': readings,
        'current_weight': coin_tracker.current_weight
    })

@app.route('/arduino/reconnect')
def arduino_reconnect():
    coin_tracker.close()
    time.sleep(1)
    connected = coin_tracker.connect()
    return jsonify({
        'success': connected,
        'port': coin_tracker.port,
        'message': 'Reconnected successfully' if connected else 'Failed to reconnect'
    })

@app.route('/system/info')
def system_info():
    import sys
    import platform
    return jsonify({
        'python_version': sys.version.split()[0],
        'platform': platform.platform(),
        'database': 'coin_tracker.db',
        'upload_folder': app.config['UPLOAD_FOLDER'],
        'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/help')
def help_page():
    base_url = request.host_url.rstrip('/')
    help_info = {
        'main_pages': [
            f'{base_url}/ - Main dashboard',
            f'{base_url}/goals - Manage savings goals',
        ],
        'telegram_tests': [
            f'{base_url}/force_alert - Send test Telegram alert',
            f'{base_url}/test/telegram/Hello - Send custom message',
            f'{base_url}/test/anomaly/100/99.9 - Test drop >0.016g',
            f'{base_url}/telegram/status - Check Telegram status',
        ],
        'testing_tools': [
            f'{base_url}/simulate/weight/50.0 - Manually set weight',
            f'{base_url}/arduino/test - Test Arduino reading',
            f'{base_url}/arduino/reconnect - Reconnect Arduino',
            f'{base_url}/debug/weight - Current status',
        ],
        'api': [
            f'{base_url}/api/current_data - Live JSON data',
            f'{base_url}/system/info - System info',
        ]
    }
    return jsonify(help_info)

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("=" * 60)
    print("PIGGY BANK TRACKER - Rs.2 Coin Counter with Telegram Alerts")
    print("=" * 60)
    print(f"📊 Dashboard: http://localhost:5000")
    print(f"🎯 Goals: http://localhost:5000/goals")
    print(f"🆘 Help: http://localhost:5000/help")
    print(f"🤖 Telegram Chat ID: {telegram_bot.chat_id}")
    print("🔔 Alert threshold: Weight drop > 0.016g (more than 2 Rs.2 coins removed)")
    print("🔔 Cooldown: 5 minutes between alerts")
    print("=" * 60)
    print("Testing endpoints:")
    print(f" • Force alert: http://localhost:5000/force_alert")
    print(f" • Simulate removal: http://localhost:5000/simulate/weight/50.0")
    print(f" • Test big drop: http://localhost:5000/test/anomaly/100/99.9")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)