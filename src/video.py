import subprocess
import json
import sys
from pathlib import Path
from .utils import sanitize_filename

def get_video_info(youtube_url):
    cmd = ["yt-dlp", "--cookies", "cookies.txt", "--dump-json", youtube_url]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("Error fetching video info:")
        try:
            err = result.stderr.decode('utf-8')
        except UnicodeDecodeError:
            err = result.stderr.decode('latin-1')
        print(err)
        return None
    try:
        return json.loads(result.stdout.decode('utf-8'))
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return None

def video_already_downloaded(download_dir: Path, title: str, video_id: str = None):
    # Candidates: raw title, sanitized title, and the video_id itself (if given)
    candidates = [title, sanitize_filename(title)]
    if video_id:
        candidates.append(video_id)
        
    for ext in ['.webm', '.mp4', '.mkv']:
        for candidate in candidates:
            file_path = download_dir / f"{candidate}{ext}"
            if file_path.exists():
                return str(file_path)
        # If video_id is provided, also look for files that start with video_id
        if video_id:
            matches = list(download_dir.glob(f"{video_id}_*{ext}"))
            if matches:
                return str(matches[0])
    return None

def download_video(youtube_url: str, title: str, video_id: str, download_dir: Path, overwrite: bool):
    # Pass video_id to the check function
    existing = video_already_downloaded(download_dir, title, video_id)
    if existing and not overwrite:
        print(f"✓ Video already exists: {existing}")
        return existing
    elif existing and overwrite:
        Path(existing).unlink()
        print(f"   Removed existing video: {existing}")

    # Output template: ID prepended to avoid filename clashes and to make ID‑based searching easy
    output_template = str(download_dir / f"[{video_id}]_%(title)s.%(ext)s")
    # Or using the placeholder: "%(id)s" is safer, but we already have video_id
    # But to be dynamic, we could use "%(id)s" inside the template.
    # However, using the known video_id is fine.
    cmd = ["yt-dlp", "--cookies", "cookies.txt", youtube_url, "-o", output_template]
    print(f"▶ Downloading video...")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("yt-dlp error:")
        try:
            err = result.stderr.decode('utf-8')
        except UnicodeDecodeError:
            err = result.stderr.decode('latin-1')
        print(err)
        sys.exit(1)

    # Find the downloaded file (the newest video file in download_dir)
    video_extensions = {'.webm', '.mp4', '.mkv'}
    files = [f for f in download_dir.iterdir() if f.suffix.lower() in video_extensions]
    if not files:
        print("No video file found after download.")
        sys.exit(1)
    video_path = str(max(files, key=lambda f: f.stat().st_ctime))
    print(f"✓ Video downloaded: {Path(video_path).name}")
    return video_path

def extract_audio(video_path: str, output_wav_path: Path, overwrite: bool):
    if not overwrite and output_wav_path.exists():
        print(f"✓ Audio already extracted: {output_wav_path}")
        return
    print(f"▶ Extracting audio to WAV...")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        "-y", str(output_wav_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        print("FFmpeg audio extraction error:")
        try:
            err = result.stderr.decode('utf-8')
        except UnicodeDecodeError:
            err = result.stderr.decode('latin-1')
        print(err)
        sys.exit(1)
    print(f"✓ Audio extracted: {output_wav_path}")