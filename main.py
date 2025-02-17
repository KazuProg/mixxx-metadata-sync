import os
import time

import mutagen
from mutagen.id3 import ID3
from tinytag import TinyTag

from mixxxdb.mixxxdb import MixxxDB, Library, TrackLocations, Settings
from audiotags import AudioTags

mixxxdb = MixxxDB()


def main():
    startup_time = int(time.time())
    db_session = mixxxdb.get_session()

    db_synctime = (
        db_session.query(Settings).filter(Settings.name == "sync.timestamp").first()
    )
    if db_synctime is None:
        db_synctime = Settings(name="sync.timestamp", value=0)
        db_session.add(db_synctime)

    tracks = db_session.query(Library).all()
    for track in tracks:
        track_location = (
            db_session.query(TrackLocations)
            .filter(TrackLocations.id == track.location)
            .first()
        )

        if not os.path.exists(track_location.location):
            continue

        audio = mutagen.File(track_location.location)
        id3 = audio.tags

        if type(id3) != ID3:
            print("Warning: ID3 tags not found.")
            continue

        mp3_tags = AudioTags(track_location.location)

        ### Import from mp3
        imported = False

        if (
            mp3_tags.synced_at is not None
            and int(db_synctime.value) <= mp3_tags.synced_at
        ):
            if track.comment != mp3_tags.comment:
                track.comment = mp3_tags.comment
                imported = True

            if mp3_tags.bpm is not None:
                if track.bpm != mp3_tags.bpm:
                    track.bpm = mp3_tags.bpm
                    imported = True

                if mp3_tags.beats is not None and mp3_tags.beats_version is not None:
                    if (
                        track.beats != mp3_tags.beats
                        or track.beats_version != mp3_tags.beats_version
                    ):
                        track.beats = mp3_tags.beats
                        track.beats_version = mp3_tags.beats_version
                        imported = True

                    track.bpm_lock = 1

            if track.title != mp3_tags.title:
                track.title = mp3_tags.title
                imported = True

            if track.artist != mp3_tags.artist:
                track.artist = mp3_tags.artist
                imported = True

            tag = TinyTag.get(track_location.location)

            if track.samplerate == 0:
                track.samplerate = tag.samplerate
                imported = True

            if track.duration == 0:
                track.duration = tag.duration
                imported = True

            if imported:
                print("Import:", track_location.location)

        ### Import from mp3:end

        ### Export to mp3
        exported = False

        if mp3_tags.synced_at is None or mp3_tags.synced_at <= int(db_synctime.value):
            if track.comment != mp3_tags.comment:
                mp3_tags.comment = track.comment
                exported = True

            # BPMロックされていればBPM,Beatが調整済みとみなしmp3へ書き込む
            if track.bpm_lock == 1:
                if track.bpm != mp3_tags.bpm:
                    mp3_tags.bpm = track.bpm
                    exported = True

                if track.beats is not None and track.beats != mp3_tags.beats:
                    mp3_tags.beats = track.beats
                    mp3_tags.beats_version = track.beats_version
                    exported = True

            if exported:
                print("Export:", track_location.location)
                mp3_tags.synced_at = startup_time
                mp3_tags.save()

        ### Export to mp3:end

    db_synctime.value = startup_time
    db_session.commit()


main()
