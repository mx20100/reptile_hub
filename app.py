from flask import Flask, render_template, request, jsonify
import os
import re
import subprocess
from core.database import init_db, get_db
from core.animal_api import animal_bp
from core.updater import update_bp

app = Flask(__name__)

# Register modules into the main app
app.register_blueprint(animal_bp)
app.register_blueprint(update_bp)

# make sure the database schema is always initialised.
# ``if __name__ == '__main__'`` only runs when the module is executed
# directly (e.g. ``python app.py``).  Under gunicorn the module is imported
# instead, so we call init_db at import time to guarantee the tables exist.
init_db()

# Re-apply the user's saved timezone on every startup so reboots don't reset it
try:
    _conn = get_db()
    _tz_row = _conn.execute("SELECT value FROM settings WHERE name='timezone'").fetchone()
    _conn.close()
    if _tz_row:
        subprocess.run(['sudo', 'timedatectl', 'set-timezone', _tz_row['value']],
                       capture_output=True, text=True, timeout=10)
except Exception:
    pass

# --- SYSTEM & NETWORK ROUTES ---

@app.route('/')
def index():
    if not os.path.exists('setup_complete.txt'):
        return render_template('wifi_setup.html')
    return render_template('index.html')

@app.route('/wifi_setup')
def wifi_setup():
    return render_template('wifi_setup.html')

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
        # Get the real Network IP (e.g., 192.168.x.x)
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        ip_address = result.stdout.split()[0] if result.stdout.strip() else 'Offline'
        
        # If the browser is accessing it, show the network IP with the port
        host = f"{ip_address}:5000" if ip_address != 'Offline' else 'Offline'
        
        return jsonify({'ip': ip_address, 'host': host})
    except Exception:
        return jsonify({'ip': 'Error', 'host': ''})

def _apply_timezone(tz):
    """Write timezone to the database and apply it to the system via timedatectl."""
    # Persist in DB so it survives reboots even if timedatectl fails
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (name, value) VALUES ('timezone', ?)", (tz,))
    conn.commit()
    conn.close()
    # Best-effort apply to the system (requires sudoers entry on Pi)
    subprocess.run(['sudo', 'timedatectl', 'set-timezone', tz],
                   capture_output=True, text=True, timeout=10)


@app.route('/api/timezone', methods=['GET'])
def get_timezone():
    """Return the current timezone (DB value takes priority over /etc/timezone)."""
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE name='timezone'").fetchone()
    conn.close()
    if row:
        return jsonify({'timezone': row['value']})
    try:
        with open('/etc/timezone', 'r') as f:
            tz = f.read().strip()
    except Exception:
        tz = 'UTC'
    return jsonify({'timezone': tz})


@app.route('/api/timezone', methods=['POST'])
def set_timezone():
    """Set the Pi's system timezone and save it to the database."""
    data = request.json
    tz = data.get('timezone', 'UTC')
    if not re.match(r'^[A-Za-z0-9/_+-]+$', tz):
        return jsonify({'success': False, 'error': 'Invalid timezone'}), 400
    try:
        _apply_timezone(tz)
        return jsonify({'success': True, 'timezone': tz})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # ensure the database schema is up to date before starting
    init_db()

    app.run(host='0.0.0.0', port=5000)
