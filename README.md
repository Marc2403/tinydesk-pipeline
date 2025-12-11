# Tiny Desk Audio Pipeline

An automated Python pipeline for downloading, segmenting, and renaming  
**NPR Tiny Desk Concerts**.  

The system pulls high-quality audio from YouTube, detects individual songs  
(even for concerts with almost no pauses), and renames MP3 files using the  
**SET LIST** found in the video description.

---

## Features

### 1. YouTube Audio Download
- Downloads the best available audio stream using `yt_dlp`.
- Automatically converts to **WAV** via FFmpeg.
- Ensures maximum possible audio quality.

### 2. Automatic Song Segmentation
- Uses `inaSpeechSegmenter` to identify music segments.
- Merges adjacent segments and splits songs based on pause detection.
- If too few songs are detected:
  → multiple refinement passes adjust thresholds  
  (smaller gaps, shorter minimum song length).

### 3. SET LIST–Based Renaming
- Extracts from the YouTube description:
  - Artist name  
  - Video title  
  - Song list (SET LIST)
- Renames all `song_X.mp3` → `Artist - TrackName.mp3`
- Automatically writes ID3 tags:
  - Artist  
  - Title  
  - Album  
  - Track number

### 4. Output Structure

tinydesk-pipeline/
│
├── songs/
│ └── {ConcertTitle}/
│ ├── Artist - Song 1.mp3
│ ├── Artist - Song 2.mp3
│ └── ...
│
├── run_tinydesk.py
├── tinydesk_config.py
├── tinydesk_split.py
├── tinydesk_rename.py
├── yt_download.py
└── requirements.txt


---

## Installation

### 1. Clone the repository

git clone https://github.com/Marc2403/tinydesk-pipeline.git
cd tinydesk-pipeline

### 2. Create a virtual environment

python -m venv .venv
.\.venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Configure FFmpeg

Edit tinydesk_config.py to point to your FFmpeg installation:
FFMPEG_BIN = Path(r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe")

## Usage

### 1. Add your Tiny Desk YouTube links in run_tinydesk.py:

YOUTUBE_LINKS = [
    "https://youtu.be/59eBs8iiLU0?si=5QCbU-7J9n_A2tuy"
]

### 2. Run the pipeline:

python run_tinydesk.py

### 3. Find the processed songs in:

songs/{ConcertTitle}/

## Requirements

Python 3.10+
FFmpeg
yt_dlp
pydub
mutagen
inaSpeechSegmenter (+ PyTorch dependency)
numpy
All dependencies are listed in requirements.txt.

