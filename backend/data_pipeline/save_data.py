import os
import pandas as pd


def save_cleaned_data(df: pd.DataFrame, filename: str):
    """
    Saves cleaned data to data/processed directory
    """

    output_dir = "../../data/processed"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, filename)

    df.to_csv(output_path, index=False)
    print(f"Saved cleaned data to {output_path}")
