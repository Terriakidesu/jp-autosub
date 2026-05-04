#!/bin/bash

# Check if batch.txt exists
if [ ! -f "batch.txt" ]; then
    echo "batch.txt not found!"
    exit 1
fi

# Read each line from batch.txt
while IFS= read -r url || [ -n "$url" ]; do
    # Skip empty lines and comments
    [[ -z "$url" || "$url" =~ ^# ]] && continue
    
    echo "-----------------------------------"
    echo "Processing: $url"
    echo "-----------------------------------"
    
    # Run the application
    uv run src/app.py "$url" --hwaccel auto --video-codec h264_qsv
    
    if [ $? -eq 0 ]; then
        echo "Successfully processed: $url"
    else
        echo "Failed to process: $url"
    fi
done < batch.txt

echo "Batch processing complete."
