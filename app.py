from flask import Flask, render_template, request, jsonify
import os
import subprocess
from core.database import get_db
from core.animal_api import animal_bp

app = Flask(__name__)

# Register the animal module into the main app
app.register_blueprint(animal_bp)

# --- SYSTEM & NETWORK ROUTES ---

@app.route('/')
def index():
    if not os.path.exists('setup_complete.txt'):
        return render_template('wifi_setup.html')
    return render_template('index.html')

@app.route('/api/wifi/current', methods=['GET'])
def current_wifi():
    try:
        result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
        ssid = result.stdout.strip()
        return jsonify({'ssid': ssid if ssid else 'Disconnected'})
    except Exception:
        return jsonify({'ssid': 'Error'})

@app.route('/api/wifi/connect', methods=['POST'])
def connect_wifi():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    
    # Create the NetworkManager profile securely
    command = f"sudo nmcli dev wifi connect '{ssid}' password '{password}'"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if "successfully activated" in result.stdout:
        with open('setup_complete.txt', 'w') as f:
            f.write('done')
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result.stderr})

@app.route('/api/wifi/skip', methods=['POST'])
def skip_wifi():
    with open('setup_complete.txt', 'w') as f:
        f.write('skipped')
    return jsonify({'success': True})

@app.route('/api/ip', methods=['GET'])
def get_ip():
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip_address = result.stdout.split()[0] if result.stdout.strip() else 'Offline'
        return jsonify({'ip': ip_address})
    except Exception:
        return jsonify({'ip': 'Error'})

if __name__ == '__main__':
    # Initialize the database file if it doesn't exist
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS animals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT, species TEXT, category TEXT,
                        feed_days INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        animal_id INTEGER, action TEXT, value TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()
    
    app.run(host='0.0.0.0', port=5000)