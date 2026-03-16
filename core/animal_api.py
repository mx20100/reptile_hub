from flask import Blueprint, request, jsonify
import datetime
from core.database import get_db
from core.registry import calculate_feeder, get_available_species

# Create Blueprint
animal_bp = Blueprint('animal_bp', __name__)

@animal_bp.route('/api/data', methods=['GET'])
def get_data():
    conn = get_db()
    animals = conn.execute("SELECT * FROM animals").fetchall()
    result = []
    
    # attempt to read current theme once; fall back to 'light' if anything goes wrong
    try:
        theme_row = conn.execute("SELECT value FROM settings WHERE name='theme'").fetchone()
        current_theme = theme_row['value'] if theme_row else 'light'
    except Exception:
        # table might not exist yet (very early database, migrated later)
        current_theme = 'light'

    for row in animals:
        animal = dict(row)
        # convert sqlite integer to python bool and ensure key exists
        animal['burmating'] = bool(animal.get('burmating', 0))
        
        # Feeding logic
        last_fed_log = conn.execute("SELECT timestamp FROM logs WHERE animal_id=? AND action='fed' ORDER BY timestamp DESC LIMIT 1", (animal['id'],)).fetchone()
        if last_fed_log:
            last_fed_date = datetime.datetime.strptime(last_fed_log['timestamp'], "%Y-%m-%d %H:%M:%S")
            animal['last_fed'] = last_fed_date.strftime("%Y-%m-%d")
            next_fed_date = last_fed_date + datetime.timedelta(days=animal['feed_days'])
            animal['next_fed'] = next_fed_date.strftime("%Y-%m-%d")
            
            # Calculate color status based on overdue days
            days_overdue = (datetime.datetime.now() - next_fed_date).days
            if days_overdue > 0:
                animal['status'] = "critical"
            elif days_overdue == 0:
                animal['status'] = "warning"
            else:
                animal['status'] = "good"
        else:
            animal['last_fed'] = "Never"
            animal['next_fed'] = "ASAP"
            animal['status'] = "critical"
            
        # Weight and feeder recommendation logic
        last_weight = conn.execute("SELECT value, timestamp FROM logs WHERE animal_id=? AND action='weighed' ORDER BY timestamp DESC LIMIT 1", (animal['id'],)).fetchone()
        if last_weight:
            weight_val = last_weight['value']
            animal['last_weight'] = f"{int(float(weight_val))}g"
            animal['last_weighed_date'] = datetime.datetime.strptime(last_weight['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            
            # Calculate feeder recommendation using the Registry
            rec = calculate_feeder(animal['species'], weight_val)
            if isinstance(rec, dict):
                animal['feeder_rec'] = f"{rec['qty']}x {rec['size']} (Suggested: {rec['freq']})"
            elif isinstance(rec, str):
                animal['feeder_rec'] = rec
            else:
                animal['feeder_rec'] = "No chart available for this species yet."
        else:
            animal['last_weight'] = "No data"
            animal['last_weighed_date'] = "Never"
            animal['feeder_rec'] = "Weigh animal to calculate feeder size."
            
        result.append(animal)

    conn.close()
    return jsonify({
        "animals": result,
        "theme": current_theme
    })

@animal_bp.route('/api/theme', methods=['POST'])
def save_theme():
    data = request.json
    new_theme = data.get('theme', 'light')
    conn = get_db()
    # make sure the table is around; init_db should have run, but be defensive
    conn.execute('''CREATE TABLE IF NOT EXISTS settings (
                        name TEXT PRIMARY KEY,
                        value TEXT)''')
    conn.execute("INSERT OR REPLACE INTO settings (name, value) VALUES ('theme', ?)", (new_theme,))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@animal_bp.route('/api/weight_history/<int:animal_id>', methods=['GET'])
def get_weight_history(animal_id):
    conn = get_db()
    # Fetch all weight logs for this specific animal, ordered from oldest to newest
    logs = conn.execute("SELECT value, timestamp FROM logs WHERE animal_id=? AND action='weighed' ORDER BY timestamp ASC", (animal_id,)).fetchall()
    conn.close()
    
    history = []
    for log in logs:
        # We only want the Date (YYYY-MM-DD), not the exact time, so we split the timestamp
        date_only = log['timestamp'].split(' ')[0] 
        history.append({
            'date': date_only,
            'weight': float(log['value'])
        })
        
    return jsonify(history)

@animal_bp.route('/api/catalog', methods=['GET'])
def get_catalog():
    return jsonify(get_available_species())

@animal_bp.route('/api/add', methods=['POST'])
def add_animal():
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO animals (name, species, category, feed_days, burmating) VALUES (?, ?, ?, ?, 0)",
                 (data['name'], data['species'], data['category'], data['feed_days']))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@animal_bp.route('/api/edit/<int:animal_id>', methods=['POST'])
def edit_animal(animal_id):
    data = request.json
    conn = get_db()
    
    # Update the main animal profile (and optionally burmation)
    fields = [data['name'], data['category'], data['species'], data['feed_days']]
    query = '''
        UPDATE animals 
        SET name=?, category=?, species=?, feed_days=?
    '''
    if 'burmating' in data:
        query += ', burmating=?'
        fields.append(1 if data['burmating'] else 0)
    query += ' WHERE id=?'
    fields.append(animal_id)
    conn.execute(query, fields)
    
    # Update the most recent weight log
    new_weight = data.get('last_weight')
    if new_weight and str(new_weight).strip() != "":
        # Find their most recent 'weighed' log
        last_log = conn.execute("SELECT id FROM logs WHERE animal_id=? AND action='weighed' ORDER BY timestamp DESC LIMIT 1", (animal_id,)).fetchone()
        
        if last_log:
            # Update the existing log
            conn.execute("UPDATE logs SET value=? WHERE id=?", (new_weight, last_log['id']))
        else:
            # If they didn't have a weight log yet, create one
            conn.execute("INSERT INTO logs (animal_id, action, value) VALUES (?, 'weighed', ?)", (animal_id, new_weight))
            
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@animal_bp.route('/api/action', methods=['POST'])
def log_action():
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO logs (animal_id, action, value) VALUES (?, ?, ?)",
                 (data['animal_id'], data['action'], data.get('value')))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@animal_bp.route('/api/delete/<int:id>', methods=['DELETE'])
def delete_animal(id):
    conn = get_db()
    conn.execute("DELETE FROM animals WHERE id=?", (id,))
    conn.execute("DELETE FROM logs WHERE animal_id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
@animal_bp.route('/api/burmation/<int:animal_id>', methods=['POST'])
def set_burmation(animal_id):
    """Toggle or set the burmation flag for an animal.

    The front end will send ``{"burmating": true}`` or ``false``; we
    persist it as an integer (0/1) in the animals table.  This endpoint
    exists separately to avoid requesting all fields required by the
    full ``/api/edit`` handler when only the burmation state needs to
    change.
    """
    data = request.json or {}
    flag = 1 if data.get('burmating') else 0
    conn = get_db()
    conn.execute("UPDATE animals SET burmating=? WHERE id=?", (flag, animal_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True})
