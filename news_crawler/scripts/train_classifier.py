import pandas as pd
import json
import re
import os
import sys
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from numpy import unique
from typing import List, Dict, Any

# path configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if "scripts" in PROJECT_ROOT:
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Dynamic data loading
# Collect all json files from the data directory containing labeled training samples
data_files: List[str] = [
    os.path.join(DATA_DIR, f)
    for f in os.listdir(DATA_DIR)
    if f.endswith('.json') and os.path.isfile(os.path.join(DATA_DIR, f))
]

all_data = []

# Validate data availability
if not data_files:
    sys.stderr.write(f"Error: No JSON files found in {DATA_DIR}. Training aborted.\n")
    sys.exit(1)

print(f"loading {len(data_files)} datasets for training")

# Aggregate data from all identified sources
for file_path in data_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            all_data.extend(data)
    except json.JSONDecodeError as e:
        print(f"Skipping {os.path.basename(file_path)}: Invalid JSON format.")
        continue
    except Exception as e:
        print(f"Skipping {os.path.basename(file_path)}: {str(e)}")
        continue

df = pd.DataFrame(all_data)

# Data cleaning keep only samples with a target label
if "label" not in df.columns:
    sys.stderr.write("Error: 'label' column missing from dataset.\n")
    sys.exit(1)

df = df[df["label"].notnull()]

if df.empty:
    sys.stderr.write("Error: Dataset is empty after label filtering.\n")
    sys.exit(1)

# Preprocessing: Handle missing values for numerical and categorical features
# This ensures consistency during the mathematical training process
df.fillna({
    "title_length": 0,
    "text_length": 0,
    "text_density": 0,
    "url_length": 0,
    "url_depth": 0,
    "has_date_pattern_in_url": False,
    "xpath_depth": 0,
    "xpath_contains_article": False,
    "xpath_contains_main_content": False,
    "xpath_contains_story": False,
    "is_article_in_category": False
}, inplace=True)

# Feature selection for the Random Forest model
# Must match the features extracted during the crawling phase
features: List[str] = [
    "url_length",
    "url_depth",
    "title_length",
    "text_length",
    "text_density",
    "has_date_pattern_in_url",
    "xpath_depth",
    "xpath_contains_article",
    "xpath_contains_main_content",
    "xpath_contains_story",
    "is_article_in_category"
]

# Robustness check: Verify all required feature columns exist
for feature in features:
    if feature not in df.columns:
        sys.stderr.write(f"Error: Required feature '{feature}' missing from data.\n")
        sys.exit(1)

X = df[features]
y = df["label"]

# Categorical label encoding
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# Dataset splitting: 75% training, 25% testing
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.25, random_state=42)

# Model Training: Random Forest Classifier
# Parameters chosen to balance complexity and generalization
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Evaluation Phase
y_pred = clf.predict(X_test)
labels_present = sorted(unique(y_test.tolist() + y_pred.tolist()))

print("\n Model Performance Report ")
print(classification_report(
    y_test, y_pred,
    labels=labels_present,
    target_names=label_encoder.inverse_transform(labels_present)
))

print("\nConfusion Matrix")
print(confusion_matrix(y_test, y_pred))

# Persistence: Save model and metadata for production use
os.makedirs(MODELS_DIR, exist_ok=True)
joblib.dump(clf, os.path.join(MODELS_DIR, "link_classifier.pkl"))
joblib.dump(label_encoder, os.path.join(MODELS_DIR, "label_encoder.pkl"))
joblib.dump(features, os.path.join(MODELS_DIR, "feature_names.pkl"))

print(f"\nModel and features successfully exported to: {MODELS_DIR}")