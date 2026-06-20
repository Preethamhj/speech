from pathlib import Path
import logging
from time import perf_counter

from app.core.config import settings
from app.services.audio_enhancement_service import AudioEnhancementService
from app.services.asr_normalization_service import ASRNormalizationService
from app.services.correction_service import IntentPreservingCorrectionService
from app.services.disfluency_service import DisfluencyCleanupService
from app.services.similarity_service import SimilarityValidationService
from app.services.stt_service import SpeechToTextService
from app.services.tts_service import TextToSpeechService
from app.utils.storage import save_debug_transcript

logger = logging.getLogger(__name__)
MAX_LOG_TEXT_CHARS = 3000


class SpeechAssistancePipeline:
    def __init__(self) -> None:
        self.enhancer = AudioEnhancementService()
        self.stt = SpeechToTextService()
        self.disfluency_cleaner = DisfluencyCleanupService()
        self.asr_normalizer = ASRNormalizationService()
        self.corrector = IntentPreservingCorrectionService()
        self.validator = SimilarityValidationService()
        self.tts = TextToSpeechService()

    def transcribe(self, audio_path: Path) -> tuple[str, str]:
        result = self.transcribe_with_metadata(audio_path)
        return result["transcript"], result["language"]

    def transcribe_with_metadata(self, audio_path: Path) -> dict[str, object]:
        logger.info("pipeline step started | step=audio_enhancement path=%s", audio_path)
        enhanced_audio_path = self.enhancer.enhance(audio_path)
        if enhanced_audio_path != audio_path:
            _print_terminal_block("AUDIO ENHANCEMENT", f"Input: {audio_path}\nEnhanced: {enhanced_audio_path}")

        logger.info("pipeline step started | step=transcribe path=%s", enhanced_audio_path)
        start = perf_counter()
        result = self.stt.transcribe_with_metadata(enhanced_audio_path)
        logger.info(
            "pipeline step completed | step=transcribe duration_sec=%.2f language=%s transcript_chars=%s",
            perf_counter() - start,
            result.language,
            len(result.transcript),
        )
        logger.info("extracted transcript | language=%s | text=%s", result.language, _log_text(result.transcript))
        _print_terminal_block("RAW WHISPER TRANSCRIPT", f"Language: {result.language}\n\n{result.transcript}")
        return {
            "transcript": result.transcript,
            "language": result.language,
            "segments": result.segments,
            "words": result.words,
            "uncertain_words": result.uncertain_words,
        }

    def correct(self, transcript: str, language: str | None = None) -> tuple[str, bool, float, str]:
        result = self.correct_with_stages(transcript, language)
        return result["final"], result["accepted"], result["similarity"], result["reason"]

    def correct_with_stages(self, transcript: str, language: str | None = None) -> dict[str, object]:
        disfluency_cleaned = transcript
        normalized = transcript
        if settings.enable_phase2_postprocessing:
            logger.info("pipeline step started | step=disfluency_cleanup input_chars=%s", len(transcript))
            disfluency_cleaned = self.disfluency_cleaner.clean(transcript)
            logger.info("pipeline step completed | step=disfluency_cleanup output_chars=%s", len(disfluency_cleaned))
            _print_terminal_block("DISFLUENCY CLEANED TRANSCRIPT", disfluency_cleaned)

            logger.info("pipeline step started | step=asr_normalization input_chars=%s", len(disfluency_cleaned))
            normalized = self.asr_normalizer.normalize(disfluency_cleaned)
            logger.info("pipeline step completed | step=asr_normalization output_chars=%s", len(normalized))
            _print_terminal_block("ASR NORMALIZED TRANSCRIPT", normalized)
        else:
            logger.info("phase 2 postprocessing skipped | reason=disabled")

        logger.info("pipeline step started | step=llm_correction language=%s input_chars=%s", language, len(normalized))
        start = perf_counter()
        candidate = self.corrector.correct(normalized, language)
        logger.info(
            "pipeline step completed | step=llm_correction candidate_chars=%s duration_sec=%.2f",
            len(candidate),
            perf_counter() - start,
        )
        logger.info("corrected transcript candidate | text=%s", _log_text(candidate))
        _print_terminal_block("FINAL CORRECTED TRANSCRIPT", candidate)
        logger.info("pipeline step started | step=similarity_validation threshold=%s", settings.similarity_threshold)
        validation_start = perf_counter()
        accepted, similarity, reason = self.validator.validate(transcript, candidate)
        logger.info(
            "pipeline step completed | step=similarity_validation duration_sec=%.2f accepted=%s similarity=%.4f reason=%s",
            perf_counter() - validation_start,
            accepted,
            similarity,
            reason,
        )
        if not accepted:
            logger.warning("correction rejected, using original transcript | text=%s", _log_text(transcript))
            _print_terminal_block("FINAL TRANSCRIPT USED", transcript)
            return {
                "disfluency": disfluency_cleaned,
                "normalized": normalized,
                "candidate": candidate,
                "final": transcript,
                "accepted": False,
                "similarity": similarity,
                "reason": reason,
            }
        logger.info("correction accepted | final_text=%s", _log_text(candidate))
        _print_terminal_block("FINAL TRANSCRIPT USED", candidate)
        return {
            "disfluency": disfluency_cleaned,
            "normalized": normalized,
            "candidate": candidate,
            "final": candidate,
            "accepted": True,
            "similarity": similarity,
            "reason": reason,
        }

    def generate_audio(self, text: str, language: str = "kn") -> tuple[str, Path]:
        logger.info("pipeline step started | step=tts language=%s text_chars=%s", language, len(text))
        start = perf_counter()
        audio_id, path = self.tts.synthesize(text, language)
        logger.info(
            "pipeline step completed | step=tts duration_sec=%.2f audio_id=%s path=%s",
            perf_counter() - start,
            audio_id,
            path,
        )
        return audio_id, path

    def process(self, audio_path: Path) -> dict[str, object]:
        logger.info("pipeline started | input_audio=%s", audio_path)
        start = perf_counter()
        transcription = self.transcribe_with_metadata(audio_path)
        original = str(transcription["transcript"])
        language = str(transcription["language"])
        correction = self.correct_with_stages(original, language)
        corrected = str(correction["final"])
        accepted = bool(correction["accepted"])
        similarity = float(correction["similarity"])
        reason = str(correction["reason"])
        corrected_audio_id, corrected_audio_path = self.generate_audio(corrected, language)
        debug_id = save_debug_transcript(
            {
                "raw": original,
                "disfluency": correction["disfluency"],
                "normalized": correction["normalized"],
                "final": corrected,
                "language": language,
                "accepted": accepted,
                "similarity_score": round(similarity, 4),
                "reason": reason,
                "segments": transcription["segments"],
                "words": transcription["words"],
                "uncertain_words": transcription["uncertain_words"],
                "pipeline_stages": self._pipeline_stages(),
            }
        )
        logger.info(
            "pipeline completed | duration_sec=%.2f accepted=%s similarity=%.4f corrected_audio_id=%s debug_id=%s",
            perf_counter() - start,
            accepted,
            similarity,
            corrected_audio_id,
            debug_id,
        )
        return {
            "original_transcript": original,
            "corrected_transcript": corrected,
            "disfluency_transcript": correction["disfluency"],
            "normalized_transcript": correction["normalized"],
            "language": language,
            "accepted": accepted,
            "similarity_score": round(similarity, 4),
            "reason": reason,
            "corrected_audio_id": corrected_audio_id,
            "corrected_audio_url": f"/audio/{corrected_audio_id}",
            "debug_id": debug_id,
            "words": transcription["words"],
            "uncertain_words": transcription["uncertain_words"],
            "pipeline_stages": self._pipeline_stages(),
            "corrected_audio_path": str(corrected_audio_path.relative_to(settings.base_dir)),
        }

    def _pipeline_stages(self) -> str:
        if settings.enable_phase2_postprocessing:
            return (
                "audio_enhancement -> raw_whisper_transcript -> disfluency_cleanup -> "
                "asr_normalization -> final_correction -> similarity_validation -> corrected_audio_generated"
            )
        return (
            "audio_enhancement -> raw_whisper_transcript -> final_correction -> "
            "similarity_validation -> corrected_audio_generated"
        )


def _log_text(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_LOG_TEXT_CHARS:
        return cleaned
    return f"{cleaned[:MAX_LOG_TEXT_CHARS]}... [truncated, total_chars={len(cleaned)}]"


def _print_terminal_block(title: str, text: str) -> None:
    print("\n" + "=" * 80, flush=True)
    print(title, flush=True)
    print("-" * 80, flush=True)
    print(text, flush=True)
    print("=" * 80 + "\n", flush=True)
