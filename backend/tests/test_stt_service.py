from app.core.config import settings
from app.services import stt_service
from app.services.stt_service import SpeechToTextService


def test_transcribe_forces_configured_language(monkeypatch):
    audio_path = settings.upload_dir / "unit-stt-input.wav"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"RIFF....WAVE")
    captured = {}

    class FakeSegment:
        text = "nanu school ge hogide"
        avg_logprob = -0.1
        no_speech_prob = 0.02
        compression_ratio = 1.0
        words = []

    class FakeInfo:
        language = "kn"

    class FakeModel:
        def transcribe(self, path, **kwargs):
            captured["path"] = path
            captured["kwargs"] = kwargs
            return [FakeSegment()], FakeInfo()

    monkeypatch.setattr(stt_service, "_load_whisper_model", lambda: FakeModel())

    transcript, language = SpeechToTextService().transcribe(audio_path)

    assert transcript == "nanu school ge hogide"
    assert language == "kn"
    assert captured["kwargs"]["language"] == "kn"
    assert captured["kwargs"]["vad_filter"] is True
    assert captured["kwargs"]["condition_on_previous_text"] is False
    assert captured["kwargs"]["word_timestamps"] is True


def test_transcribe_with_metadata_returns_confidence_words(monkeypatch):
    audio_path = settings.upload_dir / "unit-stt-input.wav"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"RIFF....WAVE")

    class FakeWord:
        word = "ಮಟ್ಕೆ"
        start = 0.0
        end = 0.4
        probability = 0.22

    class FakeSegment:
        text = "ಮಟ್ಕೆ"
        avg_logprob = -0.4
        no_speech_prob = 0.05
        compression_ratio = 1.0
        words = [FakeWord()]

    class FakeInfo:
        language = "kn"

    class FakeModel:
        def transcribe(self, path, **kwargs):
            return [FakeSegment()], FakeInfo()

    monkeypatch.setattr(stt_service, "_load_whisper_model", lambda: FakeModel())

    result = SpeechToTextService().transcribe_with_metadata(audio_path)

    assert result.transcript == "ಮಟ್ಕೆ"
    assert result.words[0]["word"] == "ಮಟ್ಕೆ"
    assert result.words[0]["probability"] == 0.22
    assert result.uncertain_words == [{"word": "ಮಟ್ಕೆ", "confidence": 0.22, "risk": "VERY_LOW"}]
