# Google Colab Setup for jp-autosub

This notebook configures the `jp-autosub` environment on Google Colab to enable high-accuracy Japanese-to-English subtitle generation using `whisper-timestamped` and DeepL.

## 1. Setup Environment
```python
from google.colab import userdata
import os

# Set these in the "Secrets" tab (key icon) in Colab
GIT_TOKEN = userdata.get('GIT_TOKEN')
DEEPL_API_KEY = userdata.get('DEEPL_API_KEY')

REPO_URL = f"https://{GIT_TOKEN}@github.com/your-username/jp-autosub.git"
os.environ['REPO_URL'] = REPO_URL

!apt-get update && apt-get install -y ffmpeg
!git clone $REPO_URL
%cd jp-autosub
!pip install uv
# Sync project dependencies
!uv sync
# Ensure dependencies are installed in the uv environment
!uv pip install torch torchaudio onnxruntime
```


## 2. Configuration
```python
with open(".env", "w") as f:
    f.write(f"DEEPL_API_KEY={DEEPL_API_KEY}")
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
