from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import threading
import time
from werkzeug.utils import secure_filename
from serial_reader import coin_tracker
from database import get_db_connection

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Background thread
def serial_reader_thread():
    if not coin_tracker.connect():
        print("Using simulated data.")
        return
    
    print("Serial reader started")
    while True:
        coin_tracker.read_weight()
        time.sleep(0.5)

thread = threading.Thread(target=serial_reader_thread, daemon=True)
thread.start()

@app.route('/')
def index():
    # Read current weight
    coin_tracker.read_weight()
    
    # Get coin data
    coins_data = coin_tracker.calculate_rs2_coins()
    
    # Get goals
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
        
        # Current Rs.2 coins and value
        current_rs2 = coins_data['rs2_count']
        current_value = coins_data['rs2_value']
        
        # Calculate progress and Rs.2 needed
        if prize > 0:
            progress = min(100, (current_value / prize) * 100)
            # Each Rs.2 gives ₹2, so divide remaining value by 2
            remaining_value = max(0, prize - current_value)
            rs2_needed = int(remaining_value / 2)
            # Add one more if there's remainder
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
    
    # Ensure all required keys exist in coins_data
    if 'remaining_weight' not in coins_data:
        coins_data['remaining_weight'] = 0.0
    
    return render_template('index.html',
                         weight=coins_data.get('total_weight', coins_data.get('weight_used', 0)),
                         coins_data=coins_data,
                         goals=goals)

@app.route('/api/current_data')
def api_current_data():
    # Read fresh data
    coin_tracker.read_weight()
    
    # Get coin data
    coins_data = coin_tracker.calculate_rs2_coins()
    
    # Get goals
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
    
    # Ensure all keys exist
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
        
        if not prize or float(prize) <= 0:
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

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    print("=" * 50)
    print("Piggy Bank Tracker - Rs.2 Coin Counter")
    print("=" * 50)
    print(f"Dashboard: http://localhost:5000")
    print(f"Manage goals: http://localhost:5000/goals")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)