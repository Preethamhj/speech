from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    base_dir: Path = Path(__file__).resolve().parents[2]
    whisper_model_size: str = "large-v3"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str | None = "kn"
    whisper_beam_size: int = 3
    whisper_best_of: int = 3
    whisper_vad_filter: bool = True
    whisper_condition_on_previous_text: bool = False
    enable_audio_enhancement: bool = True
    enable_phase2_postprocessing: bool = True
    qwen_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    enable_llm_editor: bool = True
    similarity_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    similarity_threshold: float = 0.90
    tts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    max_audio_mb: int = 100
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ]
    cors_origin_regex: str = r"^http://(localhost|127\.0\.0\.1):\d+$"

    @property
    def storage_dir(self) -> Path:
        return self.base_dir / "storage"

    @property
    def upload_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def video_dir(self) -> Path:
        return self.storage_dir / "videos"

    @property
    def generated_dir(self) -> Path:
        return self.storage_dir / "generated"

    @property
    def debug_dir(self) -> Path:
        return self.storage_dir / "debug"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
