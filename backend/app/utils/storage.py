from pathlib import Path
import json
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.utils.errors import EmptyAudioError, UnsupportedAudioFormatError

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
SUPPORTED_CONTENT_TYPES = {
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/flac",
    "audio/ogg",
    "audio/webm",
}
SUPPORTED_VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-matroska",
    "video/x-msvideo",
    "video/webm",
    "video/x-m4v",
}
MIN_AUDIO_BYTES = 44
MIN_VIDEO_BYTES = 1024


def ensure_storage_dirs() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.video_dir.mkdir(parents=True, exist_ok=True)
    settings.generated_dir.mkdir(parents=True, exist_ok=True)
    settings.debug_dir.mkdir(parents=True, exist_ok=True)


def validate_audio_file(file: UploadFile, data: bytes) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_AUDIO_EXTENSIONS and file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise UnsupportedAudioFormatError(
            "Unsupported audio format. Use wav, mp3, m4a, flac, ogg, or webm.",
            status_code=415,
        )
    if not data:
        raise EmptyAudioError("Uploaded audio is empty.", status_code=400)
    if len(data) < MIN_AUDIO_BYTES:
        raise EmptyAudioError("Uploaded audio is too small to be a valid audio file.", status_code=400)
    if suffix == ".wav" and not _looks_like_wav(data):
        raise UnsupportedAudioFormatError("Invalid WAV file. Upload a real WAV file with RIFF/WAVE audio data.", status_code=415)
    max_bytes = settings.max_audio_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise UnsupportedAudioFormatError(
            f"Audio exceeds {settings.max_audio_mb} MB limit.",
            status_code=413,
        )


async def save_upload(file: UploadFile) -> tuple[str, Path, int]:
    data = await file.read()
    validate_audio_file(file, data)
    suffix = Path(file.filename or "audio.wav").suffix.lower() or ".wav"
    audio_id = f"{uuid4().hex}{suffix}"
    path = settings.upload_dir / audio_id
    path.write_bytes(data)
    return audio_id, path, len(data)


def validate_video_file(file: UploadFile, data: bytes) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_VIDEO_EXTENSIONS and file.content_type not in SUPPORTED_VIDEO_CONTENT_TYPES:
        raise UnsupportedAudioFormatError(
            "Unsupported video format. Use mp4, mov, mkv, avi, webm, or m4v.",
            status_code=415,
        )
    if not data:
        raise EmptyAudioError("Uploaded video is empty.", status_code=400)
    if len(data) < MIN_VIDEO_BYTES:
        raise EmptyAudioError("Uploaded video is too small to be a valid video file.", status_code=400)
    max_bytes = settings.max_audio_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise UnsupportedAudioFormatError(
            f"Video exceeds {settings.max_audio_mb} MB limit.",
            status_code=413,
        )


async def save_video_upload(file: UploadFile) -> tuple[str, Path, int]:
    data = await file.read()
    validate_video_file(file, data)
    suffix = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    video_id = f"{uuid4().hex}{suffix}"
    path = settings.video_dir / video_id
    path.write_bytes(data)
    return video_id, path, len(data)


def extracted_audio_path() -> tuple[str, Path]:
    audio_id = f"{uuid4().hex}.wav"
    return audio_id, settings.upload_dir / audio_id


def enhanced_audio_path() -> tuple[str, Path]:
    audio_id = f"{uuid4().hex}.enhanced.wav"
    return audio_id, settings.upload_dir / audio_id


def resolve_uploaded_audio(audio_id: str) -> Path:
    path = (settings.upload_dir / Path(audio_id).name).resolve()
    if settings.upload_dir.resolve() not in path.parents:
        raise UnsupportedAudioFormatError("Invalid audio id.", status_code=400)
    if not path.exists():
        raise UnsupportedAudioFormatError("Audio file not found.", status_code=404)
    return path


def generated_audio_path(suffix: str = ".wav") -> tuple[str, Path]:
    audio_id = f"{uuid4().hex}{suffix}"
    return audio_id, settings.generated_dir / audio_id


def save_debug_transcript(data: dict[str, object]) -> str:
    settings.debug_dir.mkdir(parents=True, exist_ok=True)
    debug_id = uuid4().hex
    path = settings.debug_dir / f"{debug_id}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return debug_id


def load_debug_transcript(debug_id: str) -> dict[str, object]:
    path = (settings.debug_dir / f"{Path(debug_id).stem}.json").resolve()
    if settings.debug_dir.resolve() not in path.parents:
        raise UnsupportedAudioFormatError("Invalid debug transcript id.", status_code=400)
    if not path.exists():
        raise UnsupportedAudioFormatError("Debug transcript not found.", status_code=404)
    return json.loads(path.read_text(encoding="utf-8"))


def _looks_like_wav(data: bytes) -> bool:
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"
