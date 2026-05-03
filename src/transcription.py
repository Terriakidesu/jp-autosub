import whisper_timestamped
from .subtitles import save_srt
from pathlib import Path

def transcribe_japanese(
    audio_wav_path: Path,
    overwrite: bool,
    japanese_srt_path: Path,
    model_size: str = "small",
    beam_size: int = 5,
    vad_filter: bool = False,      # whisper-timestamped ignores this
    word_timestamps: bool = True,  # implicit for this library
):
    if not overwrite and japanese_srt_path.exists():
        print(f"✓ Japanese subtitles already exist: {japanese_srt_path.name}")
        return

    print(f"▶ Transcribing Japanese audio with timestamp alignment (model: {model_size})...")
    model = whisper_timestamped.load_model(model_size, device="cpu")

    # Load audio (already WAV 16kHz mono)
    import soundfile as sf
    audio, sr = sf.read(str(audio_wav_path))
    result = whisper_timestamped.transcribe_timestamped(
        model,
        audio,
        language="ja",
        beam_size=beam_size,
        vad=True,
        detect_disfluencies=True,
        compute_word_confidence=True,
        refine_whisper_precision=0.02,
    )

    # Convert result to aggregated segments
    segments = []
    current_seg = None

    print("▶ Transcription details:")
    # Simple logic to group words: merge if they are very close in time and add up to a natural length
    for seg in result["segments"]:
        for word in seg.get("words", []):
            text = word["text"].replace("[*]", "").strip()
            if not text:
                continue

            # Print word in real-time
            print(f"  {text}", end=" ", flush=True)

            if current_seg and (word["start"] - current_seg.end < 0.5) and (len(current_seg.text) < 20):
                current_seg.end = word["end"]
                current_seg.text += text
            else:
                if current_seg:
                    segments.append(current_seg)
                current_seg = Word(word["start"], word["end"], text)

    print("\n") # New line after transcription
    if current_seg:
        segments.append(current_seg)
    # Print language
    detected_lang = result.get("language", "ja")
    print(f"✓ Transcription complete. Detected language: {detected_lang}")
    print(f"✓ Total segments found: {len(segments)}")

    save_srt(iter(segments), japanese_srt_path)