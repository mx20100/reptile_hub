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
    
    for row in animals:
        animal = dict(row)
        
        # 1. FEEDING LOGIC
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
            
        # 2. WEIGHT & FEEDER REC LOGIC
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
    return jsonify(result)

@animal_bp.route('/api/catalog', methods=['GET'])
def get_catalog():
    return jsonify(get_available_species())

@animal_bp.route('/api/add', methods=['POST'])
def add_animal():
    data = request.json
    conn = get_db()
    conn.execute("INSERT INTO animals (name, species, category, feed_days) VALUES (?, ?, ?, ?)",
                 (data['name'], data['species'], data['category'], data['feed_days']))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

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
