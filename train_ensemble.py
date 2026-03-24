import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, AdaBoostClassifier
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, accuracy_score

# 1. Load the Unified Dataset
print("📂 Loading cicids2017.parquet...")
df = pd.read_parquet('datasets/cicids2017.parquet')

df.columns = df.columns.str.strip()

# 2. Preprocessing
print("🛠 Preprocessing data...")
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

X = df.drop('Label', axis=1)
y = df['Label']

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 3. Define Base Models
print("🧠 Initializing Ensemble Members...")
rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
# Cleaned up the warning by removing use_label_encoder
xgb = XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, eval_metric='mlogloss')
# Replaced the slow SVM with AdaBoost
ada = AdaBoostClassifier(n_estimators=100, random_state=42, algorithm='SAMME')

# 4. Create the Voting Ensemble
print("🗳 Building the Voting Classifier (RF + XGB + AdaBoost)...")
ensemble = VotingClassifier(
    estimators=[('rf', rf), ('xgb', xgb), ('ada', ada)],
    voting='soft' 
)

# 5. Train
print("🚀 Training... This will be MUCH faster now.")
ensemble.fit(X_train_scaled, y_train)

# 6. Evaluate
y_pred = ensemble.predict(X_test_scaled)
print("\n--- PERFORMANCE REPORT ---")
print(f"Overall Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=le.classes_))

# 7. Save Artifacts
print("💾 Saving model, scaler, and label encoder...")
joblib.dump(ensemble, 'models/ensemble_model.joblib')
joblib.dump(scaler, 'models/scaler.joblib')
joblib.dump(le, 'models/label_encoder.joblib')

print("\n✅ DONE. Your IDS engine is ready.")