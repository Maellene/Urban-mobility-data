"""
clean_data.py

Purpose:
- Clean raw NYC taxi trip data
- Remove physically impossible records
- Log all rejected records with reasons

This file performs NO feature engineering beyond what is
required to validate physical correctness.
"""

import os
import pandas as pd


# -----------------------------
# Step 1: Fix Timestamp Types
# -----------------------------
def fix_timestamps(df):
    """
    Convert pickup and dropoff timestamps to datetime.
    This is required to compute trip duration correctly.
    """
    df["tpep_pickup_datetime"] = pd.to_datetime(
        df["tpep_pickup_datetime"], errors="coerce"
    )
    df["tpep_dropoff_datetime"] = pd.to_datetime(
        df["tpep_dropoff_datetime"], errors="coerce"
    )
    return df


# -----------------------------
# Step 2: Handle Missing Values
# -----------------------------
def remove_missing_critical_fields(df):
    """
    Remove rows missing critical fields.
    These fields are required for any valid trip.
    """
    critical_fields = [
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "trip_distance",
        "fare_amount",
        "PULocationID",
        "DOLocationID",
    ]

    before = len(df)
    df_clean = df.dropna(subset=critical_fields)
    after = len(df_clean)

    rejected = df[~df.index.isin(df_clean.index)].copy()
    rejected["rejection_reason"] = "Missing critical field"

    print(f"Removed {before - after} rows due to missing critical fields")

    return df_clean, rejected


# -----------------------------
# Step 3: Remove Duplicate Trips
# -----------------------------
def remove_duplicates(df):
    """
    Remove duplicate trips based on time and location.
    """
    before = len(df)

    df_clean = df.drop_duplicates(
        subset=[
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "PULocationID",
            "DOLocationID",
        ]
    )

    after = len(df_clean)
    rejected = df[~df.index.isin(df_clean.index)].copy()
    rejected["rejection_reason"] = "Duplicate trip"

    print(f"Removed {before - after} duplicate rows")

    return df_clean, rejected


# -----------------------------
# Step 4: Compute Trip Duration
# -----------------------------
def compute_trip_duration(df):
    """
    Compute trip duration in minutes.
    Used to detect impossible trips.
    """
    df["trip_duration_minutes"] = (
        df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    return df


# -----------------------------
# Step 5: Remove Physically Impossible Trips
# -----------------------------
def remove_physical_outliers(df):
    """
    Remove trips that violate physical constraints.
    """
    conditions = (
        (df["trip_duration_minutes"] <= 0)
        | (df["trip_distance"] <= 0)
        | (df["fare_amount"] < 0)
    )

    rejected = df[conditions].copy()
    rejected["rejection_reason"] = "Physically impossible trip"

    df_clean = df[~conditions].copy()

    print(f"Removed {len(rejected)} physically impossible trips")

    return df_clean, rejected


# -----------------------------
# Main Cleaning Pipeline
# -----------------------------
def clean_trip_data(df):
    """
    Run the full cleaning pipeline.
    """
    rejection_log = []

    df = fix_timestamps(df)

    df, rejected_missing = remove_missing_critical_fields(df)
    rejection_log.append(rejected_missing)

    df, rejected_duplicates = remove_duplicates(df)
    rejection_log.append(rejected_duplicates)

    df = compute_trip_duration(df)

    df, rejected_physical = remove_physical_outliers(df)
    rejection_log.append(rejected_physical)

    # Combine all rejected records
    rejection_df = pd.concat(rejection_log, ignore_index=True)

    return df, rejection_df


# -----------------------------
# Run for testing
# -----------------------------
if __name__ == "__main__":
    from load_data import load_trip_data

    TRIP_DATA_PATH = "../../data/raw/yellow_tripdata_YYYY_MM.parquet"

    raw_df = load_trip_data(TRIP_DATA_PATH)

    clean_df, rejected_df = clean_trip_data(raw_df)

    print("\nSummary:")
    print("Original records:", len(raw_df))
    print("Clean records:", len(clean_df))
    print("Rejected records:", len(rejected_df))

    out_rel = "../../data/processed/rejected_records.csv"
    out_path = os.path.normpath(os.path.join(os.path.dirname(__file__), out_rel))
    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)
    rejected_df.to_csv(out_path, index=False)
