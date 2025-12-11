import os
from pathlib import Path

# Basis-Ordner des Projekts (der Ordner, wo dieses File liegt)
BASE_DIR = Path(__file__).resolve().parent

# Pfad zu deiner ffmpeg.exe (so wie du ihn angelegt hast)
FFMPEG_BIN = Path(r"C:\ffmpeg\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe")

# ffmpeg-Ordner an PATH anhängen, damit pydub / inaSpeechSegmenter ihn finden
os.environ["PATH"] = str(FFMPEG_BIN.parent) + \
    os.pathsep + os.environ.get("PATH", "")

# Ordner, in den die gesplitteten Songs kommen
OUTPUT_ROOT = BASE_DIR / "songs"

# Segmentier-Parameter
# mindestens 45 Sekunden, damit wir keinen Quatsch als Song speichern
MIN_SONG_LENGTH_SECONDS = 45
# bis zu 12 Sekunden Sprechpause innerhalb eines Songs zusammenfassen
MAX_GAP_WITHIN_SONG_SECONDS = 12
