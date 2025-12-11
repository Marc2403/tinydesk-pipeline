import re
from pathlib import Path

import yt_dlp

from tinydesk_config import FFMPEG_BIN, BASE_DIR


def sanitize_title(title: str) -> str:
    """
    Macht aus einem YouTube-Titel einen halbwegs sauberen Dateinamen/Ordnernamen.
    """
    title = title.strip()
    # ungültige Zeichen ersetzen
    title = re.sub(r'[^0-9A-Za-zäöüÄÖÜß\-\s_]', "_", title)
    # Mehrfach-Leerzeichen zu einem
    title = re.sub(r"\s+", " ", title)
    return title[:80]


def download_best_audio_wav(url: str, base_dir: Path | None = None) -> Path:
    """
    Lädt von YouTube den bestmöglichen Audiostream als WAV herunter
    und gibt den Pfad zur WAV-Datei zurück.
    """
    if base_dir is None:
        base_dir = BASE_DIR

    print("\n======================")
    print(f"[DOWNLOAD] URL: {url}")
    print("======================")

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,  # nur dieses Video, keine Mix-Playlist
        "outtmpl": str(base_dir / "%(title)s.%(ext)s"),
        "ffmpeg_location": str(FFMPEG_BIN),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",  # beste Qualität
            }
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    title = info.get("title", "tinydesk")
    sanitized = sanitize_title(title)

    # Kandidaten suchen, die nach dem Download entstanden sind
    candidates = list(base_dir.glob(
        f"{title}*.wav")) + list(base_dir.glob(f"{sanitized}*.wav"))

    if not candidates:
        # Fallback: neueste .wav im Ordner
        wav_files = list(base_dir.glob("*.wav"))
        if not wav_files:
            raise FileNotFoundError("Keine WAV-Datei nach Download gefunden.")
        wav_path = max(wav_files, key=lambda p: p.stat().st_mtime)
    else:
        wav_path = candidates[0]

    print(f"[DOWNLOAD] Fertig: {wav_path.name}")
    return wav_path
