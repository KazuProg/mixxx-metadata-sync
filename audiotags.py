import base64

import mutagen
from mutagen.id3 import ID3, TXXX, TBPM, COMM, TOPE


class AudioTags:
    def __init__(self, filename):
        self.filename = filename
        self.tags = ID3(filename)

    @property
    def artist(self):
        return self.tags.get("TPE1", [None])[0]

    @property
    def title(self):
        return self.tags.get("TIT2", [None])[0]

    @property
    def bpm(self):
        return float(self.tags.get("TBPM", [0])[0]) if "TBPM" in self.tags else None

    @bpm.setter
    def bpm(self, value):
        self.tags.add(TBPM(encoding=3, text=str(value)))

    @property
    def comment(self):
        tag = self.tags.getall("COMM")
        return tag[0].text[0] if tag else None

    @comment.setter
    def comment(self, comment):
        self.tags.delall("COMM")
        if comment is not None:
            self.tags.add(COMM(encoding=3, text=comment))

    @property
    def beats(self):
        beats = self.tags.get("TXXX:Mixxx_Beats", [None])[0]
        if beats is not None:
            beats = base64.b64decode(beats)
        return beats

    @beats.setter
    def beats(self, value):
        encoded = base64.b64encode(value).decode("utf-8")
        self.tags.add(TXXX(desc="Mixxx_Beats", text=encoded))

    @property
    def beats_version(self):
        return self.tags.get("TXXX:Mixxx_BeatsVer", [None])[0]

    @beats_version.setter
    def beats_version(self, value):
        self.tags.add(TXXX(desc="Mixxx_BeatsVer", text=value))

    @property
    def synced_at(self):
        return (
            int(self.tags.get("TXXX:Mixxx_SyncedAt", [0])[0])
            if "TXXX:Mixxx_SyncedAt" in self.tags
            else None
        )

    @synced_at.setter
    def synced_at(self, value):
        self.tags.add(TXXX(desc="Mixxx_SyncedAt", text=str(value)))

    def save(self):
        self.tags.save()
