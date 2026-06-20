from pathlib import Path
import argparse

from app.evaluation.cer import character_error_rate
from app.evaluation.dataset_loader import load_dataset
from app.evaluation.wer import word_error_rate
from app.services.pipeline_service import SpeechAssistancePipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark ASR and final transcript quality on a dataset.")
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("--final", action="store_true", help="Evaluate the final corrected transcript instead of raw ASR.")
    args = parser.parse_args()

    pipeline = SpeechAssistancePipeline()
    rows = []
    for sample in load_dataset(args.dataset_dir):
        transcription = pipeline.transcribe_with_metadata(sample.file)
        hypothesis = str(transcription["transcript"])
        if args.final:
            correction = pipeline.correct_with_stages(hypothesis, str(transcription["language"]))
            hypothesis = str(correction["final"])
        rows.append(
            {
                "file": sample.file.name,
                "wer": word_error_rate(sample.ground_truth, hypothesis),
                "cer": character_error_rate(sample.ground_truth, hypothesis),
            }
        )

    for row in rows:
        print(f"{row['file']}\tWER={row['wer']:.4f}\tCER={row['cer']:.4f}")
    if rows:
        print(f"AVERAGE\tWER={sum(row['wer'] for row in rows) / len(rows):.4f}\tCER={sum(row['cer'] for row in rows) / len(rows):.4f}")


if __name__ == "__main__":
    main()
