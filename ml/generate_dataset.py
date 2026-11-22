import os
import numpy as np
import pandas as pd

# Make results reproducible
np.random.seed(42)

# Find the main project folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# Create data folder if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Number of synthetic transactions
NUM_RECORDS = 2000

data = []

for i in range(NUM_RECORDS):

    user_id = f"U{1000 + np.random.randint(0, 9000)}"

    # Security signals
    sim_changed = np.random.choice([0, 1], p=[0.90, 0.10])
    new_device = np.random.choice([0, 1], p=[0.75, 0.25])
    location_changed = np.random.choice([0, 1], p=[0.80, 0.20])

    failed_otp_attempts = np.random.choice(
        [0, 1, 2, 3, 4, 5],
        p=[0.60, 0.15, 0.10, 0.07, 0.05, 0.03]
    )

    # Transaction amount
    transaction_amount = round(
        np.random.lognormal(mean=8.0, sigma=1.0),
        2
    )

    transaction_amount = min(transaction_amount, 200000)

    # Number of transactions in a short period
    transaction_velocity = np.random.poisson(1.5)
    transaction_velocity = min(transaction_velocity, 10)

    # -----------------------------------------
    # Synthetic fraud scoring
    # -----------------------------------------

    fraud_score = 0

    if sim_changed == 1:
        fraud_score += 3

    if new_device == 1:
        fraud_score += 2

    if location_changed == 1:
        fraud_score += 2

    if failed_otp_attempts >= 2:
        fraud_score += 2

    if failed_otp_attempts >= 4:
        fraud_score += 2

    if transaction_amount >= 50000:
        fraud_score += 3

    if transaction_amount >= 100000:
        fraud_score += 2

    if transaction_velocity >= 4:
        fraud_score += 3

    if transaction_velocity >= 7:
        fraud_score += 2

    # Add small random variation
    fraud_score += np.random.choice(
        [-1, 0, 0, 0, 1],
        p=[0.10, 0.20, 0.40, 0.20, 0.10]
    )

    # Decide whether transaction is fraudulent
    fraud = 1 if fraud_score >= 6 else 0

    data.append({
        "user_id": user_id,
        "sim_changed": sim_changed,
        "new_device": new_device,
        "location_changed": location_changed,
        "failed_otp_attempts": failed_otp_attempts,
        "transaction_amount": transaction_amount,
        "transaction_velocity": transaction_velocity,
        "fraud": fraud
    })


# Convert to DataFrame
df = pd.DataFrame(data)

# Save CSV
output_file = os.path.join(DATA_DIR, "transactions.csv")

df.to_csv(output_file, index=False)

print()
print("=" * 60)
print("SIMShield AI - Synthetic Dataset Generator")
print("=" * 60)
print()

print("Dataset created successfully!")
print(f"Records: {len(df)}")
print(f"File: {output_file}")

print()
print("Fraud distribution:")
print(df["fraud"].value_counts())

print()
print("First 5 records:")
print(df.head())

print()
print("=" * 60)