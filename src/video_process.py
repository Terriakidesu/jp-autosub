import subprocess
import shutil
import sys
import re
from pathlib import Path
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

def burn_subtitles(video_path: str, srt_path: str, output_path: Path, overwrite: bool, hwaccel: str = None, video_codec: str = "libx264"):
    output_path = Path(output_path)
    if not overwrite and output_path.exists():
        print(f"✓ Final video already exists: {output_path}")
        return
    print("▶ Burning subtitles into video (ffmpeg)...")
    video_dir = Path(video_path).parent
    srt_name = Path(srt_path).name
    temp_srt = video_dir / srt_name
    shutil.copy2(srt_path, temp_srt)

    # Need duration to track progress
    duration = get_video_duration(video_path)
    
    output_abs = str(output_path.resolve())
    cmd = ["ffmpeg"]
    if hwaccel:
        cmd.extend(["-hwaccel", hwaccel])
    cmd.extend([
        "-i", Path(video_path).name,
        "-vf", f"subtitles={srt_name}",
        "-c:a", "copy",
        "-c:v", video_codec,
        "-y", output_abs
    ])
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Encoding...", total=duration)
        
        process = subprocess.Popen(
            cmd,
            cwd=video_dir,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        for line in process.stderr:
            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}.\d{2})", line)
            if time_match:
                time_str = time_match.group(1)
                h, m, s = map(float, time_str.split(':'))
                seconds = h * 3600 + m * 60 + s
                progress.update(task, completed=seconds)
    
    process.wait()
    temp_srt.unlink(missing_ok=True)

    if process.returncode != 0:
        print("FFmpeg error.")
        sys.exit(1)
    print(f"✓ Hard‑subbed video saved: {output_path.name}")

def get_video_duration(video_path: str):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0
