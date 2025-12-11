# tinydesk_rename.py

import os
import re
from pathlib import Path
from typing import List, Tuple

from mutagen.easyid3 import EasyID3
import yt_dlp


def get_setlist_from_youtube(url: str) -> Tuple[str, str, List[str]]:
    """
    Holt Titel, Uploader und SET LIST aus der YouTube-Beschreibung.

    Rückgabe:
      artist (rateweise),
      album_title (z.B. kompletter Videotitel),
      track_titles (Liste der Songs in Reihenfolge)
    """
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    description = info.get("description") or ""
    video_title = info.get("title") or ""
    uploader = info.get("uploader") or ""

    # Artist aus dem Videotitel raten, z.B. "girl in red: Tiny Desk Concert"
    m = re.match(r"(.+?)\s*[:|-]\s*Tiny Desk",
                 video_title, flags=re.IGNORECASE)
    if m:
        artist = m.group(1).strip()
    else:
        # Fallback: Uploader nehmen
        artist = uploader or "Unknown Artist"

    album_title = video_title or "Tiny Desk Concert"

    # SET LIST Block finden
    lines = description.splitlines()
    track_titles: List[str] = []

    # Index der Zeile mit "SET LIST" (case-insensitive)
    start_idx = None
    for i, line in enumerate(lines):
        if "set list" in line.lower():
            start_idx = i
            break

    if start_idx is None:
        print("⚠️  Keine 'SET LIST' in der Videobeschreibung gefunden.")
        return artist, album_title, track_titles

    # Zeilen NACH "SET LIST" durchgehen, bis eine wirklich leere Zeile
    for line in lines[start_idx + 1:]:
        stripped = line.strip()
        if not stripped and track_titles:
            # Leere Zeile nach dem Setlist-Block → fertig
            break
        if not stripped:
            continue

        # Versuche zuerst, in Anführungszeichen zu parsen: "Phantom Pain"
        quoted = re.findall(r'"([^"]+)"', stripped)
        if quoted:
            for q in quoted:
                title = q.strip()
                if title:
                    track_titles.append(title)
            continue

        # Falls keine Anführungszeichen, evtl. "1. Phantom Pain" oder "- Phantom Pain"
        m2 = re.match(r"[-•\d.)\s]*(.+)", stripped)
        if m2:
            title = m2.group(1).strip()
            if title:
                track_titles.append(title)

    return artist, album_title, track_titles


def slugify_filename(text: str) -> str:
    """
    Entfernt unzulässige Zeichen für Windows-Dateinamen.
    """
    text = re.sub(r'[\\/*?:"<>|]', "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def rename_songs_with_setlist(songs_dir: Path, youtube_url: str):
    """
    Benennt alle Dateien 'song_X.mp3' in songs_dir anhand der SET LIST
    der angegebenen YouTube-URL um, setzt außerdem ID3-Tags.
    """
    if not songs_dir.is_dir():
        print(f"❌ Ordner '{songs_dir}' nicht gefunden.")
        return

    print(f"📥 Hole SET LIST von YouTube: {youtube_url}")
    artist, album_title, track_titles = get_setlist_from_youtube(youtube_url)

    print(f"➡️  Artist (geschätzt): {artist}")
    print(f"➡️  Album-Titel: {album_title}")
    print("➡️  Gefundene Songs:")
    for i, t in enumerate(track_titles, start=1):
        print(f"   {i}. {t}")

    # Alle Dateien im Format song_X.mp3 einsammeln
    files = []
    for name in os.listdir(songs_dir):
        lower = name.lower()
        if lower.startswith("song_") and lower.endswith(".mp3"):
            try:
                nummer = int(lower.split("_")[1].split(".")[0])
                files.append((nummer, name))
            except ValueError:
                continue

    if not files:
        print("❌ Keine Dateien im Format 'song_X.mp3' gefunden.")
        return

    files.sort(key=lambda x: x[0])

    if track_titles and len(track_titles) != len(files):
        print(
            f"⚠️  Achtung: SET LIST hat {len(track_titles)} Titel, "
            f"aber es gibt {len(files)} song_X.mp3 Dateien."
        )
        print(
            "   Ich ordne einfach der Reihe nach zu, Überschuss wird 'Unbenannter Track'.")

    for idx, (nummer, filename) in enumerate(files, start=1):
        old_path = songs_dir / filename

        if track_titles and idx <= len(track_titles):
            title = track_titles[idx - 1]
        else:
            title = f"Unbenannter Track {idx}"

        safe_title = slugify_filename(title)
        new_filename = f"{artist} - {safe_title}.mp3"
        new_path = songs_dir / new_filename

        # Falls Datei schon existiert, (2), (3), ... anhängen
        counter = 2
        while new_path.exists():
            new_filename = f"{artist} - {safe_title} ({counter}).mp3"
            new_path = songs_dir / new_filename
            counter += 1

        os.rename(old_path, new_path)
        print(f"✨ Umbenannt: '{filename}'  →  '{new_filename}'")

        # ID3-Tags setzen
        try:
            audio = EasyID3(new_path)
        except Exception:
            audio = EasyID3()

        audio["artist"] = artist
        audio["title"] = title
        audio["album"] = album_title
        audio["tracknumber"] = str(idx)
        audio.save(new_path)
        print(
            f"   Tags gesetzt: Artist='{artist}', Title='{title}', Track={idx}")

    print(
        f"✅ Fertig! Songs im Ordner '{songs_dir}' automatisch benannt und getaggt.")


# Optional: Standalone-Aufruf wie früher
if __name__ == "__main__":
    # Einfacher Testmodus: globaler "songs"-Ordner + eine URL
    SONGS_FOLDER = "songs"
    YOUTUBE_URL = "https://www.youtube.com/watch?v=cXYgdCXkLMc"

    base_dir = Path(__file__).resolve().parent
    songs_dir = base_dir / SONGS_FOLDER

    rename_songs_with_setlist(songs_dir, YOUTUBE_URL)
