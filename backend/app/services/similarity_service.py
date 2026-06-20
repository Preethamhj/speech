from functools import lru_cache

from app.core.config import settings
from app.utils.errors import ModelExecutionError


@lru_cache(maxsize=1)
def _load_similarity_model():
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(settings.similarity_model_name)
    except Exception as exc:
        raise ModelExecutionError(f"Failed to load similarity model: {exc}", status_code=503) from exc


class SimilarityValidationService:
    def score(self, original: str, corrected: str) -> float:
        if original.strip() == corrected.strip():
            return 1.0
        try:
            from sentence_transformers import util

            model = _load_similarity_model()
            embeddings = model.encode([original, corrected], convert_to_tensor=True, normalize_embeddings=True)
            return float(util.cos_sim(embeddings[0], embeddings[1]).item())
        except ModelExecutionError:
            raise
        except Exception as exc:
            raise ModelExecutionError(f"Similarity validation failed: {exc}", status_code=500) from exc

    def validate(self, original: str, corrected: str) -> tuple[bool, float, str]:
        similarity = self.score(original, corrected)
        if similarity < settings.similarity_threshold:
            return False, similarity, "Correction rejected because semantic similarity is below threshold."
        return True, similarity, "Correction accepted."
