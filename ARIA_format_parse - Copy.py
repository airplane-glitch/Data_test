import xml.etree.ElementTree as ET
import csv
import os

input_file = r"D:\jumpstart-latest\log\messages.log" 
output_file = "ARIA_flight_data.csv"

def parse_aria_format(input_file, output_file):

    data = []

    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            try:
                if line.strip(): 
                    root = ET.fromstring(line)
                    for record in root.findall(".//record"):
                        track = record.find(".//track")
                        flight_plan = record.find(".//flightPlan")

                        primary_partition = "USA"
                        secondary_partition = "Florida" 
                        timestamp = track.find("mrtTime").text if track is not None and track.find("mrtTime") is not None else ""
                        vin_or_id = track.find("acAddress").text if track is not None and track.find("acAddress") is not None else ""
                        latitude = track.find("lat").text if track is not None and track.find("lat") is not None else ""
                        longitude = track.find("lon").text if track is not None and track.find("lon") is not None else ""
                        altitude = track.find("reportedAltitude").text if track is not None and track.find("reportedAltitude") is not None else ""
                        custom_1 = flight_plan.find("acid").text if flight_plan is not None and flight_plan.find("acid") is not None else ""  # Aircraft ID
                        custom_2 = flight_plan.find("acType").text if flight_plan is not None and flight_plan.find("acType") is not None else ""

                        data.append([
                            primary_partition,
                            secondary_partition,
                            timestamp,
                            vin_or_id,
                            latitude,
                            longitude,
                            altitude,
                            custom_1,
                            custom_2,
                        ])
            except ET.ParseError:
                print("Skipping invalid XML line.")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        csv_writer = csv.writer(csvfile)

        csv_writer.writerow([
            "Primary Partition",
            "Secondary Partition",
            "Timestamp",
            "VIN or ID",
            "Latitude",
            "Longitude",
            "Altitude",
            "Custom 1",
            "Custom 2"
        ])

        csv_writer.writerows(data)

    print(f"ARIA-formatted data has been saved to {output_file}")

parse_aria_format(input_file, output_file)
