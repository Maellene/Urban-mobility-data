import os
import pandas as pd


def log_rejections(
    original_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    output_filename: str = "rejection_log.csv"
):
    """
    Logs rejected records with reasons.
    This provides transparency for data cleaning decisions.
    """

    output_dir = "../../data/processed"
    os.makedirs(output_dir, exist_ok=True)

    rejection_stats = []

    # Total rows
    total_rows = len(original_df)
    remaining_rows = len(cleaned_df)

    rejection_stats.append({
        "reason": "Total raw records",
        "count": total_rows
    })

    rejection_stats.append({
        "reason": "Records after full pipeline",
        "count": remaining_rows
    })

    rejection_stats.append({
        "reason": "Total rejected records",
        "count": total_rows - remaining_rows
    })

    log_df = pd.DataFrame(rejection_stats)

    output_path = os.path.join(output_dir, output_filename)
    log_df.to_csv(output_path, index=False)

    print(f"Rejection log saved to {output_path}")
