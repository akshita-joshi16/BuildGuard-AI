# 🦺 BuildGuard AI
### AI-Powered Construction Site Safety Monitoring

BuildGuard AI is an AI-assisted construction safety monitoring application that uses computer vision to identify Personal Protective Equipment (PPE) and potential safety concerns in construction-site images and videos.

It provides an interactive web dashboard where users can upload media, view AI-generated detection results, and review previous detection activity.

## ✨ Key Features

- **Image Detection:** Upload images and identify PPE-related objects.
- **Video Detection:** Analyze video frames and display detection results.
- **AI-Based Monitoring:** Uses a trained YOLO object detection model.
- **Visual Results:** Displays annotated images with detection boxes and confidence scores.
- **Activity History:** Stores detection records using SQLite.
- **Dashboard Statistics:** Shows analysis activity and detection summaries.
- **Web Interface:** Simple and interactive Streamlit dashboard.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development |
| YOLO (Ultralytics) | Object detection |
| OpenCV | Image and video processing |
| Streamlit | Web application |
| SQLite | Detection history storage |
| NumPy | Image data processing |
| Pillow | Image handling |
| Google Colab | Model training |

## 📁 Project Structure

```text
BuildGuard-AI/
│
├── app.py
├── detection.py
├── video_detection.py
├── storage.py
├── report_generator.py
├── config.py
├── train.py
├── requirements.txt
├── packages.txt
│
├── models/
│   └── best (1).pt
│
├── assets/
├── pages/
├── database/
├── uploads/
├── outputs/
└── README.md
```

## 🚀 Run Locally

### Step 1: Clone the repository

```bash
git clone https://github.com/akshita-joshi16/BuildGuard-AI.git
```

### Step 2: Open the project directory

```bash
cd BuildGuard-AI
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## 🧠 AI Model

BuildGuard AI uses a trained YOLO model to detect objects associated with construction-site safety.

The model produces predictions with confidence scores and visual bounding boxes.

The trained model weights are expected at:

```text
models/best (1).pt
```

## 💾 Database

SQLite is used to store detection activity and related information. Users can view previously recorded image and video analysis through the application.

## 🌐 Deployment

The application is designed to run using Streamlit and can be deployed through a supported cloud hosting platform.

## ⚠️ Disclaimer

BuildGuard AI is an academic AI-assisted monitoring project. AI predictions may contain errors and should not replace professional safety inspections, certified PPE checks, or established construction-site safety procedures.

## 👩‍💻 Project Information

**Project Name:** BuildGuard AI  
**Domain:** Artificial Intelligence and Computer Vision  
**Application:** Construction Site Safety Monitoring

---

⭐ If you find this project interesting, consider giving the repository a star!
