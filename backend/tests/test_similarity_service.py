from app.services.similarity_service import SimilarityValidationService


def test_similarity_validation_rejects_low_score(monkeypatch):
    service = SimilarityValidationService()
    monkeypatch.setattr(service, "score", lambda _original, _corrected: 0.42)

    accepted, score, reason = service.validate("I need project help", "Weather is sunny")

    assert accepted is False
    assert score == 0.42
    assert "below threshold" in reason


def test_similarity_validation_accepts_high_score(monkeypatch):
    service = SimilarityValidationService()
    monkeypatch.setattr(service, "score", lambda _original, _corrected: 0.96)

    accepted, score, reason = service.validate("I I need help", "I need help")

    assert accepted is True
    assert score == 0.96
    assert reason == "Correction accepted."
