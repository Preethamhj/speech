from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.services.confidence_analysis import ConfidenceAnalysisService
from app.utils.errors import ModelExecutionError


class TranscriptionResult:
    def __init__(
        self,
        transcript: str,
        language: str,
        segments: list[dict[str, object]],
        words: list[dict[str, object]],
        uncertain_words: list[dict[str, object]],
    ) -> None:
        self.transcript = transcript
        self.language = language
        self.segments = segments
        self.words = words
        self.uncertain_words = uncertain_words


@lru_cache(maxsize=1)
def _load_whisper_model():
    try:
        from faster_whisper import WhisperModel

        return WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
    except Exception as exc:
        raise ModelExecutionError(f"Failed to load Whisper model: {exc}", status_code=503) from exc


class SpeechToTextService:
    def transcribe(self, audio_path: Path) -> tuple[str, str]:
        result = self.transcribe_with_metadata(audio_path)
        return result.transcript, result.language

    def transcribe_with_metadata(self, audio_path: Path) -> TranscriptionResult:
        try:
            model = _load_whisper_model()
            kwargs = {
                "beam_size": settings.whisper_beam_size,
                "vad_filter": settings.whisper_vad_filter,
                "multilingual": True,
                "condition_on_previous_text": settings.whisper_condition_on_previous_text,
                "word_timestamps": True,
            }
            if settings.whisper_best_of > 1:
                kwargs["best_of"] = settings.whisper_best_of
            if settings.whisper_language:
                kwargs["language"] = settings.whisper_language
            segments, info = model.transcribe(
                str(audio_path),
                **kwargs,
            )
            segment_list = list(segments)
            transcript = " ".join(segment.text.strip() for segment in segment_list).strip()
            analyzer = ConfidenceAnalysisService()
            segment_confidences, word_confidences = analyzer.analyze(segment_list)
        except ModelExecutionError:
            raise
        except Exception as exc:
            message = str(exc)
            if "Invalid data found when processing input" in message:
                raise ModelExecutionError(
                    "Speech transcription failed because the uploaded file is not valid readable audio.",
                    status_code=422,
                ) from exc
            raise ModelExecutionError(f"Speech transcription failed: {exc}", status_code=500) from exc

        if not transcript:
            raise ModelExecutionError("Speech transcription produced an empty transcript.", status_code=422)
        return TranscriptionResult(
            transcript=transcript,
            language=info.language or "unknown",
            segments=[item.to_dict() for item in segment_confidences],
            words=[item.to_dict() for item in word_confidences],
            uncertain_words=analyzer.get_uncertain_words(word_confidences),
        )
