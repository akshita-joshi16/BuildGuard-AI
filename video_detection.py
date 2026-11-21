"""Sampled-frame PPE detection for BuildGuard AI videos.

Analyzes one frame per second and returns annotated frames plus a summary.
This does not create a re-encoded annotated MP4.
"""

from collections import Counter
from pathlib import Path
import os
import tempfile


from detection import CONFIDENCE_THRESHOLD, get_model


def detect_video(video_file, confidence=CONFIDENCE_THRESHOLD,
                 frame_interval_seconds=1, max_frames=120):
    """Analyze an uploaded video at a fixed interval.

    Args:
        video_file: Streamlit UploadedFile or bytes containing a video.
        confidence: YOLO confidence threshold.
        frame_interval_seconds: Seconds between sampled frames.
        max_frames: Maximum number of frames to analyze.

    Returns:
        A dictionary containing annotated RGB frames, timestamps, detections,
        class counts, duration, and any error message.
    """
    result = {
        "ok": False,
        "frames": [],
        "summary": {},
        "total_frames_analyzed": 0,
        "duration_seconds": 0.0,
        "error": None,
        "warning": None,
    }

    temp_path = None
    capture = None

    try:
        import cv2

        if frame_interval_seconds <= 0:
            raise ValueError("Frame interval must be greater than zero.")

        if hasattr(video_file, "getvalue"):
            video_bytes = video_file.getvalue()
            original_name = getattr(video_file, "name", "uploaded_video.mp4")
        elif isinstance(video_file, (bytes, bytearray)):
            video_bytes = bytes(video_file)
            original_name = "uploaded_video.mp4"
        else:
            raise ValueError("Please provide an uploaded video file.")

        if not video_bytes:
            raise ValueError("The uploaded video is empty.")

        suffix = Path(original_name).suffix.lower()
        if suffix not in {".mp4", ".mov", ".avi", ".m4v", ".webm"}:
            suffix = ".mp4"

        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        capture = cv2.VideoCapture(temp_path)
        if not capture.isOpened():
            raise ValueError(
                "Could not open this video. Please try an MP4, MOV, or AVI file."
            )

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        if fps <= 0 or frame_count <= 0:
            raise ValueError("Could not read the video's frame rate or duration.")

        duration = frame_count / fps
        result["duration_seconds"] = round(duration, 2)

        model = get_model()
        counts = Counter()
        sampled_frames = 0
        timestamp = 0.0

        while timestamp < duration and sampled_frames < max_frames:
            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
            success, frame = capture.read()

            if not success or frame is None:
                timestamp += frame_interval_seconds
                continue

            predictions = model.predict(
                source=frame,
                conf=float(confidence),
                verbose=False,
            )

            if not predictions:
                timestamp += frame_interval_seconds
                continue

            prediction = predictions[0]
            names = prediction.names or model.names
            frame_detections = []

            if prediction.boxes is not None:
                for box in prediction.boxes:
                    class_id = int(box.cls[0].item())
                    score = float(box.conf[0].item())
                    coords = box.xyxy[0].tolist()

                    if isinstance(names, dict):
                        class_name = str(names.get(class_id, class_id))
                    else:
                        class_name = str(names[class_id])

                    frame_detections.append({
                        "class_id": class_id,
                        "class_name": class_name,
                        "confidence": score,
                        "x1": float(coords[0]),
                        "y1": float(coords[1]),
                        "x2": float(coords[2]),
                        "y2": float(coords[3]),
                    })
                    counts[class_name] += 1

            annotated_bgr = prediction.plot()
            annotated_rgb = cv2.cvtColor(
                annotated_bgr, cv2.COLOR_BGR2RGB
            )

            result["frames"].append({
                "timestamp_seconds": round(timestamp, 2),
                "timestamp_label": (
                    f"{int(timestamp // 60):02d}:{int(timestamp % 60):02d}"
                ),
                "annotated_image": annotated_rgb,
                "detections": frame_detections,
                "detection_count": len(frame_detections),
            })

            sampled_frames += 1
            timestamp += frame_interval_seconds

        if sampled_frames == 0:
            raise ValueError("No video frames could be analyzed.")

        result["ok"] = True
        result["summary"] = dict(counts)
        result["total_frames_analyzed"] = sampled_frames

        if timestamp < duration:
            result["warning"] = (
                f"Analysis stopped after {max_frames} sampled frames. "
                "Use a shorter video to analyze the entire clip."
            )

        return result

    except Exception as exc:
        result["error"] = str(exc)
        return result

    finally:
        if capture is not None:
            capture.release()

        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
