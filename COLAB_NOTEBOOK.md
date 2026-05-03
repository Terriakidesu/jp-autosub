# Google Colab Setup for jp-autosub

This notebook configures the `jp-autosub` environment on Google Colab to enable high-accuracy Japanese-to-English subtitle generation using `whisper-timestamped` and DeepL.

## 1. Setup Environment
```python
!apt-get update && apt-get install -y ffmpeg
!git clone https://github.com/your-username/jp-autosub.git
%cd jp-autosub
!pip install uv
!uv sync
!uv pip install torchaudio onnxruntime
```

## 2. Configuration
Create a `.env` file for your DeepL API key.
```python
from google.colab import userdata
deepl_key = userdata.get('DEEPL_API_KEY')
with open(".env", "w") as f:
    f.write(f"DEEPL_API_KEY={deepl_key}")
```

## 3. Run Transcription
Execute the following to transcribe and translate a video URL.
```python
VIDEO_URL = "YOUR_YOUTUBE_URL_HERE"
!uv run src/app.py "$VIDEO_URL" -o --hwaccel auto --video-codec libx264
```

## 4. Download Results
```python
from google.colab import files
import glob

# Download the generated mp4
files.download(glob.glob("output/*.mp4")[0])
```
