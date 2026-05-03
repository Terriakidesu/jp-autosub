import re
from pathlib import Path

def sanitize_filename(name: str) -> str:
    r"""
    Replace characters invalid for Windows filenames with underscores.
    Invalid: \ / : * ? " < > | and control characters.
    Also remove trailing dots and spaces.
    """
    # Replace invalid characters
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Replace control characters
    name = ''.join(ch for ch in name if ord(ch) >= 32)
    # Trim trailing dots and spaces
    name = name.rstrip('. ')
    return name

def setup_directories(download_dir: Path, output_dir: Path, temp_dir: Path):
    download_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(exist_ok=True)
