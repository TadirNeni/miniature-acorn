import os
import time
import random
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
# ADDED: session, redirect, url_for, flash
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
# ADDED: wraps
from functools import wraps
from sniffer import NetworkInterface

# Machine Learning Imports
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from xgboost import XGBClassifier

app = Flask(__name__)
app.secret_key = "super_secret_ids_key" # REQUIRED for sessions/login
# ==========================================
# CHAPTER 4: CORE SUBSYSTEM CLASSES
# ==========================================

class DatasetManager:
    """Handles loading, cleaning, encoding, and normalising Parquet/CSV datasets."""
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.categorical_cols = []
        self.X_train = self.X_test = self.y_train = self.y_test = None

    def load_and_preprocess(self, dataset_name):
        parquet_path = f"datasets/{dataset_name}.parquet"
        csv_path = f"datasets/{dataset_name}.csv"
        
        try:
            if os.path.exists(parquet_path):
                df = pd.read_parquet(parquet_path)
                format_used = "Parquet"
            elif os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                format_used = "CSV"
            else:
                return {"status": "error", "message": f"Dataset {dataset_name} not found in 'datasets/'."}
            
            # Sampling for efficient prototype training
            if len(df) > 50000:
                df = df.sample(n=50000, random_state=42)
            
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(inplace=True)
            
            target_col = df.columns[-1]
            X = df.drop(columns=[target_col])
            y = df[target_col]
            
            # Handle Categorical Features (Strings/Categories)
            self.categorical_cols = X.select_dtypes(include=['object', 'category']).columns
            for col in self.categorical_cols:
                X[col] = LabelEncoder().fit_transform(X[col].astype(str))
            
            # Encode Target Labels
            y_encoded = self.label_encoder.fit_transform(y.astype(str))
            
            # Scale Numerical Data
            X_scaled = self.scaler.fit_transform(X)
            
            # Split Data
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
                X_scaled, y_encoded, test_size=0.2, random_state=42
            )
            
            return {"status": "success", "message": f"Loaded {len(df)} rows from {format_used}. Features normalized."}
        except Exception as e:
            return {"status": "error", "message": f"Preprocessing error: {str(e)}"}

class EnsembleModel:
    """Trains base learners (RF, XGB, SVM) and establishes the Voting Classifier."""
    def __init__(self):
        self.is_trained = False
        self.model = None
        self.metrics = {}

    def train_model(self, X_train, y_train, X_test, y_test):
        try:
            # Base Learners
            rf = RandomForestClassifier(n_estimators=50, random_state=42)
            xgb = XGBClassifier(eval_metric='mlogloss', random_state=42)
            svm = SVC(kernel='linear', probability=True, random_state=42)
            
            # Ensemble (Voting Classifier)
            self.model = VotingClassifier(
                estimators=[('rf', rf), ('xgb', xgb), ('svm', svm)],
                voting='soft'
            )
            
            self.model.fit(X_train, y_train)
            self.is_trained = True
            
            # Evaluate Performance
            y_pred = self.model.predict(X_test)
            self.metrics = {
                'accuracy': accuracy_score(y_test, y_pred) * 100,
                'precision': precision_score(y_test, y_pred, average='macro', zero_division=0) * 100,
                'recall': recall_score(y_test, y_pred, average='macro', zero_division=0) * 100,
                'f1': f1_score(y_test, y_pred, average='macro', zero_division=0) * 100
            }
            return {"status": "success", "message": f"Ensemble trained! Accuracy: {self.metrics['accuracy']:.2f}%"}
        except Exception as e:
            return {"status": "error", "message": f"Training failed: {str(e)}"}

    def predict(self, feature_vector, label_encoder):
        if not self.is_trained: return "Engine Offline"
        pred_idx = self.model.predict(feature_vector)[0]
        return label_encoder.inverse_transform([pred_idx])[0]

class FeatureExtractor:
    """Prepares live network data for the model."""
    def __init__(self, dataset_mgr):
        self.dataset_mgr = dataset_mgr

    def extract_features(self, raw_dict):
        df_live = pd.DataFrame([raw_dict])
        # Note: If raw_dict has strings, you must apply the same encoding as training
        scaled_features = self.dataset_mgr.scaler.transform(df_live)
        return scaled_features

class ModelPersistence:
    """Saves and loads the entire pipeline."""
    def save_all(self, model, scaler, encoder, filename="ids_pipeline.pkl"):
        try:
            joblib.dump({'model': model, 'scaler': scaler, 'encoder': encoder}, filename)
            return {"status": "success", "message": f"Pipeline saved to {filename}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def load_all(self, filename="ids_pipeline.pkl"):
        if not os.path.exists(filename): return {"status": "error", "message": "Save file not found."}
        try:
            data = joblib.load(filename)
            return {"status": "success", "data": data, "message": "Pipeline loaded successfully."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# ==========================================
# SYSTEM INITIALIZATION
# ==========================================
dataset_mgr = DatasetManager()
ensemble_model = EnsembleModel()
feature_extractor = FeatureExtractor(dataset_mgr)
persistence = ModelPersistence()

# Global variable for manual attack testing
force_attack = False

# --- SECURITY DECORATOR ---
# Add this above your routes to protect Admin-only pages
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            flash("Unauthorized: Administrative privileges required.")
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- LOGIN ROUTE ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')
        role = request.form.get('role')

        # Logic for Admin
        if user == "admin" and pw == "admin123" and role == "admin":
            session['user'] = "Administrator"
            session['role'] = "admin"
            return redirect(url_for('dashboard'))
        
        # Logic for Analyst
        elif user == "analyst" and pw == "analyst123" and role == "analyst":
            session['user'] = "SOC Analyst"
            session['role'] = "analyst"
            return redirect(url_for('dashboard'))
        
        else:
            flash("Invalid credentials or role mismatch.")
            return redirect(url_for('login'))

    return render_template('login.html')

# --- DASHBOARD ROUTE ---
@app.route('/dashboard')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    # Redirect based on role
    if session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    else:
        return render_template('analyst_dashboard.html')

# --- LOGOUT ROUTE ---
@app.route('/logout')
def logout():
    session.clear() # This "forgets" the user
    flash("Successfully logged out.")
    return redirect(url_for('login'))
# ==========================================
# FLASK ROUTES (The Controller)
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/preprocess', methods=['POST'])
def api_preprocess():
    dataset = request.json.get('dataset', 'nsl-kdd')
    return jsonify(dataset_mgr.load_and_preprocess(dataset))

@app.route('/api/train', methods=['POST'])
@admin_required 
def api_train():
    if dataset_mgr.X_train is None:
        return jsonify({"status": "error", "message": "Preprocess dataset first!"})
    
    res = ensemble_model.train_model(
        dataset_mgr.X_train, 
        dataset_mgr.y_train, 
        dataset_mgr.X_test, 
        dataset_mgr.y_test
    )
    
    if res["status"] == "success": 
        res["metrics"] = ensemble_model.metrics
        
    return jsonify(res)

@app.route('/api/save', methods=['POST'])
def api_save():
    if not ensemble_model.is_trained: return jsonify({"status": "error", "message": "No trained model."})
    return jsonify(persistence.save_all(ensemble_model.model, dataset_mgr.scaler, dataset_mgr.label_encoder))

@app.route('/api/load', methods=['POST'])
def api_load():
    res = persistence.load_all()
    if res["status"] == "success":
        ensemble_model.model = res["data"]["model"]
        dataset_mgr.scaler = res["data"]["scaler"]
        dataset_mgr.label_encoder = res["data"]["encoder"]
        ensemble_model.is_trained = True
    return jsonify(res)

# --- NEW PRESENTATION LOGIC ---
# Global variable to track how long the attack should last
attack_end_time = 0 

@app.route('/trigger_attack', methods=['POST'])
def trigger_attack():
    global attack_end_time
    # Set the attack window to last for exactly 10 seconds from right now
    attack_end_time = time.time() + 10 
    return jsonify({"status": "ATTACK INITIATED (10 Seconds)"})

@app.route('/analyze', methods=['GET'])
def analyze():
    global attack_end_time
    
    # 1. System initializing state
    if not ensemble_model.is_trained:
        dummy_flow = {"Destination Port": 0, "Protocol": 0, "Flow Duration": 0, "Total Fwd Packets": 0}
        return jsonify({"prediction": "System Ready", "status": "success", "data": dummy_flow})

    try:
        # 2. THE DEMO TRIGGER: Check if we are inside the 10-second attack window
        if time.time() < attack_end_time:
            # Generate highly malicious-looking traffic for the Analyst table
            malicious_flow = {
                "Destination Port": 80,
                "Protocol": 6, 
                "Flow Duration": random.randint(10, 50), # extremely fast connections
                "Total Fwd Packets": random.randint(500, 2500) # massive packet flood (DoS signature)
            }
            return jsonify({"prediction": "SIMULATED DOS", "status": "danger", "data": malicious_flow})
            
        # 3. Normal Traffic Generation & ML Prediction (When no attack is active)
        raw_flow = {
            "Destination Port": random.choice([80, 443, 22, 3389]),
            "Protocol": random.choice([6, 17]), 
            "Flow Duration": random.randint(100, 15000),
            "Total Fwd Packets": random.randint(1, 50)
        }
        
        features = feature_extractor.extract_features(raw_flow)
        prediction = ensemble_model.predict(features, dataset_mgr.label_encoder)
        
        status = "danger" if str(prediction).lower() not in ['normal', 'benign'] else "success"
        
        return jsonify({
            "prediction": str(prediction).upper(), 
            "status": status, 
            "data": raw_flow
        })
        
    except Exception as e:
        # Fallback if there is an error
        fallback_flow = {"Destination Port": "N/A", "Protocol": "N/A", "Flow Duration": "N/A", "Total Fwd Packets": "N/A"}
        return jsonify({"prediction": "LISTENING...", "status": "secondary", "data": fallback_flow})
            
if __name__ == '__main__':
    os.makedirs('datasets', exist_ok=True)
    app.run(debug=True, port=5000)