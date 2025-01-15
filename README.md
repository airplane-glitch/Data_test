# Rought draft for recordkeeping

Current flow:

1. Obtained xml data from SWIM portal.
2. Output: log folder
3. Parsed data with "ARIA_format_parse.py"
4. Output: ARIA_flight_data.csv
5. Traffic conflict detection / data validation with "opti_traffic_test_logs_final.py"
6. Output: "Conflict_logs_na" - Appear to be false positives
7. Final validation: Examine individual logs and confirm validity with Symphony OpsVue 2020 - Unable to replicate events.

