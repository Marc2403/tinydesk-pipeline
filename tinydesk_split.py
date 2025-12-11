# tinydesk_split.py

from pathlib import Path

from inaSpeechSegmenter import Segmenter
from pydub import AudioSegment

from tinydesk_config import (
    MIN_SONG_LENGTH_SECONDS,
    MAX_GAP_WITHIN_SONG_SECONDS,
)


def build_song_blocks(
    segments,
    min_song_len: float = MIN_SONG_LENGTH_SECONDS,
    max_gap: float = MAX_GAP_WITHIN_SONG_SECONDS,
):
    """
    Nimmt die Segmente (label, start, end) vom Segmenter und baut zusammenhängende
    'music'-Blöcke, die wir als einzelne Songs speichern.

    Mehrere music-Segmente, die nicht zu weit auseinander liegen, werden gemerged.
    """
    current_start = None
    current_end = None
    song_blocks: list[tuple[float, float]] = []

    for label, start, end in segments:
        if label != "music":
            continue

        if current_start is None:
            # Start eines neuen Songs
            current_start = start
            current_end = end
        else:
            gap = start - current_end
            if gap <= max_gap:
                # noch der gleiche Song (z.B. kurze Ansage vom Künstler)
                current_end = end
            else:
                # alter Song zu Ende, neuen Song beginnen
                duration = current_end - current_start
                if duration >= min_song_len:
                    song_blocks.append((current_start, current_end))
                current_start = start
                current_end = end

    # letzten Block nicht vergessen
    if current_start is not None:
        duration = current_end - current_start
        if duration >= min_song_len:
            song_blocks.append((current_start, current_end))

    return song_blocks


def refine_song_blocks_with_params(
    segments,
    desired_num_songs: int,
    min_song_len_start: float,
    max_gap_start: float,
    min_song_len_min: float = 20.0,
    max_gap_min: float = 2.0,
    steps: int = 4,
):
    """
    Versucht, durch schrittweises Anpassen von min_song_len und max_gap
    mehr Song-Blöcke zu erzeugen, bis wir mindestens desired_num_songs haben
    oder die Grenzen erreicht sind.

    Idee:
      - Start mit deinen Standardwerten (z.B. 45 s / 12 s)
      - In mehreren Schritten:
          * min_song_len nach unten
          * max_gap nach unten
      - Ziel: kleinere Pausen nicht mehr zusammenkleben und kürzere Songs zulassen.
    """
    # Start: Standard-Blöcke
    best_blocks = build_song_blocks(
        segments,
        min_song_len=min_song_len_start,
        max_gap=max_gap_start,
    )

    if len(best_blocks) >= desired_num_songs:
        return best_blocks

    for i in range(1, steps + 1):
        factor = i / steps

        # min_song_len linear Richtung min_song_len_min bewegen
        min_len = max(
            min_song_len_start - factor *
            (min_song_len_start - min_song_len_min),
            min_song_len_min,
        )
        # max_gap linear Richtung max_gap_min bewegen
        max_gap = max(
            max_gap_start - factor * (max_gap_start - max_gap_min),
            max_gap_min,
        )

        print(
            f"[REFINE] Versuch {i}/{steps}: "
            f"min_len={min_len:.1f}s, max_gap={max_gap:.1f}s"
        )

        blocks = build_song_blocks(
            segments,
            min_song_len=min_len,
            max_gap=max_gap,
        )
        print(f"[REFINE] -> {len(blocks)} Blöcke gefunden.")

        best_blocks = blocks

        if len(blocks) >= desired_num_songs:
            print("[REFINE] Zielanzahl erreicht oder überschritten.")
            break

    return best_blocks


def split_tiny_desk_audio(
    input_path: Path,
    output_dir: Path,
    desired_num_songs: int | None = None,
):
    """
    Nimmt eine WAV-Datei eines Tiny Desk Konzerts,
    segmentiert Musik-Bereiche und speichert sie als einzelne MP3-Songs.

    Wenn desired_num_songs gesetzt ist (z.B. Anzahl Titel aus SET LIST)
    und wir zu wenige Song-Blöcke finden, wird versucht, durch
    aggressivere Parameter mehr Blöcke zu erzeugen.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[SEGMENT] Lade Segmenter...")
    seg = Segmenter()

    print(f"[SEGMENT] Segmentiere Audio: {input_path.name}")
    segments = seg(str(input_path))

    print("[SEGMENT] Baue Song-Blöcke (Standard-Parameter)...")
    song_blocks = build_song_blocks(segments)

    if not song_blocks:
        print("[WARN] Keine Songblöcke gefunden.")
        return

    original_count = len(song_blocks)
    print(f"[SEGMENT] Standard: {original_count} Song(s) gefunden.")

    # Falls wir eine Zielanzahl aus der SET LIST kennen und zu wenig Blöcke haben:
    if desired_num_songs is not None and original_count < desired_num_songs:
        print(
            f"[INFO] Setlist hat {desired_num_songs} Songs, "
            f"Segmenter nur {original_count}. "
            f"Versuche feinere Parameter..."
        )
        song_blocks = refine_song_blocks_with_params(
            segments,
            desired_num_songs=desired_num_songs,
            min_song_len_start=MIN_SONG_LENGTH_SECONDS,
            max_gap_start=MAX_GAP_WITHIN_SONG_SECONDS,
        )
        print(
            f"[INFO] Nach Refinement: {len(song_blocks)} Song-Blöcke "
            f"(Ziel aus Setlist: {desired_num_songs})"
        )

    print(f"[SEGMENT] Lade komplettes Audio...")
    audio = AudioSegment.from_file(str(input_path))

    for idx, (start, end) in enumerate(song_blocks, start=1):
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        clip = audio[start_ms:end_ms]

        filename = f"song_{idx:02d}.mp3"
        out_path = output_dir / filename

        print(
            f"[EXPORT] {filename}: {start:.1f}s – {end:.1f}s "
            f"(Dauer: {end - start:.1f}s)"
        )
        clip.export(out_path, format="mp3", bitrate="320k")

    print(f"[FERTIG] Songs gespeichert in: {output_dir.resolve()}")
