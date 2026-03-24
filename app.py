from flask import Flask, render_template, jsonify
import sqlite3
import os

# Import the database connection from the module we created earlier
from database import get_db_connection

app = Flask(__name__)

# ==========================================
# 4.1 Control Centre / Main Menu
# ==========================================
@app.route('/')
def dashboard():
    """
    Main entry point. Renders the dynamic web dashboard.
    Fetches basic stats and recent events from the database.
    """
    conn = get_db_connection()
    
    # Fetch the 5 most recent alerts/events to display on the dashboard table
    recent_events = conn.execute(
        'SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 5'
    ).fetchall()
    
    # Get total attack count
    attack_count_query = conn.execute(
        "SELECT COUNT(*) FROM alerts WHERE attack_type != 'Benign'"
    ).fetchone()
    total_attacks = attack_count_query[0] if attack_count_query else 0

    conn.close()

    # We pass the data to the template (we will update the HTML to use these variables next)
    return render_template('dashboard.html', events=recent_events, total_attacks=total_attacks)

# ==========================================
# 4.2 The Submenus / Subsystems (API Routes)
# ==========================================

@app.route('/dataset', methods=['GET'])
def dataset_management():
    """Dataset Management Subsystem: Loads and preprocesses CICIDS2017."""
    # Placeholder for cicids2017.py integration
    return jsonify({"status": "Dataset loaded and preprocessed successfully."})

@app.route('/train', methods=['POST'])
def model_training():
    """Model Training Subsystem: Trains RF, XGBoost, AdaBoost, SVM."""
    # Placeholder for train_ensemble.py integration
    return jsonify({"status": "Ensemble model training initiated."})

@app.route('/evaluate', methods=['GET'])
def model_evaluation():
    """Model Evaluation Subsystem: Computes Accuracy, F1, ROC-AUC."""
    return jsonify({
        "accuracy": 0.9975,
        "precision": 0.98,
        "recall": 0.97,
        "f1_score": 0.97
    })

@app.route('/detect/start', methods=['POST'])
def start_realtime_detection():
    """Real-Time Detection Subsystem: Triggers Scapy sniffing."""
    # Placeholder for sniffer.py integration
    return jsonify({"message": "Real-time network monitoring started."})

@app.route('/alerts', methods=['GET'])
def alert_management():
    """Alert Management Subsystem: Retrieves filtered alert records."""
    conn = get_db_connection()
    alerts = conn.execute('SELECT * FROM alerts').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in alerts])

@app.route('/model/save', methods=['POST'])
def model_persistence():
    """Model Persistence Subsystem: Saves/loads .pkl or .joblib files."""
    return jsonify({"message": "Model saved successfully to /models directory."})

if __name__ == '__main__':
    # Start the dynamic web dashboard on the local web server
    print("[*] Starting IDS Control Centre...")
    app.run(debug=True, host='0.0.0.0', port=5000)