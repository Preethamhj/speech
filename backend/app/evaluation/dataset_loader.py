import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetSample:
    file: Path
    ground_truth: str


def load_dataset(dataset_dir: Path) -> list[DatasetSample]:
    metadata_path = dataset_dir / "metadata.json"
    data = json.loads(metadata_path.read_text(encoding="utf-8"))
    samples = data["samples"] if isinstance(data, dict) else data
    return [
        DatasetSample(
            file=dataset_dir / "audio" / str(item["file"]),
            ground_truth=str(item["ground_truth"]),
        )
        for item in samples
    ]
