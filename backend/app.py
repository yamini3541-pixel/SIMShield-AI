from flask import Flask, request, jsonify
from flask_cors import CORS

import sqlite3
import os
import joblib
import pandas as pd
from datetime import datetime


# ============================================================
# APP CONFIGURATION
# ============================================================

app = Flask(__name__)
CORS(app)


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "backend", "models")

DATABASE_FILE = os.path.join(DATA_DIR, "simshield.db")
MODEL_FILE = os.path.join(MODEL_DIR, "fraud_model.pkl")


# Make sure required folders exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# LOAD MACHINE LEARNING MODEL
# ============================================================

try:
    model = joblib.load(MODEL_FILE)
    print("AI fraud model loaded successfully.")
except Exception as error:
    model = None
    print("WARNING: Could not load fraud model.")
    print(error)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    """
    Create a connection to the SQLite database.
    """
    connection = sqlite3.connect(DATABASE_FILE)

    # Allows us to access database columns by name
    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_db_connection()
    cursor = connection.cursor()

    # --------------------------------------------------------
    # Transactions table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL,

            sim_changed INTEGER NOT NULL,

            new_device INTEGER NOT NULL,

            location_changed INTEGER NOT NULL,

            failed_otp_attempts INTEGER NOT NULL,

            transaction_amount REAL NOT NULL,

            transaction_velocity INTEGER NOT NULL,

            risk_score REAL,

            risk_level TEXT,

            action TEXT,

            fraud_prediction INTEGER,

            reasons TEXT,

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # Human feedback table
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS human_feedback (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            transaction_id INTEGER NOT NULL,

            reviewer_label INTEGER NOT NULL,

            reviewer_comment TEXT,

            created_at TEXT NOT NULL,

            FOREIGN KEY(transaction_id)
                REFERENCES transactions(id)
        )
    """)

    connection.commit()
    connection.close()

    print("SQLite database initialized successfully.")


# Initialize database when application starts
initialize_database()


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "project": "SIMShield AI",
        "status": "running",
        "message": "SIMShield AI backend is running successfully."
    })


# ============================================================
# HELPER FUNCTION - CALCULATE EXPLAINABLE REASONS
# ============================================================

def generate_reasons(data):

    reasons = []

    if data["sim_changed"] == 1:
        reasons.append(
            "SIM change detected"
        )

    if data["new_device"] == 1:
        reasons.append(
            "Login or transaction from a new device"
        )

    if data["location_changed"] == 1:
        reasons.append(
            "Location change detected"
        )

    if data["failed_otp_attempts"] >= 2:
        reasons.append(
            "Multiple failed OTP attempts"
        )

    if data["transaction_amount"] >= 50000:
        reasons.append(
            "High transaction amount"
        )

    if data["transaction_velocity"] >= 4:
        reasons.append(
            "Unusually high transaction velocity"
        )

    # If no unusual signals were detected
    if not reasons:
        reasons.append(
            "No major suspicious signals detected"
        )

    return reasons


# ============================================================
# HELPER FUNCTION - RISK LEVEL
# ============================================================

def get_risk_level(risk_score):

    if risk_score >= 70:
        return "HIGH"

    elif risk_score >= 40:
        return "MEDIUM"

    else:
        return "LOW"


# ============================================================
# HELPER FUNCTION - ACTION
# ============================================================

def get_action(risk_level):

    if risk_level == "HIGH":
        return "BLOCK_AND_REVIEW"

    elif risk_level == "MEDIUM":
        return "STEP_UP_VERIFICATION"

    else:
        return "ALLOW"


# ============================================================
# FRAUD CHECK API
# ============================================================

@app.route("/api/fraud/check", methods=["POST"])
def fraud_check():

    # --------------------------------------------------------
    # Check whether model is available
    # --------------------------------------------------------

    if model is None:

        return jsonify({
            "success": False,
            "error": "Fraud detection model is not available."
        }), 500

    # --------------------------------------------------------
    # Get JSON request
    # --------------------------------------------------------

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "error": "Request body must contain JSON data."
        }), 400

    # --------------------------------------------------------
    # Validate required fields
    # --------------------------------------------------------

    required_fields = [
        "user_id",
        "sim_changed",
        "new_device",
        "location_changed",
        "failed_otp_attempts",
        "transaction_amount",
        "transaction_velocity"
    ]

    missing_fields = []

    for field in required_fields:

        if field not in data:
            missing_fields.append(field)

    if missing_fields:

        return jsonify({
            "success": False,
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }), 400

    # --------------------------------------------------------
    # Convert values to correct data types
    # --------------------------------------------------------

    try:

        user_id = str(data["user_id"])

        sim_changed = int(data["sim_changed"])

        new_device = int(data["new_device"])

        location_changed = int(
            data["location_changed"]
        )

        failed_otp_attempts = int(
            data["failed_otp_attempts"]
        )

        transaction_amount = float(
            data["transaction_amount"]
        )

        transaction_velocity = int(
            data["transaction_velocity"]
        )

    except (ValueError, TypeError):

        return jsonify({
            "success": False,
            "error": "Invalid data type in request."
        }), 400

    # --------------------------------------------------------
    # Validate values
    # --------------------------------------------------------

    if sim_changed not in [0, 1]:

        return jsonify({
            "success": False,
            "error": "sim_changed must be 0 or 1."
        }), 400

    if new_device not in [0, 1]:

        return jsonify({
            "success": False,
            "error": "new_device must be 0 or 1."
        }), 400

    if location_changed not in [0, 1]:

        return jsonify({
            "success": False,
            "error": "location_changed must be 0 or 1."
        }), 400

    if failed_otp_attempts < 0:

        return jsonify({
            "success": False,
            "error": "failed_otp_attempts cannot be negative."
        }), 400

    if transaction_amount < 0:

        return jsonify({
            "success": False,
            "error": "transaction_amount cannot be negative."
        }), 400

    if transaction_velocity < 0:

        return jsonify({
            "success": False,
            "error": "transaction_velocity cannot be negative."
        }), 400

    # --------------------------------------------------------
    # Prepare ML input
    # --------------------------------------------------------

    features = pd.DataFrame([{

        "sim_changed": sim_changed,

        "new_device": new_device,

        "location_changed": location_changed,

        "failed_otp_attempts": failed_otp_attempts,

        "transaction_amount": transaction_amount,

        "transaction_velocity": transaction_velocity

    }])

    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    prediction = int(
        model.predict(features)[0]
    )

    # --------------------------------------------------------
    # Fraud probability
    # --------------------------------------------------------

    probability = model.predict_proba(features)[0]

    fraud_probability = float(
        probability[1]
    )

        # --------------------------------------------------------
    # Risk score
    # --------------------------------------------------------

    ml_risk_score = fraud_probability * 100

    if (
        sim_changed == 1
        and new_device == 1
        and location_changed == 1
        and failed_otp_attempts >= 5
        and transaction_amount >= 50000
        and transaction_velocity >= 4
    ):
        security_risk_score = 90

    elif (
        sim_changed == 1
        and new_device == 1
        and location_changed == 1
        and failed_otp_attempts >= 3
    ):
        security_risk_score = 75
elif (
    sim_changed == 1
    and location_changed == 1
    and failed_otp_attempts >= 2
):
    security_risk_score = 45



    else:
        security_risk_score = 0

    risk_score = round(
        max(
            ml_risk_score,
            security_risk_score
        ),
        2
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    risk_level = get_risk_level(risk_score)

    # --------------------------------------------------------
    # Recommended action
    # --------------------------------------------------------

    action = get_action(risk_level)
  
    # --------------------------------------------------------
    # Explainable reasons
    # --------------------------------------------------------

    reasons = generate_reasons({

        "sim_changed": sim_changed,

        "new_device": new_device,

        "location_changed": location_changed,

        "failed_otp_attempts":
            failed_otp_attempts,

        "transaction_amount":
            transaction_amount,

        "transaction_velocity":
            transaction_velocity

    })

    # Convert reasons into text for SQLite
    reasons_text = " | ".join(reasons)

    # --------------------------------------------------------
    # Current timestamp
    # --------------------------------------------------------

    created_at = datetime.now().isoformat(
        timespec="seconds"
    )

    # --------------------------------------------------------
    # Store transaction
    # --------------------------------------------------------

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (

            user_id,

            sim_changed,

            new_device,

            location_changed,

            failed_otp_attempts,

            transaction_amount,

            transaction_velocity,

            risk_score,

            risk_level,

            action,

            fraud_prediction,

            reasons,

            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        user_id,

        sim_changed,

        new_device,

        location_changed,

        failed_otp_attempts,

        transaction_amount,

        transaction_velocity,

        risk_score,

        risk_level,

        action,

        prediction,

        reasons_text,

        created_at

    ))

    transaction_id = cursor.lastrowid

    connection.commit()

    connection.close()

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return jsonify({

        "success": True,

        "transaction_id": transaction_id,

        "user_id": user_id,

        "fraud_prediction": prediction,

        "fraud_probability": round(
            fraud_probability * 100,
            2
        ),

        "risk_score": risk_score,

        "risk_level": risk_level,

        "recommended_action": action,

        "reasons": reasons,

        "created_at": created_at

    })


# ============================================================
# GET TRANSACTIONS
# ============================================================

@app.route("/api/transactions", methods=["GET"])
def get_transactions():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()

    connection.close()

    transactions = []

    for row in rows:

        transaction = dict(row)

        # Convert reasons string back to list
        if transaction.get("reasons"):

            transaction["reasons"] = (
                transaction["reasons"]
                .split(" | ")
            )

        else:

            transaction["reasons"] = []

        transactions.append(transaction)

    return jsonify({

        "success": True,

        "count": len(transactions),

        "transactions": transactions

    })


# ============================================================
# GET SINGLE TRANSACTION
# ============================================================

@app.route("/api/transactions/<int:transaction_id>",
           methods=["GET"])
def get_transaction(transaction_id):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return jsonify({

            "success": False,

            "error": "Transaction not found."

        }), 404

    transaction = dict(row)

    if transaction.get("reasons"):

        transaction["reasons"] = (
            transaction["reasons"]
            .split(" | ")
        )

    else:

        transaction["reasons"] = []

    return jsonify({

        "success": True,

        "transaction": transaction

    })


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.route("/api/dashboard/stats",
           methods=["GET"])
def dashboard_stats():

    connection = get_db_connection()

    cursor = connection.cursor()

    # Total transactions
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
    """)

    total_transactions = cursor.fetchone()[0]

    # High risk
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'HIGH'
    """)

    high_risk = cursor.fetchone()[0]

    # Medium risk
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'MEDIUM'
    """)

    medium_risk = cursor.fetchone()[0]

    # Low risk
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE risk_level = 'LOW'
    """)

    low_risk = cursor.fetchone()[0]

    # Predicted fraud
    cursor.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE fraud_prediction = 1
    """)

    predicted_fraud = cursor.fetchone()[0]

    connection.close()

    return jsonify({

        "success": True,

        "total_transactions":
            total_transactions,

        "high_risk":
            high_risk,

        "medium_risk":
            medium_risk,

        "low_risk":
            low_risk,

        "predicted_fraud":
            predicted_fraud

    })


# ============================================================
# HUMAN REVIEW FEEDBACK
# ============================================================
@app.route("/api/review/feedback", methods=["POST"])
def submit_feedback():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "error": "Request body must contain JSON data."
        }), 400

    transaction_id = data.get("transaction_id")
    reviewer_label = data.get("reviewer_label")
    reviewer_comment = data.get("reviewer_comment", "")

    if transaction_id is None:
        return jsonify({
            "success": False,
            "error": "transaction_id is required."
        }), 400

    if reviewer_label not in [0, 1]:
        return jsonify({
            "success": False,
            "error": "reviewer_label must be 0 or 1."
        }), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    transaction = cursor.fetchone()

    if transaction is None:
        connection.close()

        return jsonify({
            "success": False,
            "error": "Transaction not found."
        }), 404

    cursor.execute("""
        INSERT INTO human_feedback (
            transaction_id,
            reviewer_label,
            reviewer_comment,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        transaction_id,
        reviewer_label,
        reviewer_comment,
        datetime.now().isoformat(timespec="seconds")
    ))

    feedback_id = cursor.lastrowid

    connection.commit()
    connection.close()

    # -----------------------------------------
    # Retrain model using human feedback
    # -----------------------------------------

    retraining_status = "failed"

    try:

        import subprocess
        import sys

        train_script = os.path.join(
            BASE_DIR,
            "ml",
            "train_model.py"
        )

        training_result = subprocess.run(
            [
                sys.executable,
                train_script
            ],
            capture_output=True,
            text=True
        )

        if training_result.returncode == 0:

            print(
                "Model retrained successfully "
                "using human feedback."
            )

            retraining_status = "success"

            global model

            model = joblib.load(MODEL_FILE)

            print(
                "Updated fraud model loaded "
                "into the running backend."
            )

        else:

            print("Model retraining failed:")
            print(training_result.stderr)

    except Exception as error:

        print("Retraining error:", error)

    return jsonify({
        "success": True,
        "message": (
            "Human feedback stored and "
            "model retraining completed."
        ),
        "feedback_id": feedback_id,
        "transaction_id": transaction_id,
        "reviewer_label": reviewer_label,
        "retraining": retraining_status
    })


# ============================================================
# PENDING HUMAN REVIEWS
# ============================================================

@app.route("/api/review/pending",
           methods=["GET"])
def pending_reviews():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT t.*

        FROM transactions t

        LEFT JOIN human_feedback f
        ON t.id = f.transaction_id

        WHERE f.id IS NULL

        ORDER BY t.id DESC

        LIMIT 100
    """)

    rows = cursor.fetchall()

    connection.close()

    transactions = []

    for row in rows:

        transaction = dict(row)

        if transaction.get("reasons"):

            transaction["reasons"] = (
                transaction["reasons"]
                .split(" | ")
            )

        else:

            transaction["reasons"] = []

        transactions.append(transaction)

    return jsonify({

        "success": True,

        "count": len(transactions),

        "pending_reviews": transactions

    })


# ============================================================
# MODEL STATUS
# ============================================================

@app.route("/api/model/status",
           methods=["GET"])
def model_status():

    model_exists = os.path.exists(
        MODEL_FILE
    )

    return jsonify({

    "success": True,

    "message": "Human feedback stored and model retraining completed.",

    "feedback_id": feedback_id,

    "transaction_id": transaction_id,

    "reviewer_label": reviewer_label,

    "retraining": retraining_status

})

# ============================================================
# ERROR HANDLER
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "error": "API endpoint not found."

    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "error": "Internal server error."

    }), 500


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("SIMShield AI Backend")
    print("=" * 60)

    print()
    print("Server starting...")

    print()
    print("Open in browser:")
    print("http://127.0.0.1:5000")

    print()
    print("Fraud Check API:")
    print("POST http://127.0.0.1:5000/api/fraud/check")

    print()
    print("=" * 60)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
