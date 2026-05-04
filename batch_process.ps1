if (-not (Test-Path "batch.txt")) {
    Write-Host "batch.txt not found!" -ForegroundColor Red
    exit 1
}

$urls = Get-Content "batch.txt"
foreach ($url in $urls) {
    if ([string]::IsNullOrWhiteSpace($url) -or $url.Trim().StartsWith("#")) {
        continue
    }

    Write-Host "-----------------------------------"
    Write-Host "Processing: $url"
    Write-Host "-----------------------------------"
    
    uv run src/app.py $url --hwaccel auto --video-codec h264_qsv
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Successfully processed: $url" -ForegroundColor Green
    } else {
        Write-Host "Failed to process: $url" -ForegroundColor Red
    }
}

Write-Host "Batch processing complete."
Read-Host "Press Enter to exit..."
