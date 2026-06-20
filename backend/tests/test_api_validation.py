from app.utils.storage import validate_audio_file, validate_video_file
from app.utils.errors import EmptyAudioError, UnsupportedAudioFormatError


class FakeUpload:
    def __init__(self, filename: str, content_type: str) -> None:
        self.filename = filename
        self.content_type = content_type


def test_empty_audio_is_rejected():
    try:
        validate_audio_file(FakeUpload("sample.wav", "audio/wav"), b"")
    except EmptyAudioError:
        return
    raise AssertionError("EmptyAudioError was not raised")


def test_tiny_audio_is_rejected():
    try:
        validate_audio_file(FakeUpload("sample.wav", "audio/wav"), b"not wav!")
    except EmptyAudioError:
        return
    raise AssertionError("EmptyAudioError was not raised")


def test_invalid_wav_header_is_rejected():
    try:
        validate_audio_file(FakeUpload("sample.wav", "audio/wav"), b"x" * 64)
    except UnsupportedAudioFormatError:
        return
    raise AssertionError("UnsupportedAudioFormatError was not raised")


def test_unsupported_audio_is_rejected():
    try:
        validate_audio_file(FakeUpload("sample.txt", "text/plain"), b"hello")
    except UnsupportedAudioFormatError:
        return
    raise AssertionError("UnsupportedAudioFormatError was not raised")


def test_video_upload_accepts_supported_formats():
    validate_video_file(FakeUpload("sample.mp4", "video/mp4"), b"v" * 2048)


def test_unsupported_video_is_rejected():
    try:
        validate_video_file(FakeUpload("sample.txt", "text/plain"), b"hello")
    except UnsupportedAudioFormatError:
        return
    raise AssertionError("UnsupportedAudioFormatError was not raised")
