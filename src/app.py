
import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to sys.path so 'src' package can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils import setup_directories, sanitize_filename
from src.video import get_video_info, download_video, extract_audio, video_already_downloaded
from src.transcription import transcribe_japanese
from src.subtitles import translate_srt_with_deepl
from src.video_process import burn_subtitles

load_dotenv()

# Default directories
DOWNLOAD_DIR = Path("downloads")
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
DEEPL_TARGET_LANG = "EN-US"

def main():
    parser = argparse.ArgumentParser(description="Japanese to English video auto-subtitler.")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("-s", "--skip-download", action="store_true", help="Skip video download (use existing file)")
    parser.add_argument("-m", "--model", default="small", help="Whisper model size (e.g., tiny, base, small, medium, large-v3)")
    parser.add_argument("-b", "--beam-size", type=int, default=5, help="Beam size for transcription (higher = slower but more accurate, default 5)")
    parser.add_argument("-v", "--vad", action="store_true", help="Enable VAD filter (Voice Activity Detection) for tighter timestamps")
    parser.add_argument("--hwaccel", help="Hardware acceleration for ffmpeg (e.g., cuda, dxva2, qsv, vaapi)")
    parser.add_argument("--video-codec", default="libx264", help="Video encoder codec (e.g., libx264, h264_nvenc, h264_qsv)")
    parser.add_argument("--no-word-timestamps", action="store_true", help="Disable word-level timestamps (may produce fewer segments)")

    args = parser.parse_args()

    setup_directories(DOWNLOAD_DIR, OUTPUT_DIR, TEMP_DIR)

    if not DEEPL_API_KEY:
        print("ERROR: DeepL API key not found. Please create a .env file with DEEPL_API_KEY=your_key")
        sys.exit(1)

    # Fetch metadata
    info = get_video_info(args.url)
    if not info:
        sys.exit(1)
    video_id = info['id']
    raw_title = info['title']
    safe_title = sanitize_filename(raw_title)

    print(f"Video: {raw_title} ({video_id})")

    output_video = OUTPUT_DIR / f"{safe_title}_hardsub_en.mp4"
    if not args.overwrite and output_video.exists():
        print(f"✓ Final video already exists: {output_video}")
        print("   Use --overwrite to regenerate.")
        sys.exit(0)

    # Download or skip
    if args.skip_download:
        video_path = video_already_downloaded(DOWNLOAD_DIR, raw_title, video_id)
        if not video_path:
            print("ERROR: --skip-download used, but no existing video found.")
            sys.exit(1)
        print(f"✓ Using existing video: {video_path}")
    else:
        video_path = download_video(args.url, raw_title, video_id, DOWNLOAD_DIR, args.overwrite)

    # Extract audio
    wav_audio = TEMP_DIR / f"{video_id}_audio.wav"
    extract_audio(video_path, wav_audio, args.overwrite)

    # Transcribe Japanese (with VAD and word timestamps)
    japanese_srt = TEMP_DIR / f"{video_id}_subtitles_ja.srt"
    transcribe_japanese(
        audio_wav_path=wav_audio,
        overwrite=args.overwrite,
        japanese_srt_path=japanese_srt,
        model_size=args.model,
        beam_size=args.beam_size,
        vad_filter=args.vad,
        word_timestamps=not args.no_word_timestamps,   # enabled by default
    )

    # Translate to English via DeepL
    english_srt = translate_srt_with_deepl(
        japanese_srt_path=japanese_srt,
        api_key=DEEPL_API_KEY,
        video_id=video_id,
        target_lang=DEEPL_TARGET_LANG,
        temp_dir=TEMP_DIR,
        overwrite=args.overwrite
    )

    # Burn subtitles into video
    burn_subtitles(
        video_path=video_path,
        srt_path=str(english_srt),
        output_path=output_video,
        overwrite=args.overwrite,
        hwaccel=args.hwaccel,
        video_codec=args.video_codec
    )

    print("\n✅ All done!")
    print(f"   Final video: {output_video}")

if __name__ == "__main__":
    main()