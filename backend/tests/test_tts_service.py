from pathlib import Path
from uuid import uuid4

from app.services import tts_service
from app.services.tts_service import TextToSpeechService


class FakeTTS:
    is_multi_lingual = True

    def tts_to_file(self, text: str, file_path: str, language: str = "kn") -> None:
        path = Path(file_path)
        path.write_bytes(
            b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
            b"\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00"
        )


def test_audio_generation_creates_wav(monkeypatch):
    audio_id = f"test-{uuid4().hex}.wav"
    path = Path("storage/generated") / audio_id
    path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tts_service, "_load_tts_model", lambda: FakeTTS())
    monkeypatch.setattr(tts_service, "generated_audio_path", lambda suffix=".wav": (audio_id, path))

    audio_id, output_path = TextToSpeechService().synthesize("ನಮಸ್ಕಾರ", "kn")

    assert audio_id.startswith("test-")
    assert output_path.exists()
    assert output_path.stat().st_size > 0
