# BuildGuard AI

Multimodal Construction Safety Intelligence Platform.

A college AI/ML project that uses YOLO and OpenCV to detect construction-site safety issues from images and video, presents results in a Streamlit app, stores runs in SQLite, and can be deployed publicly on Render. Model training is done in Google Colab; the code lives on GitHub.

## Stack

| Piece | Role |
| --- | --- |
| Python | Language for the whole project |
| YOLO (`ultralytics`) | Object detection model |
| OpenCV | Image and video handling |
| Streamlit | Web interface |
| SQLite | Local database |
| Google Colab | Train the model |
| GitHub | Version control |
| Render | Public deployment |

## Layout

| Path | What it will do |
| --- | --- |
| `app.py` | Streamlit entry point. Upload media, run detection, show results and reports. |
| `train.py` | Train or fine-tune YOLO and save weights. |
| `detection.py` | Run YOLO on a single image. |
| `video_detection.py` | Run YOLO across video frames. |
| `report_generator.py` | Build a safety report from detection results. |
| `storage.py` | Save and load runs in SQLite. |
| `config.py` | Settings such as folder paths, the model file name, and detection confidence. |
| `requirements.txt` | Python packages to install. |
| `.gitignore` | Tells Git to skip heavy files, the database, and private settings. |
| `models/` | Trained YOLO weights (`.pt` files stay off GitHub). |
| `dataset/data.yaml` | Tells YOLO where the images are and what each class is called. |
| `dataset/images/train/` | Photos used to teach the model. |
| `dataset/images/val/` | Photos used to check the model. |
| `dataset/labels/train/` | Box labels for the training photos. |
| `dataset/labels/val/` | Box labels for the check photos. |
| `database/` | The SQLite database file will be saved here. |
| `uploads/` | Photos and videos a user uploads on the website. |
| `outputs/images/` | Photos after detection boxes are drawn. |
| `outputs/videos/` | Videos after detection boxes are drawn. |
| `outputs/reports/` | Saved safety reports. |
| `assets/` | Logo and sample pictures for the website. |
| `pages/` | Extra website pages, added later. |
| `tests/` | Simple checks, added later. |
| `src/` | Shared helpers once the app grows past the top-level modules. |

This repository currently contains the folder structure only. Application code comes in later steps.
