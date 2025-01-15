import os
import pandas as pd
from scipy.spatial.distance import cdist
import numpy as np

log_dir = r"D:\conflict_logs"
os.makedirs(log_dir, exist_ok=True)

def create_log_files(conflicts_df, original_data, log_dir):
    for _, row in conflicts_df.iterrows():
        aircraft1_data = original_data[original_data["VIN_or_ID"] == row["Aircraft1"]]
        aircraft2_data = original_data[original_data["VIN_or_ID"] == row["Aircraft2"]]

        combined_data = pd.concat([aircraft1_data, aircraft2_data])

        conflict_id = f"{row['Aircraft1']}_{row['Aircraft2']}_{row['Timestamp1'].strftime('%Y-%m-%dT%H-%M-%S')}"
        log_file_path = os.path.join(log_dir, f"conflict_{conflict_id}.log")

        combined_data.to_csv(log_file_path, index=False)

try:
    data = pd.read_csv(r"D:\ARIA_flight_data.csv")  # Correct file path
    print("Dataset loaded successfully.")
except FileNotFoundError as e:
    print(f"Error: {e}. Ensure the file path is correct.")
    exit()

data["Timestamp"] = pd.to_datetime(data["Timestamp"]).dt.floor("s")  # Round to whole seconds

data = data.dropna(subset=["Latitude", "Longitude", "Altitude", "VIN or ID"])

data = data[data["VIN or ID"] != "000000"]

data = data[data["Altitude"] > 700]

data["Latitude"] = data["Latitude"].round(4)
data["Longitude"] = data["Longitude"].round(4)

data['Custom 1'] = data['Custom 1'].astype(str).str.strip().str.lower()

data.rename(columns={"VIN or ID": "VIN_or_ID"}, inplace=True)

def analyze_traffic_conflicts(data, horizontal_threshold=500, vertical_threshold=500, time_window_seconds=10):
    """
    Analyze traffic conflicts using optimized filtering and vectorized calculations.
    """
    horizontal_threshold_miles = horizontal_threshold / 5280

    data["Timestamp_seconds"] = data["Timestamp"].astype(np.int64) // 10**9  # Convert to seconds

    conflicts = []

    data = data.sort_values(by="Timestamp_seconds").reset_index(drop=True)

    for i, row in data.iterrows():
        potential = data[data["Timestamp_seconds"] == row["Timestamp_seconds"]]

        lat_diff = np.abs(potential["Latitude"] - row["Latitude"])
        lon_diff = np.abs(potential["Longitude"] - row["Longitude"])
        bounding_box = lat_diff <= (horizontal_threshold_miles / 69.0)  # Approx. 1 degree = 69 miles
        potential = potential[bounding_box]

        potential = potential[potential["VIN_or_ID"] != row["VIN_or_ID"]]

        potential = potential[
            potential["Custom 1"] != row["Custom 1"]
        ]

        if potential.empty:
            continue

        coords = potential[["Latitude", "Longitude"]].to_numpy()
        distances = cdist([[row["Latitude"], row["Longitude"]]], coords, metric="euclidean")[0]

        vertical_distances = np.abs(row["Altitude"] - potential["Altitude"].to_numpy())

        conflict_indices = np.where(
            (distances <= horizontal_threshold_miles) &
            (vertical_distances <= vertical_threshold)
        )[0]

        for idx in conflict_indices:
            conflict = potential.iloc[idx]
            conflict_lat = (row["Latitude"] + conflict["Latitude"]) / 2
            conflict_lon = (row["Longitude"] + conflict["Longitude"]) / 2

            aircraft_pair = tuple(sorted([row["VIN_or_ID"], conflict["VIN_or_ID"]]))

            conflicts.append({
                "AircraftPair": aircraft_pair,
                "Timestamp1": row["Timestamp"],
                "Aircraft1": row["VIN_or_ID"],
                "Custom1_Aircraft1": row.get("Custom 1", None),
                "Timestamp2": conflict["Timestamp"],
                "Aircraft2": conflict["VIN_or_ID"],
                "Custom1_Aircraft2": conflict.get("Custom 1", None),
                "HorizontalDistance_ft": distances[idx] * 5280,
                "VerticalDistance_ft": vertical_distances[idx],
                "Conflict_Latitude": conflict_lat,
                "Conflict_Longitude": conflict_lon,
            })

    conflicts_df = pd.DataFrame(conflicts)

    if not conflicts_df.empty:
        conflicts_df["TimeGroup"] = (conflicts_df["Timestamp1"].astype(np.int64) // (time_window_seconds * 10**9)) * time_window_seconds

        conflicts_df = conflicts_df.sort_values(["HorizontalDistance_ft", "VerticalDistance_ft"]).groupby(
            ["AircraftPair", "TimeGroup"]
        ).first().reset_index()

    return conflicts_df

conflicts_df = analyze_traffic_conflicts(data, horizontal_threshold=500, vertical_threshold=500, time_window_seconds=10)

create_log_files(conflicts_df, data, log_dir)

if conflicts_df.empty:
    print("No conflicts detected.")
else:
    print(f"Conflicts detected: {len(conflicts_df)}")
    print(conflicts_df.head())

conflicts_df.to_csv(r"D:\traffic_conflicts_filtered_grouped_same_second.csv", index=False)
print("Conflicts saved to D:\\traffic_conflicts_filtered_grouped_same_second.csv")
