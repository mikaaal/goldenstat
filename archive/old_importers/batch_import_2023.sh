#!/bin/bash

# Batch import script for remaining 2023/2024 season files
# Created: 2025-09-19

echo "🎯 Starting batch import of 13 remaining 2023/2024 divisions..."
echo "⏰ Started at: $(date)"
echo ""

# List of remaining files to import
files=(
    "t_x0iz_3791_match_urls.txt"
    "t_jaxh_8760_match_urls.txt" 
    "t_gIVw_6888_match_urls.txt"
    "t_fPTj_9933_match_urls.txt"
    "t_e8pV_5661_match_urls.txt"
    "t_aFYd_4203_match_urls.txt"
    "t_a9wN_5712_match_urls.txt"
    "t_YzuS_8311_match_urls.txt"
    "t_T7jk_7930_match_urls.txt"
    "t_Qgj3_9223_match_urls.txt"
    "t_HNTb_3455_match_urls.txt"
    "t_EyOG_1906_match_urls.txt"
    "t_B4Ye_1284_match_urls.txt"
)

total_files=${#files[@]}
completed=0
total_success=0
total_failed=0

echo "📋 Processing $total_files divisions..."
echo ""

for file in "${files[@]}"; do
    completed=$((completed + 1))
    
    # Extract division ID from filename
    division_id=$(echo "$file" | sed 's/_match_urls\.txt$//')
    
    echo "📊 [$completed/$total_files] Processing division: $division_id"
    echo "📂 File: $file"
    echo "⏰ $(date)"
    echo ""
    
    # Run the import
    python3 new_season_importer.py "$division_id" "$file" "2023/2024"
    exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "✅ Division $division_id completed successfully"
        total_success=$((total_success + 1))
    else
        echo "❌ Division $division_id failed with exit code $exit_code"
        total_failed=$((total_failed + 1))
    fi
    
    echo ""
    echo "📈 Progress: $completed/$total_files completed"
    echo "   ✅ Successful: $total_success"
    echo "   ❌ Failed: $total_failed"
    echo ""
    echo "===========================================" 
    echo ""
    
    # Small delay to be respectful to the server
    sleep 2
done

echo "🎉 Batch import completed!"
echo "⏰ Finished at: $(date)"
echo ""
echo "📊 Final Results:"
echo "   📁 Total divisions processed: $total_files"
echo "   ✅ Successful imports: $total_success"
echo "   ❌ Failed imports: $total_failed"
echo ""

if [ $total_failed -eq 0 ]; then
    echo "🎯 All divisions imported successfully! 🎉"
else
    echo "⚠️  Some divisions failed. Check the output above for details."
fi