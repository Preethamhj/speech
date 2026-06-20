import logging
import shutil
import subprocess
from pathlib import Path
from time import perf_counter

from app.core.config import settings
from app.utils.errors import ModelExecutionError
from app.utils.storage import enhanced_audio_path

logger = logging.getLogger(__name__)


class AudioEnhancementService:
    def enhance(self, audio_path: Path) -> Path:
        if not settings.enable_audio_enhancement:
            logger.info("audio enhancement skipped | reason=disabled path=%s", audio_path)
            return audio_path

        if shutil.which("ffmpeg") is None:
            logger.warning("audio enhancement skipped | reason=ffmpeg_not_found path=%s", audio_path)
            return audio_path

        _, output_path = enhanced_audio_path()
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(audio_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-af",
            "highpass=f=80,lowpass=f=7600,loudnorm",
            str(output_path),
        ]

        logger.info("audio enhancement started | input=%s output=%s", audio_path, output_path)
        try:
            start = perf_counter()
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except OSError as exc:
            raise ModelExecutionError(f"Audio enhancement failed: {exc}", status_code=500) from exc

        if result.returncode != 0:
            error = result.stderr.strip() or "Unknown ffmpeg error."
            logger.warning("audio enhancement failed, using original | stderr=%s", error)
            return audio_path

        if not output_path.exists() or output_path.stat().st_size == 0:
            logger.warning("audio enhancement produced empty output, using original | output=%s", output_path)
            return audio_path

        logger.info(
            "audio enhancement completed | duration_sec=%.2f size_bytes=%s output=%s",
            perf_counter() - start,
            output_path.stat().st_size,
            output_path,
        )
        return output_path
