from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import os
import subprocess

app = Flask(__name__)
DB_FILE = 'reptiles.db'
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Animals table
    c.execute('''CREATE TABLE IF NOT EXISTS animals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, 
                  species TEXT, feed_days INTEGER, meal_size INTEGER)''')
    # Logs table
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, animal_id INTEGER, 
                  action TEXT, value REAL, timestamp DATETIME)''')
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'light')")
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    # Check if WiFi is set up
    if not os.path.exists('setup_complete.txt'):
        return render_template('wifi_setup.html')
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    conn = get_db()
    animals = [dict(row) for row in conn.execute("SELECT * FROM animals").fetchall()]
    theme = conn.execute("SELECT value FROM settings WHERE key='theme'").fetchone()['value']
    
    # Calculate next feed dates
    for animal in animals:
        # Get feeding data
        last_fed = conn.execute("SELECT timestamp FROM logs WHERE animal_id=? AND action='fed' ORDER BY timestamp DESC LIMIT 1", (animal['id'],)).fetchone()
        if last_fed:
            last_fed_date = datetime.datetime.strptime(last_fed['timestamp'], "%Y-%m-%d %H:%M:%S")
            animal['last_fed'] = last_fed_date.strftime("%Y-%m-%d")
            next_fed = last_fed_date + datetime.timedelta(days=animal['feed_days'])
            animal['next_fed'] = next_fed.strftime("%Y-%m-%d")
            animal['needs_feeding'] = datetime.datetime.now() >= next_fed
        else:
            animal['last_fed'] = "Never"
            animal['next_fed'] = "Now"
            animal['needs_feeding'] = True
            
        # Get weight data (NEW ADDITION)
        last_weight = conn.execute("SELECT value, timestamp FROM logs WHERE animal_id=? AND action='weighed' ORDER BY timestamp DESC LIMIT 1", (animal['id'],)).fetchone()
        if last_weight:
            animal['last_weight'] = f"{int(last_weight['value'])}g"
            animal['last_weighed_date'] = datetime.datetime.strptime(last_weight['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        else:
            animal['last_weight'] = "No data"
            animal['last_weighed_date'] = "Never"

    conn.close()
    return jsonify({'animals': animals, 'theme': theme})

@app.route('/api/action', methods=['POST'])
def log_action():
    data = request.json
    conn = get_db()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO logs (animal_id, action, value, timestamp) VALUES (?, ?, ?, ?)",
                 (data['animal_id'], data['action'], data.get('value', 0), timestamp))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/animal', methods=['POST', 'DELETE'])
def manage_animal():
    conn = get_db()
    if request.method == 'POST':
        data = request.json
        conn.execute("INSERT INTO animals (name, category, species, feed_days, meal_size) VALUES (?, ?, ?, ?, ?)",
                     (data['name'], data['category'], data['species'], data['feed_days'], data.get('meal_size', 0)))
    elif request.method == 'DELETE':
        animal_id = request.json['id']
        conn.execute("DELETE FROM animals WHERE id=?", (animal_id,))
        conn.execute("DELETE FROM logs WHERE animal_id=?", (animal_id,)) # Clear logs too
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/theme', methods=['POST'])
def update_theme():
    theme = request.json['theme']
    conn = get_db()
    conn.execute("UPDATE settings SET value=? WHERE key='theme'", (theme,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/wifi/current', methods=['GET'])
def current_wifi():
    try:
        # Asks nmcli for the active network
        result = subprocess.run(['/usr/bin/sudo', '/usr/bin/nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if line.startswith('yes:'):
                return jsonify({'ssid': line.split(':')[1]})
        return jsonify({'ssid': 'Not Connected'})
    except Exception:
        return jsonify({'ssid': 'Unknown'})

@app.route('/wifi_setup')
def wifi_setup():
    # Allows to manually navigate to the Wi-Fi screen
    return render_template('wifi_setup.html')

@app.route('/api/wifi/scan', methods=['GET'])
def scan_wifi():
    try:
        # Use absolute paths so systemd knows exactly where the tools are
        result = subprocess.run(['/usr/bin/sudo', '/usr/bin/nmcli', '-t', '-f', 'SSID', 'dev', 'wifi'], capture_output=True, text=True)
        networks = list(set([line.strip() for line in result.stdout.split('\n') if line.strip()]))
        return jsonify({'networks': networks})
    except Exception as e:
        print(f"Scan error: {e}") # Prints to the system journal for debugging
        return jsonify({'networks': [], 'error': str(e)}), 500

@app.route('/api/wifi/connect', methods=['POST'])
def connect_wifi():
    data = request.json
    ssid = data.get('ssid')
    password = data.get('password')
    try:
        # Absolute paths for connecting as well
        result = subprocess.run(['/usr/bin/sudo', '/usr/bin/nmcli', 'dev', 'wifi', 'connect', ssid, 'password', password], capture_output=True, text=True)
        if result.returncode == 0:
            with open('setup_complete.txt', 'w') as f:
                f.write('done')
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': result.stderr})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ip', methods=['GET'])
def get_ip():
    try:
        # 'hostname -I' asks the Pi for its network IP addresses
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        # It usually returns a list separated by spaces, so we grab the first one
        ip_address = result.stdout.split()[0] if result.stdout.strip() else 'Offline'
        return jsonify({'ip': ip_address})
    except Exception:
        return jsonify({'ip': 'Error'})
    
@app.route('/api/wifi/skip', methods=['POST'])
def skip_wifi():
    # User pressed skip. Just create the file so it never asks again
    with open('setup_complete.txt', 'w') as f:
        f.write('done')
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)