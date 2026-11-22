
"""Training script for BuildGuard AI using Ultralytics YOLO."""

from pathlib import Path
from ultralytics import YOLO

from config import PROJECT_ROOT, MODEL_DIR

# Dataset configuration
DATASET_YAML = PROJECT_ROOT / "dataset" / "data.yaml"

# Starting model
BASE_MODEL = "yolo11n.pt"

# Training settings
EPOCHS = 50
IMAGE_SIZE = 640
BATCH_SIZE = 8
WORKERS = 2


def train_model():
    """Train a YOLO model on the construction PPE dataset."""

    if not DATASET_YAML.is_file():
        raise FileNotFoundError(
            f"Dataset configuration not found: {DATASET_YAML}"
        )

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model = YOLO(BASE_MODEL)

    model.train(
        data=str(DATASET_YAML),
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        workers=WORKERS,
        project=str(PROJECT_ROOT / "runs"),
        name="buildguard_training",
        exist_ok=True,
    )

    best_weights = (
        PROJECT_ROOT
        / "runs"
        / "buildguard_training"
        / "weights"
        / "best.pt"
    )

    if not best_weights.is_file():
        raise FileNotFoundError(
            "Training finished, but best.pt was not found."
        )

    destination = MODEL_DIR / "best.pt"

    import shutil
    shutil.copy2(best_weights, destination)

    print(f"Training completed. Model saved to: {destination}")


if __name__ == "__main__":
    train_model()
