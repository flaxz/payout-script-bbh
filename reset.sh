#!/bin/bash

rm processed_files.db payments.db temp_payments_file.csv

echo "Databases deleted."

find ./pay -name "*.csv" -type f -delete

echo "CSV files deleted."
