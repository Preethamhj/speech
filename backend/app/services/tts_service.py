from functools import lru_cache
from pathlib import Path

import soundfile as sf

from app.core.config import settings
from app.utils.errors import ModelExecutionError
from app.utils.storage import generated_audio_path


@lru_cache(maxsize=1)
def _load_tts_model():
    try:
        from TTS.api import TTS

        return TTS(settings.tts_model_name)
    except Exception:
        return None


class TextToSpeechService:
    def synthesize(self, text: str, language: str = "kn") -> tuple[str, Path]:
        audio_id, output_path = generated_audio_path(".wav")
        try:
            model = _load_tts_model()
            if model is None:
                self._synthesize_with_system_voice(text, output_path)
                return audio_id, output_path

            kwargs = {"text": text, "file_path": str(output_path)}
            if getattr(model, "is_multi_lingual", False):
                kwargs["language"] = self._normalize_language(language)
            speakers = getattr(model, "speakers", None)
            if speakers:
                kwargs["speaker"] = speakers[0]
            model.tts_to_file(**kwargs)
        except ModelExecutionError:
            raise
        except Exception as exc:
            raise ModelExecutionError(f"Text-to-speech generation failed: {exc}", status_code=500) from exc

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ModelExecutionError("Text-to-speech generated an empty audio file.", status_code=500)
        return audio_id, output_path

    def _synthesize_with_system_voice(self, text: str, output_path: Path) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", 145)
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
        except Exception as exc:
            raise ModelExecutionError(
                "Text-to-speech generation failed. Coqui TTS is available only on Python <3.12, "
                f"and the local system voice fallback failed: {exc}",
                status_code=500,
            ) from exc

        if output_path.exists() and output_path.stat().st_size > 0:
            return

        sf.write(output_path, [0.0] * 16000, 16000)

    def _normalize_language(self, language: str) -> str:
        lowered = (language or "kn").lower()
        if lowered.startswith("en"):
            return "en"
        if lowered.startswith("kn") or lowered.startswith("kannada"):
            return "kn"
        return lowered[:2]
