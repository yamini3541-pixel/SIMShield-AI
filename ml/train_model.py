import os
import sqlite3
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# -----------------------------------------
# Project paths
# -----------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "transactions.csv"
)

MODEL_DIR = os.path.join(
    BASE_DIR,
    "backend",
    "models"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "fraud_model.pkl"
)

DATABASE_FILE = os.path.join(BASE_DIR, "data", "simshield.db")

# Create model folder
os.makedirs(MODEL_DIR, exist_ok=True)


# -----------------------------------------
# Load original dataset
# -----------------------------------------

print()
print("=" * 60)
print("SIMShield AI - Model Training")
print("=" * 60)
print()

print("Loading original dataset...")

df = pd.read_csv(DATA_FILE)

print(f"Original dataset: {len(df)} records")


# -----------------------------------------
# Load human feedback from SQLite
# -----------------------------------------

if os.path.exists(DATABASE_FILE):

    print("Loading human feedback...")

    connection = sqlite3.connect(DATABASE_FILE)

    feedback_query = """
        SELECT
            t.sim_changed,
            t.new_device,
            t.location_changed,
            t.failed_otp_attempts,
            t.transaction_amount,
            t.transaction_velocity,
            f.reviewer_label AS fraud
        FROM transactions t
        INNER JOIN human_feedback f
        ON t.id = f.transaction_id
    """

    feedback_df = pd.read_sql_query(
        feedback_query,
        connection
    )

    connection.close()

else:

    feedback_df = pd.DataFrame()


# -----------------------------------------
# Add human corrections
# -----------------------------------------

if len(feedback_df) > 0:

    print(
        f"Human feedback records: "
        f"{len(feedback_df)}"
    )

    df = pd.concat(
        [
            df,
            feedback_df
        ],
        ignore_index=True
    )

else:

    print("No human feedback found.")


print(
    f"Total training records: "
    f"{len(df)}"
)


# -----------------------------------------
# Features
# -----------------------------------------

features = [
    "sim_changed",
    "new_device",
    "location_changed",
    "failed_otp_attempts",
    "transaction_amount",
    "transaction_velocity"
]

X = df[features]
y = df["fraud"]


# -----------------------------------------
# Train/Test Split
# -----------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


print()
print(
    f"Training records: "
    f"{len(X_train)}"
)

print(
    f"Testing records: "
    f"{len(X_test)}"
)


# -----------------------------------------
# Create Random Forest model
# -----------------------------------------

print()
print("Training Random Forest model...")

model = RandomForestClassifier(
    n_estimators=150,
    max_depth=10,
    random_state=42,
    class_weight="balanced"
)

model.fit(
    X_train,
    y_train
)


# -----------------------------------------
# Evaluate model
# -----------------------------------------

predictions = model.predict(X_test)

accuracy = accuracy_score(
    y_test,
    predictions
)

print()
print("=" * 60)
print("MODEL RESULTS")
print("=" * 60)

print()

print(
    f"Accuracy: "
    f"{accuracy * 100:.2f}%"
)

print()

print("Classification Report:")

print(
    classification_report(
        y_test,
        predictions,
        target_names=[
            "Legitimate",
            "Fraud"
        ]
    )
)


# -----------------------------------------
# Save model
# -----------------------------------------

joblib.dump(
    model,
    MODEL_FILE
)

print()
print("=" * 60)
print("MODEL SAVED SUCCESSFULLY")
print("=" * 60)

print()

print("Model file:")
print(MODEL_FILE)

print()

print(
    "Training completed with "
    "human feedback included."
)

print()