from pathlib import Path

from app.services import video_service
from app.services.video_service import VideoAudioExtractionService
from app.utils.errors import ModelExecutionError


class FakeCompletedProcess:
    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr


def test_video_extraction_invokes_ffmpeg(monkeypatch):
    output_path = Path("storage/uploads/extracted-test.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(video_service.shutil, "which", lambda name: "ffmpeg.exe")
    monkeypatch.setattr(video_service, "extracted_audio_path", lambda: ("extracted-test.wav", output_path))

    def fake_run(command, capture_output, text, check):
        assert command[0] == "ffmpeg"
        assert "-vn" in command
        output_path.write_bytes(b"RIFFdata")
        return FakeCompletedProcess()

    monkeypatch.setattr(video_service.subprocess, "run", fake_run)

    audio_id, path = VideoAudioExtractionService().extract_wav(Path("storage/videos/input.mp4"))

    assert audio_id == "extracted-test.wav"
    assert path.exists()
    assert path.stat().st_size > 0


def test_video_extraction_requires_ffmpeg(monkeypatch):
    monkeypatch.setattr(video_service.shutil, "which", lambda name: None)

    try:
        VideoAudioExtractionService().extract_wav(Path("storage/videos/input.mp4"))
    except ModelExecutionError as exc:
        assert exc.status_code == 503
        assert "ffmpeg" in exc.message
        return

    raise AssertionError("ModelExecutionError was not raised")
