
"""Single-image PPE detection for BuildGuard AI."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "models" / "best (1).pt"
CONFIDENCE_THRESHOLD = 0.25

_model = None


def model_file_exists():
    return MODEL_PATH.is_file()


def get_model():
    """Load the trained YOLO model once."""
    global _model

    if _model is not None:
        return _model

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    try:
        from ultralytics import YOLO
        _model = YOLO(str(MODEL_PATH))
        return _model
    except ImportError as exc:
        raise ImportError(
            "Ultralytics is not installed. Install it using "
            "python -m pip install ultralytics"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Could not load the YOLO model: {exc}"
        ) from exc


def detect_image(image, confidence=CONFIDENCE_THRESHOLD):
    """Detect objects in an uploaded image."""

    result = {
        "ok": False,
        "annotated_image": None,
        "detections": [],
        "error": None,
        "model_path": str(MODEL_PATH),
        "class_names": [],
    }

    try:
        import cv2
        import numpy as np

        # Convert uploaded image to OpenCV format.
        if hasattr(image, "getvalue"):
            image_bytes = image.getvalue()
        elif isinstance(image, (bytes, bytearray)):
            image_bytes = image
        else:
            raise ValueError("Please provide an uploaded image.")

        array = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr_image = cv2.imdecode(array, cv2.IMREAD_COLOR)

        if bgr_image is None:
            raise ValueError("Could not read the uploaded image.")

        model = get_model()

        predictions = model.predict(
            source=bgr_image,
            conf=float(confidence),
            verbose=False
        )

        if not predictions:
            raise RuntimeError("The model returned no predictions.")

        prediction = predictions[0]
        names = prediction.names or model.names

        if isinstance(names, dict):
            class_names = list(names.values())
        else:
            class_names = list(names)

        detections = []

        if prediction.boxes is not None:
            for box in prediction.boxes:
                class_id = int(box.cls[0].item())
                confidence_score = float(box.conf[0].item())
                coordinates = box.xyxy[0].tolist()

                if isinstance(names, dict):
                    class_name = str(names.get(class_id, class_id))
                else:
                    class_name = str(names[class_id])

                detections.append({
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": confidence_score,
                    "x1": float(coordinates[0]),
                    "y1": float(coordinates[1]),
                    "x2": float(coordinates[2]),
                    "y2": float(coordinates[3]),
                })

        annotated_bgr = prediction.plot()
        annotated_rgb = cv2.cvtColor(
            annotated_bgr,
            cv2.COLOR_BGR2RGB
        )

        result["ok"] = True
        result["annotated_image"] = annotated_rgb
        result["detections"] = detections
        result["class_names"] = class_names

        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result
