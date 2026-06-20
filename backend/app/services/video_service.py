import shutil
import subprocess
from pathlib import Path
import logging
from time import perf_counter

from app.utils.errors import ModelExecutionError
from app.utils.storage import extracted_audio_path

logger = logging.getLogger(__name__)


class VideoAudioExtractionService:
    def extract_wav(self, video_path: Path) -> tuple[str, Path]:
        logger.info("video extraction started | input_video=%s", video_path)
        if shutil.which("ffmpeg") is None:
            logger.error("video extraction failed | reason=ffmpeg_not_found")
            raise ModelExecutionError(
                "ffmpeg is not installed or not available on PATH. Install ffmpeg and restart the terminal.",
                status_code=503,
            )

        audio_id, output_path = extracted_audio_path()
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_path),
        ]

        try:
            start = perf_counter()
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            logger.exception("video extraction failed | reason=os_error")
            raise ModelExecutionError(f"ffmpeg audio extraction failed: {exc}", status_code=500) from exc

        if result.returncode != 0:
            error = result.stderr.strip() or "Unknown ffmpeg error."
            logger.error("video extraction failed | returncode=%s stderr=%s", result.returncode, error)
            raise ModelExecutionError(f"ffmpeg audio extraction failed: {error}", status_code=500)

        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.error("video extraction failed | reason=empty_output path=%s", output_path)
            raise ModelExecutionError("ffmpeg produced an empty audio file.", status_code=422)

        logger.info(
            "video extraction completed | duration_sec=%.2f audio_id=%s size_bytes=%s output=%s",
            perf_counter() - start,
            audio_id,
            output_path.stat().st_size,
            output_path,
        )
        return audio_id, output_path
