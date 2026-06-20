from app.services.audio_enhancement_service import AudioEnhancementService
from app.core.config import settings


def test_audio_enhancement_returns_original_when_ffmpeg_is_missing(monkeypatch):
    audio_path = settings.upload_dir / "unit-enhancement-input.wav"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"RIFF....WAVE")
    monkeypatch.setattr("app.services.audio_enhancement_service.shutil.which", lambda _: None)

    assert AudioEnhancementService().enhance(audio_path) == audio_path


def test_audio_enhancement_invokes_ffmpeg(monkeypatch):
    audio_path = settings.upload_dir / "unit-enhancement-input.wav"
    output_path = settings.upload_dir / "unit-enhancement-output.wav"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    audio_path.write_bytes(b"RIFF....WAVE")
    captured = {}

    class FakeResult:
        returncode = 0
        stderr = ""

    def fake_run(command, capture_output, text, check):
        captured["command"] = command
        output_path.write_bytes(b"RIFF....WAVEclean")
        return FakeResult()

    monkeypatch.setattr("app.services.audio_enhancement_service.shutil.which", lambda _: "ffmpeg")
    monkeypatch.setattr("app.services.audio_enhancement_service.enhanced_audio_path", lambda: ("x", output_path))
    monkeypatch.setattr("app.services.audio_enhancement_service.subprocess.run", fake_run)

    assert AudioEnhancementService().enhance(audio_path) == output_path
    assert captured["command"][:5] == ["ffmpeg", "-y", "-i", str(audio_path), "-ac"]
    assert "highpass=f=80,lowpass=f=7600,loudnorm" in captured["command"]
