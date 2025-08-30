import csv
import re
from datetime import datetime, timedelta
import os
import json

def sanitize_path(file_path):
    """Remove surrounding quotation marks if present."""
    return file_path.strip('"')

def extract_keys_from_auditdata(audit_data):
    """Dynamically extract key-value pairs from AuditData."""
    key_value_pairs = {}
    # Use regex to find all key-value pairs in the format "key":"value"
    matches = re.findall(r'"([^"]+)":"([^"]+)"', audit_data)
    for key, value in matches:
        key_value_pairs[key] = value
    return key_value_pairs

def process_csv(input_file, output_file=None):
    # Sanitize input file path
    input_file = sanitize_path(input_file)
    
    # Generate output file name if not provided
    if not output_file:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_processed.csv"

    with open(input_file, mode='r', newline='', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Determine all dynamic columns from AuditData
        dynamic_columns = set()
        for row in reader:
            audit_data = row.get("AuditData", "")
            dynamic_columns.update(extract_keys_from_auditdata(audit_data).keys())
        infile.seek(0)  # Reset file pointer to the beginning after reading

        # Finalize column order
        static_columns = ['CreationDate', 'Date', 'Time', 'UserId', 'Operation']
        fieldnames = static_columns + list(dynamic_columns - set(static_columns))
        writer = csv.DictWriter(open(output_file, mode='w', newline='', encoding='utf-8'), fieldnames=fieldnames)
        writer.writeheader()

        # Process rows
        next(reader)  # Skip header row
        for row in reader:
            # Process CreationDate
            creation_date_utc = row.get("CreationDate", "")
            if creation_date_utc:
                utc_datetime = datetime.strptime(creation_date_utc[:19], "%Y-%m-%dT%H:%M:%S")
                adjusted_datetime = utc_datetime + timedelta(hours=10)

                local_date = adjusted_datetime.strftime("%d-%m-%Y")
                local_time = adjusted_datetime.strftime("%H:%M:%S")

                if adjusted_datetime.hour >= 24:
                    adjusted_datetime += timedelta(days=1)
                    local_date = adjusted_datetime.strftime("%d-%m-%Y")
                    local_time = (adjusted_datetime - timedelta(hours=24)).strftime("%H:%M:%S")

                row["Date"] = local_date
                row["Time"] = local_time

            # Extract dynamic keys from AuditData
            audit_data = row.get("AuditData", "")
            dynamic_values = extract_keys_from_auditdata(audit_data)
            row.update(dynamic_values)

            # Remove unnecessary columns
            for col in ["AuditData", "AssociatedAdminUnits", "AssociatedAdminUnitsNames"]:
                row.pop(col, None)

            # Write row
            ordered_row = {field: row.get(field, "") for field in fieldnames}
            writer.writerow(ordered_row)

# Prompt for input file path and sanitize it
input_file = input("Enter the path to the input CSV file: ")
output_file = None  # Leave output_file as None to automatically create a new CSV

# Run the function with user-specified paths
process_csv(input_file, output_file)
