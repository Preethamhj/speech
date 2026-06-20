from app.services.correction_service import IntentPreservingCorrectionService


class DisfluencyCleanupService:
    def __init__(self) -> None:
        self._cleaner = IntentPreservingCorrectionService()

    def clean(self, transcript: str) -> str:
        return self._cleaner.deterministic_cleanup(transcript)
