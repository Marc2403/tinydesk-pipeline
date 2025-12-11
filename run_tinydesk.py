# run_tinydesk.py

from pathlib import Path

from tinydesk_config import BASE_DIR, OUTPUT_ROOT
from yt_download import download_best_audio_wav, sanitize_title
from tinydesk_split import split_tiny_desk_audio
from tinydesk_rename import rename_songs_with_setlist, get_setlist_from_youtube

# Hier trägst du deine Tiny-Desk-Links ein
YOUTUBE_LINKS = [
    "https://youtu.be/59eBs8iiLU0?si=5QCbU-7J9n_A2tuy"
]


def process_tiny_desk_link(url: str):
    """
    Für einen Link:
      1) SET LIST abfragen → gewünschte Songanzahl bestimmen
      2) Audio als WAV herunterladen
      3) einen Ordner für das Konzert anlegen
      4) Songs dorthin exportieren (mit Setlist-Info)
      5) Songs anhand der SET LIST umbenennen und taggen
    """
    # 1) SET LIST holen, um desired_num_songs zu erfahren
    print(f"[INFO] Hole SET LIST für: {url}")
    artist, album_title, track_titles = get_setlist_from_youtube(url)
    desired_num_songs = len(track_titles) if track_titles else None
    print(f"[INFO] SET LIST hat {desired_num_songs or 0} Titel.")

    # 2) Download
    wav_path = download_best_audio_wav(url, BASE_DIR)

    # 3) Konzert-Ordner
    title = wav_path.stem
    folder_name = sanitize_title(title)
    concert_dir = OUTPUT_ROOT / folder_name

    print(f"[INFO] Verarbeite Konzert: {folder_name}")

    # 4) Splitten, ggf. aggressiver suchen, falls wir zu wenige Songs haben
    split_tiny_desk_audio(
        wav_path,
        concert_dir,
        desired_num_songs=desired_num_songs,
    )

    # 5) Umbenennen nach SET LIST (wie bisher)
    rename_songs_with_setlist(concert_dir, url)


if __name__ == "__main__":
    OUTPUT_ROOT.mkdir(exist_ok=True)

    for link in YOUTUBE_LINKS:
        try:
            process_tiny_desk_link(link)
        except Exception as e:
            print(
                f"[ERROR] Beim Verarbeiten von {link} ist ein Fehler aufgetreten:")
            print(e)
