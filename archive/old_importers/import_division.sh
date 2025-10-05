#!/bin/bash

# Import Division Script for GoldenStat
# Usage: ./import_division.sh <division_id>

if [ $# -eq 0 ]; then
    echo "Usage: $0 <division_id>"
    echo "Example: $0 t_jM8s_0341"
    exit 1
fi

DIVISION_ID=$1
URL_FILE="${DIVISION_ID}_match_urls.txt"

echo "🎯 Starting import process for division: $DIVISION_ID"
echo "=" $(printf '=%.0s' {1..50})

# Step 1: Generate match URLs if file doesn't exist or is older than 1 day
if [ ! -f "$URL_FILE" ] || [ $(find "$URL_FILE" -mtime +1 -print) ]; then
    echo "📋 Step 1: Generating match URLs..."
    python3 generate_match_urls.py "$DIVISION_ID"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to generate URLs"
        exit 1
    fi
else
    echo "📂 Using existing URL file: $URL_FILE"
fi

echo ""

# Step 2: Import matches using the URL file
echo "📥 Step 2: Importing matches..."
python3 new_season_importer.py "$DIVISION_ID" "$URL_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Import process completed successfully!"
else
    echo ""
    echo "❌ Import process failed!"
    exit 1
fi