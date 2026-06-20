from pathlib import Path
import argparse

from app.services.pipeline_service import SpeechAssistancePipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the speech assistance pipeline on a local audio file.")
    parser.add_argument("audio_path", type=Path, help="Path to a local audio file")
    parser.add_argument(
        "--no-tts",
        action="store_true",
        help="Run transcription and transcript correction only, without generating corrected audio.",
    )
    args = parser.parse_args()

    pipeline = SpeechAssistancePipeline()
    if args.no_tts:
        original, language = pipeline.transcribe(args.audio_path)
        corrected, accepted, similarity, reason = pipeline.correct(original, language)
        print_result(original, corrected, language, accepted, similarity, reason, None)
        return

    result = pipeline.process(args.audio_path)
    print_result(
        str(result["original_transcript"]),
        str(result["corrected_transcript"]),
        str(result["language"]),
        bool(result["accepted"]),
        float(result["similarity_score"]),
        str(result["reason"]),
        str(result["corrected_audio_path"]),
    )


def print_result(
    original: str,
    corrected: str,
    language: str,
    accepted: bool,
    similarity: float,
    reason: str,
    audio_path: str | None,
) -> None:
    print("\n" + "#" * 80)
    print("PIPELINE SUMMARY")
    print("#" * 80)
    print(f"Language: {language}")
    print(f"Accepted: {accepted}")
    print(f"Similarity: {similarity:.4f}")
    print(f"Reason: {reason}")
    if audio_path:
        print(f"Corrected audio: {audio_path}")
    print("\nOriginal:")
    print(original)
    print("\nCorrected:")
    print(corrected)


if __name__ == "__main__":
    main()
