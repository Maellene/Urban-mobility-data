"""
load_data.py

Purpose:
- Load large NYC Taxi datasets from disk
- Inspect structure safely
- DO NOT modify or clean data

This is the first step in the data pipeline.
"""

import os
import glob
import pandas as pd
from data_pipeline.save_data import save_cleaned_data

# GeoJSON files are spatial → geopandas
try:
    import geopandas as gpd
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False


# -----------------------------
# Helper function for safe printing
# -----------------------------
def inspect_dataframe(df, name):
    """
    Prints safe, high-level information about a DataFrame.
    This avoids memory issues with large datasets.
    """
    print(f"\n--- {name} ---")
    print("Columns:")
    print(df.columns)

    print("\nData types:")
    print(df.dtypes)

    print("\nFirst 5 rows:")
    print(df.head())

    print(f"\nTotal rows: {len(df)}")


# -----------------------------
# Load Parquet: Trip Data
# -----------------------------
def load_trip_data(parquet_path):
    """
    Loads NYC taxi trip data from a Parquet or CSV file.
    Tries the exact path first; if missing, searches for
    `yellow_tripdata_*` files relative to this script.
    """
    # If the exact path exists, load based on its extension.
    if os.path.exists(parquet_path):
        print(f"\nLoading trip data from {parquet_path}")
        lower = parquet_path.lower()
        if lower.endswith(".parquet"):
            df = pd.read_parquet(parquet_path, engine="pyarrow")
        elif lower.endswith(".csv"):
            df = pd.read_csv(parquet_path)
        else:
            # Unknown extension — try parquet first, then CSV
            try:
                df = pd.read_parquet(parquet_path, engine="pyarrow")
            except Exception:
                df = pd.read_csv(parquet_path)
        inspect_dataframe(df, "Trip Data")
        return df

    # If the placeholder path wasn't found, look for any matching trip file.
    # Resolve the search directory relative to this script so running from
    # different CWDs (tests, CI, user shell) still finds the data.
    search_dir_rel = os.path.dirname(parquet_path) or "."
    search_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), search_dir_rel))
    candidates = glob.glob(os.path.join(search_dir, "yellow_tripdata_*.*"))
    if candidates:
        # Prefer parquet files if present
        parquet_candidates = [p for p in candidates if p.lower().endswith(".parquet")]
        csv_candidates = [p for p in candidates if p.lower().endswith(".csv")]
        chosen = parquet_candidates[0] if parquet_candidates else csv_candidates[0]
        print(f"\nFound trip data file: {chosen} — loading that instead of {parquet_path}")
        return load_trip_data(chosen)

    raise FileNotFoundError(f"Trip data file not found: {parquet_path}")


# -----------------------------
# Load CSV: Zone Lookup
# -----------------------------
def load_zone_lookup(csv_path):
    """
    Loads taxi zone lookup table.
    Maps location IDs to boroughs and zones.
    """
    # Try the exact path first
    if os.path.exists(csv_path):
        print(f"\nLoading zone lookup from {csv_path}")
        df = pd.read_csv(csv_path)
        inspect_dataframe(df, "Zone Lookup")
        return df

    # If not found, search relative to this script (handles different CWDs)
    search_dir_rel = os.path.dirname(csv_path) or "."
    search_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), search_dir_rel))
    candidates = glob.glob(os.path.join(search_dir, "taxi_zone_lookup.*"))
    if candidates:
        chosen = candidates[0]
        print(f"\nFound zone lookup file: {chosen} — loading that instead of {csv_path}")
        df = pd.read_csv(chosen)
        inspect_dataframe(df, "Zone Lookup")
        return df

    raise FileNotFoundError(f"Zone lookup file not found: {csv_path}")


# -----------------------------
# Load GeoJSON: Zone Shapes
# -----------------------------
def load_zone_shapes(geojson_path):
    """
    Loads spatial zone boundaries.
    Requires geopandas.
    """
    if not GEOPANDAS_AVAILABLE:
        print("\nGeopandas not installed. Skipping zone shapes load.")
        return None

    # If the exact path exists, try loading it (handles .geojson, .shp, etc.)
    if os.path.exists(geojson_path):
        print(f"\nLoading zone shapes from {geojson_path}")
        gdf = gpd.read_file(geojson_path)
        inspect_dataframe(gdf, "Zone Shapes")
        return gdf

    # Search for common zone shapes files relative to this script
    search_dir_rel = os.path.dirname(geojson_path) or "."
    search_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), search_dir_rel))

    candidates = []
    # Look for taxi_zones.* (e.g., taxi_zones.shp / taxi_zones.geojson)
    candidates.extend(glob.glob(os.path.join(search_dir, "taxi_zones.*")))
    # Also search inside taxi_zones/ directory for shapefiles
    shp_dir = os.path.join(search_dir, "taxi_zones")
    if os.path.isdir(shp_dir):
        candidates.extend(glob.glob(os.path.join(shp_dir, "*.shp")))

    if candidates:
        # Prefer geojson, then shapefile
        geojsons = [p for p in candidates if p.lower().endswith(".geojson")]
        shps = [p for p in candidates if p.lower().endswith(".shp")]
        chosen = geojsons[0] if geojsons else (shps[0] if shps else candidates[0])
        print(f"\nFound zone shapes file: {chosen} — loading that instead of {geojson_path}")
        gdf = gpd.read_file(chosen)
        inspect_dataframe(gdf, "Zone Shapes")
        return gdf

    raise FileNotFoundError(f"Zone shapes file not found: {geojson_path}")


# -----------------------------
# Main execution (for testing)
# -----------------------------
if __name__ == "__main__":
    # Adjust paths if needed
    TRIP_DATA_PATH = "../../data/raw/yellow_tripdata_YYYY_MM.parquet"
    ZONE_LOOKUP_PATH = "../../data/raw/taxi_zone_lookup.csv"
    ZONE_SHAPES_PATH = "../../data/raw/taxi_zones.geojson"

    trip_df = load_trip_data(TRIP_DATA_PATH)
    zone_lookup_df = load_zone_lookup(ZONE_LOOKUP_PATH)
    zone_shapes_gdf = load_zone_shapes(ZONE_SHAPES_PATH)

    # Save a copy of the loaded trip data for downstream steps
    save_cleaned_data(trip_df, "cleaned_trips.csv")
