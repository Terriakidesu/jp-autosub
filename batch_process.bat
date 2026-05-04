@echo off
setlocal enabledelayedexpansion

if not exist "batch.txt" (
    echo batch.txt not found!
    exit /b 1
)

for /f "usebackq tokens=* delims=" %%A in ("batch.txt") do (
    set "url=%%A"
    
    :: Skip empty lines
    if not "!url!"=="" (
        :: Skip lines starting with #
        set "firstchar=!url:~0,1!"
        if not "!firstchar!"=="#" (
            echo -----------------------------------
            echo Processing: !url!
            echo -----------------------------------
            
            call uv run src/app.py "!url!" --hwaccel auto --video-codec h264_qsv
            
            if !errorlevel! equ 0 (
                echo Successfully processed: !url!
            ) else (
                echo Failed to process: !url!
            )
        )
    )
)

echo Batch processing complete.
pause
