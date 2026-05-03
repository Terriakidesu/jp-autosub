import pysrt
import deepl
import sys
from pathlib import Path

def fmt_time(seconds: float) -> str:
    """Formats seconds into SRT timestamp format: HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def merge_segments(segments, min_gap=0.5, max_chars=30, max_duration=5.0):
    """Merges short segments and splits long ones, optimized for Japanese."""
    merged = []
    seg_list = list(segments)
    if not seg_list:
        return merged
    
    current = seg_list[0]
    for next_seg in seg_list[1:]:
        current_text = getattr(current, 'text', '')
        next_text = getattr(next_seg, 'text', '')
        
        # Merge if short and close
        # Use character count instead of word count for Japanese
        if (next_seg.start - current.end < min_gap) and (len(current_text) + len(next_text) < max_chars):
            current.end = next_seg.end
            current.text = (current_text + next_text).strip()
        else:
            merged.append(current)
            current = next_seg
            
    merged.append(current)
    return merged

def save_srt(segments, output_path: Path):
    # segments is a generator; ensure it's iterable
    merged = merge_segments(segments)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(merged, start=1):
            # Handle both segment objects and word objects
            start = getattr(seg, 'start', 0.0)
            end = getattr(seg, 'end', 0.0)
            text = getattr(seg, 'text', '')
            f.write(f"{i}\n{fmt_time(start)} --> {fmt_time(end)}\n{text.strip()}\n\n")
    print(f"✓ Subtitles saved: {output_path.name}")

import re

def split_long_segments(subs, max_words=12):
    """Splits long SRT lines at natural punctuation boundaries."""
    new_subs = pysrt.SubRipFile()
    
    # Regex to split on punctuation while keeping the punctuation
    punctuation_pattern = re.compile(r'([,.!?。，！？])\s*')
    
    for sub in subs:
        words = sub.text.split()
        if len(words) <= max_words:
            new_subs.append(sub)
        else:
            # Try to find natural split points
            parts = punctuation_pattern.split(sub.text)
            # Recombine punctuation with preceding part
            phrases = []
            for i in range(0, len(parts) - 1, 2):
                phrases.append(parts[i] + parts[i+1])
            if len(parts) % 2 != 0:
                phrases.append(parts[-1])
            
            # Filter empty strings
            phrases = [p.strip() for p in phrases if p.strip()]
            
            # If no good punctuation splits, fall back to word-count splitting
            if len(phrases) <= 1:
                # (Existing word-count logic for fallback)
                num_chunks = (len(words) + max_words - 1) // max_words
                phrases = [" ".join(words[i*max_words:(i+1)*max_words]) for i in range(num_chunks)]
            
            # Calculate total duration in milliseconds
            total_duration_ms = sub.end.ordinal - sub.start.ordinal
            
            # Keep track of cumulative time to assign accurate start/end
            cumulative_ms = 0
            
            for i, phrase in enumerate(phrases):
                phrase_words = phrase.split()
                # Weight duration based on word count
                weight = len(phrase_words) / len(words)
                chunk_duration = int(total_duration_ms * weight)
                
                start_time = sub.start + pysrt.SubRipTime(milliseconds=cumulative_ms)
                # Ensure the last chunk ends at the original sub.end
                if i == len(phrases) - 1:
                    end_time = sub.end
                else:
                    end_time = start_time + pysrt.SubRipTime(milliseconds=chunk_duration)
                
                new_sub = pysrt.SubRipItem(
                    index=len(new_subs) + 1,
                    start=start_time,
                    end=end_time,
                    text=phrase
                )
                new_subs.append(new_sub)
                cumulative_ms += chunk_duration
    return new_subs

def resolve_overlaps(subs):
    """Ensures no subtitles overlap by adjusting end times to match the start of the next."""
    for i in range(len(subs) - 1):
        if subs[i].end > subs[i+1].start:
            subs[i].end = subs[i+1].start
    return subs

def translate_srt_with_deepl(japanese_srt_path: Path, api_key: str, video_id: str, target_lang: str, temp_dir: Path, overwrite: bool):
    translated_path = temp_dir / f"{video_id}_subtitles_ja_{target_lang.lower()}.srt"
    if not overwrite and translated_path.exists():
        print(f"✓ English subtitles already exist: {translated_path.name}")
        return translated_path

    print("▶ Translating with DeepL...")
    translator = deepl.Translator(api_key)
    
    # 1. Open and PRE-MERGE segments for better context
    raw_subs = pysrt.open(japanese_srt_path, encoding='utf-8')
    # Use higher thresholds for translation context
    merged_subs = merge_segments(raw_subs, min_gap=0.8, max_words=20, max_duration=6.0)
    
    # Convert to pysrt object
    subs = pysrt.SubRipFile()
    for i, seg in enumerate(merged_subs, start=1):
        subs.append(pysrt.SubRipItem(index=i, start=seg.start, end=seg.end, text=seg.text))

    # 2. Batch Translation
    batch_size = 25
    total = len(subs)
    for i in range(0, total, batch_size):
        batch = subs[i:i+batch_size]
        text_batch = "\n".join([sub.text for sub in batch])
        try:
            translated = translator.translate_text(text_batch, target_lang=target_lang)
            translated_lines = translated.text.split("\n")
            for j, sub in enumerate(batch):
                if j < len(translated_lines):
                    sub.text = translated_lines[j]
        except Exception as e:
            print(f"DeepL API error on batch {i//batch_size + 1}: {e}")
            sys.exit(1)
        print(f"   Translated batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
    
    # 3. Post-process to ensure readability
    final_subs = split_long_segments(subs)
    final_subs.save(translated_path, encoding='utf-8')
    print(f"✓ English subtitles saved: {translated_path.name}")
    return translated_path
