"""BuildGuard AI — Industrial Safety Command Center (multi-user)."""

from datetime import datetime
from io import BytesIO
import hashlib
import logging

import pandas as pd
import streamlit as st

import config
import detection
import video_detection
import storage
from report_generator import generate_pdf_report


logger = logging.getLogger("buildguard")


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="BuildGuard AI | Safety Command Center",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# DESIGN
# ---------------------------------------------------------

def apply_design():
    st.html(
        """
        <style>
        /* Hide Streamlit menu, toolbar, deploy button and footer */
        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .stAppDeployButton {
            display: none !important;
            visibility: hidden !important;
        }

        .stApp {
            background: #F5F1E7;
            color: #18372E;
        }

        .block-container {
            max-width: 1440px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, p, label {
            color: #18372E;
        }

        div[data-testid="stSidebar"] {
            background: #142D27;
        }

        div[data-testid="stSidebar"] p,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3 {
            color: #F5F1E7;
        }

        .hero {
            background: linear-gradient(120deg, #142D27, #315B49);
            border-radius: 20px;
            padding: 30px 34px;
            border-left: 7px solid #B8E36B;
            margin-bottom: 20px;
        }

        .hero h1 {
            color: #FFFFFF;
            font-size: 2.35rem;
            margin: 5px 0 10px 0;
        }

        .hero p {
            color: #E6EEE8;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 0;
        }

        .eyebrow {
            color: #B8E36B !important;
            font-size: 0.76rem !important;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .section-label {
            color: #52705F;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .info-panel {
            background: #FFFFFF;
            border: 1px solid #E4E8DD;
            border-radius: 14px;
            padding: 18px 20px;
            margin: 10px 0;
        }

        .info-panel strong {
            color: #18372E;
        }

        .info-panel p {
            color: #53685C;
            margin: 5px 0 0 0;
            line-height: 1.5;
        }

        .small-note {
            color: #65776B;
            font-size: 0.84rem;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E4E8DD;
            border-radius: 14px;
            padding: 16px 18px;
        }

        div[data-testid="stMetricLabel"] {
            color: #53685C;
        }

        div[data-testid="stMetricValue"] {
            color: #18372E;
        }

        .stButton > button[kind="primary"] {
            background: #315B49;
            border: 1px solid #315B49;
            color: #FFFFFF;
            border-radius: 9px;
            font-weight: 700;
        }

        .stButton > button[kind="primary"]:hover {
            background: #24453A;
            border-color: #24453A;
        }

        .stDownloadButton > button {
            background: #B8E36B;
            color: #18372E;
            border: 1px solid #A6D253;
            border-radius: 9px;
            font-weight: 700;
        }

        hr {
            border-color: #DDE4D8;
        }
        </style>
        """
    )


def show_hero(title, description, eyebrow="BUILDGUARD AI"):
    st.html(
        f"""
        <div class="hero">
            <p class="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
            <p>{description}</p>
        </div>
        """
    )


def show_notice():
    st.info(
        "BuildGuard AI displays AI-generated predictions from uploaded media. "
        "Predictions are not certified safety findings and do not independently "
        "establish that a safety violation occurred."
    )


def format_date(value):
    if not value:
        return "—"

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %I:%M %p")
    except (ValueError, TypeError):
        return str(value)


def file_key(uploaded_file):
    """Create a stable key so reruns do not save the same upload again."""
    return hashlib.sha256(uploaded_file.getvalue()).hexdigest()


def show_detection_table(detections):
    if not detections:
        st.info("No predictions were returned for this file.")
        return

    rows = []

    for item in detections:
        confidence = float(item.get("confidence", 0) or 0)

        row = {
            "Predicted class": item.get("class_name", "Unknown"),
            "Confidence": f"{confidence * 100:.1f}%",
        }

        if item.get("frame_timestamp") is not None:
            row["Frame time (seconds)"] = round(
                float(item["frame_timestamp"]), 2
            )

        for coordinate in ("x1", "y1", "x2", "y2"):
            if item.get(coordinate) is not None:
                row[coordinate] = round(float(item[coordinate]), 1)

        rows.append(row)

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )


def get_potential_ppe_flags(class_distribution):
    """Count predictions whose class labels explicitly indicate missing PPE."""
    total = 0

    for item in class_distribution:
        class_name = str(item.get("class_name", "")).strip().lower()

        if class_name.startswith("no_") or class_name.startswith("missing_"):
            total += int(item.get("prediction_count", 0) or 0)

    return total


# ---------------------------------------------------------
# LOGIN GATE — nothing below runs until the user signs in
# ---------------------------------------------------------

apply_design()

if not st.user.is_logged_in:
    show_hero(
        "Industrial Safety Command Center",
        "Sign in to access your personal safety dashboard. Your uploads, "
        "history and reports are private to your account.",
        "WELCOME",
    )
    st.button("Sign in with Google", type="primary", on_click=st.login)
    st.stop()

USER_ID = str(st.user.email or "").strip().lower()

if not USER_ID:
    st.error("Your account did not provide an email address. Please sign in again.")
    st.button("Log out", on_click=st.logout)
    st.stop()


def save_run_safely(**kwargs):
    """Save a detection run for the signed-in user without hiding a result."""
    try:
        return storage.save_detection_run(user_id=USER_ID, **kwargs)
    except Exception:
        logger.exception("Could not save detection run")
        st.warning(
            "Detection finished, but this run could not be saved to your history."
        )
        return None


# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------

try:
    storage.init_db()
    database_ready = True
except Exception:
    logger.exception("Database initialization failed")
    database_ready = False


# ---------------------------------------------------------
# SIDEBAR NAVIGATION
# ---------------------------------------------------------

PAGES = [
    "Overview",
    "Image Detection",
    "Video Detection",
    "Analytics",
    "Safety Reports",
    "Detection History",
    "About",
]

model_ready = detection.model_file_exists()

with st.sidebar:
    st.markdown("## 🦺 BuildGuard AI")
    st.caption("Industrial Safety Command Center")
    st.divider()

    selected_page = st.radio(
        "NAVIGATION",
        PAGES,
        label_visibility="visible",
    )

    st.divider()

    st.caption(f"Signed in as {USER_ID}")
    st.button("Log out", on_click=st.logout, use_container_width=True)


# ---------------------------------------------------------
# LOAD DASHBOARD DATA (this user only)
# ---------------------------------------------------------

dashboard_stats = {
    "total_runs": 0,
    "image_runs": 0,
    "video_runs": 0,
    "failed_runs": 0,
    "total_predictions": 0,
}

all_class_distribution = []
recent_history = []

if database_ready:
    try:
        dashboard_stats = storage.get_dashboard_stats(USER_ID)
        all_class_distribution = storage.get_class_distribution(USER_ID, days=None)
        recent_history = storage.get_detection_history(USER_ID, limit=10)
    except Exception:
        logger.exception("Could not load dashboard information")
        st.error("Could not load your dashboard right now. Please try again.")


successful_runs = max(
    0,
    int(dashboard_stats.get("total_runs", 0) or 0)
    - int(dashboard_stats.get("failed_runs", 0) or 0),
)

potential_flags = get_potential_ppe_flags(all_class_distribution)


# =========================================================
# 1. OVERVIEW
# =========================================================

if selected_page == "Overview":

    show_hero(
        "Your Safety Dashboard",
        "A centralized view of your construction-site PPE predictions, "
        "image and video analysis, detection activity, and safety reports.",
        "PERSONAL DASHBOARD",
    )

    if not database_ready:
        st.error("Your data is temporarily unavailable. Please try again later.")

    st.markdown("### Operational overview")
    st.caption("Figures below come from your saved detection runs.")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Successful scans", successful_runs)

    with col2:
        st.metric("AI predictions", dashboard_stats.get("total_predictions", 0))

    with col3:
        st.metric("Potential PPE flags", potential_flags)

    with col4:
        st.metric("Failed runs", dashboard_stats.get("failed_runs", 0))

    st.markdown("### Analysis activity")

    activity_col1, activity_col2 = st.columns(2)

    with activity_col1:
        st.metric("Image analysis runs", dashboard_stats.get("image_runs", 0))

    with activity_col2:
        st.metric("Video analysis runs", dashboard_stats.get("video_runs", 0))

    st.markdown("### Recent activity")

    if recent_history:
        history_rows = []

        for item in recent_history:
            history_rows.append(
                {
                    "Run ID": item["id"],
                    "Date": format_date(item.get("created_at")),
                    "File": item.get("file_name", "—"),
                    "Type": str(item.get("source_type", "—")).title(),
                    "Status": str(item.get("status", "—")).title(),
                    "Predictions": item.get("prediction_count", 0),
                }
            )

        st.dataframe(
            pd.DataFrame(history_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info(
            "No saved detection runs yet. Visit Image Detection or Video "
            "Detection to analyze your first file."
        )

    show_notice()


# =========================================================
# 2. IMAGE DETECTION
# =========================================================

elif selected_page == "Image Detection":

    show_hero(
        "Image Detection",
        "Upload construction-site photographs to view predicted PPE classes, "
        "confidence scores, and annotated images.",
        "PHOTO ANALYSIS",
    )

    if not model_ready:
        st.error(
            "The detection service is temporarily unavailable. "
            "Please try again later."
        )

    uploaded_images = st.file_uploader(
        "Choose construction-site photos",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="image_upload",
    )

    if uploaded_images:
        st.caption(f"{len(uploaded_images)} photo(s) selected.")

        preview_columns = st.columns(min(len(uploaded_images), 3))

        for index, uploaded_image in enumerate(uploaded_images):
            with preview_columns[index % len(preview_columns)]:
                st.image(
                    uploaded_image.getvalue(),
                    caption=uploaded_image.name,
                    use_container_width=True,
                )

    run_images = st.button(
        "Run detection on selected photos",
        type="primary",
        disabled=not uploaded_images or not model_ready,
        use_container_width=False,
    )

    if run_images:
        results = []

        progress = st.progress(0)
        status_text = st.empty()

        for index, uploaded_image in enumerate(uploaded_images):
            status_text.write(f"Analyzing {uploaded_image.name}...")

            try:
                outcome = detection.detect_image(
                    BytesIO(uploaded_image.getvalue())
                )
            except Exception:
                logger.exception("Image detection failed")
                outcome = {
                    "ok": False,
                    "error": "Image detection failed. Please try again.",
                    "detections": [],
                }

            detections = outcome.get("detections", []) or []
            success = bool(outcome.get("ok"))

            run_id = save_run_safely(
                source_type="image",
                file_name=uploaded_image.name,
                file_size=uploaded_image.size,
                detections=detections if success else [],
                status="success" if success else "failed",
                error=None if success else "Detection failed",
            )

            results.append(
                {
                    "key": file_key(uploaded_image),
                    "name": uploaded_image.name,
                    "size": uploaded_image.size,
                    "outcome": outcome,
                    "run_id": run_id,
                }
            )

            progress.progress((index + 1) / len(uploaded_images))

        st.session_state["buildguard_image_results"] = results
        status_text.success("Image analysis finished.")

    saved_results = st.session_state.get("buildguard_image_results", [])

    if uploaded_images:
        st.markdown("### Analysis results")

        for uploaded_image in uploaded_images:
            current_key = file_key(uploaded_image)

            matching_result = next(
                (
                    result
                    for result in saved_results
                    if result.get("key") == current_key
                ),
                None,
            )

            if matching_result is None:
                continue

            outcome = matching_result["outcome"]

            with st.container(border=True):
                st.markdown(f"#### {uploaded_image.name}")

                if not outcome.get("ok"):
                    st.error("Image detection failed. Please try again.")
                    continue

                if matching_result.get("run_id") is not None:
                    st.caption(f"Saved history run ID: {matching_result['run_id']}")

                annotated = outcome.get("annotated_image")

                if annotated is not None:
                    st.image(
                        annotated,
                        caption="Model predictions",
                        use_container_width=True,
                    )

                detections = outcome.get("detections", []) or []

                result_col1, result_col2 = st.columns(2)

                with result_col1:
                    st.metric("Predictions", len(detections))

                with result_col2:
                    st.metric(
                        "Potential missing-PPE predictions",
                        sum(
                            1 for item in detections
                            if str(item.get("class_name", "")).lower().startswith(
                                ("no_", "missing_")
                            )
                        ),
                    )

                if detections:
                    show_detection_table(detections)
                else:
                    st.info(
                        "The model returned no predictions above its confidence "
                        "threshold. This does not mean the site is safety-compliant."
                    )

                st.caption(
                    "Each row is a model prediction. It is not a verified safety "
                    "violation or a unique-worker count."
                )

    show_notice()


# =========================================================
# 3. VIDEO DETECTION
# =========================================================

elif selected_page == "Video Detection":

    show_hero(
        "Video Detection",
        "Analyze uploaded construction-site videos by sampling frames at "
        "one-second intervals and reviewing the model's predictions over time.",
        "VIDEO ANALYSIS",
    )

    if not model_ready:
        st.error(
            "The detection service is temporarily unavailable. "
            "Please try again later."
        )

    uploaded_video = st.file_uploader(
        "Choose a construction-site video",
        type=["mp4", "mov", "avi", "webm"],
        key="video_upload",
    )

    if uploaded_video:
        st.video(uploaded_video)

    analyze_video = st.button(
        "Analyze video",
        type="primary",
        disabled=uploaded_video is None or not model_ready,
    )

    if analyze_video and uploaded_video is not None:
        with st.spinner("Analyzing sampled video frames. Please wait..."):
            try:
                outcome = video_detection.detect_video(
                    BytesIO(uploaded_video.getvalue()),
                    frame_interval_seconds=config.VIDEO_FRAME_INTERVAL_SECONDS,
                    max_frames=config.VIDEO_MAX_FRAMES,
                )
            except Exception:
                logger.exception("Video analysis failed")
                outcome = {
                    "ok": False,
                    "error": "Video analysis failed. Please try again.",
                    "frames": [],
                    "summary": {},
                }

        frames = outcome.get("frames", []) or []
        flattened_detections = []

        for frame in frames:
            frame_timestamp = frame.get("timestamp")

            for item in frame.get("detections", []) or []:
                saved_item = dict(item)
                saved_item["frame_timestamp"] = frame_timestamp
                flattened_detections.append(saved_item)

        success = bool(outcome.get("ok"))

        run_id = save_run_safely(
            source_type="video",
            file_name=uploaded_video.name,
            file_size=uploaded_video.size,
            detections=flattened_detections if success else [],
            status="success" if success else "failed",
            duration_seconds=outcome.get("duration_seconds"),
            frames_analyzed=outcome.get("total_frames_analyzed"),
            error=None if success else "Video analysis failed",
        )

        st.session_state["buildguard_video_result"] = {
            "key": file_key(uploaded_video),
            "name": uploaded_video.name,
            "size": uploaded_video.size,
            "outcome": outcome,
            "run_id": run_id,
        }

    saved_video = st.session_state.get("buildguard_video_result")
    matching_video = (
        uploaded_video is not None
        and saved_video is not None
        and saved_video.get("key") == file_key(uploaded_video)
    )

    if matching_video:
        outcome = saved_video["outcome"]

        st.markdown("### Video analysis results")

        if not outcome.get("ok"):
            st.error("Video analysis failed. Please try again.")
        else:
            if saved_video.get("run_id") is not None:
                st.caption(f"Saved history run ID: {saved_video['run_id']}")

            frames = outcome.get("frames", []) or []
            total_frames = outcome.get("total_frames_analyzed", len(frames))
            duration = outcome.get("duration_seconds", 0) or 0
            summary = outcome.get("summary", {}) or {}

            metric1, metric2, metric3 = st.columns(3)

            with metric1:
                st.metric("Frames analyzed", total_frames)

            with metric2:
                st.metric("Video duration", f"{float(duration):.1f} sec")

            with metric3:
                st.metric(
                    "Predictions across sampled frames",
                    sum(int(value) for value in summary.values()),
                )

            if outcome.get("warning"):
                st.warning(outcome["warning"])

            st.markdown("#### Prediction summary")

            if summary:
                summary_df = pd.DataFrame(
                    [
                        {"Predicted class": name, "Predictions": count}
                        for name, count in summary.items()
                    ]
                )
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info(
                    "No classes were predicted in the sampled frames. "
                    "This is not a safety clearance."
                )

            st.markdown("#### Sampled frame review")

            for index, frame in enumerate(frames):
                timestamp_label = frame.get(
                    "timestamp_label",
                    f"{float(frame.get('timestamp', 0) or 0):.1f} sec",
                )

                with st.expander(
                    f"Frame {index + 1} · {timestamp_label} · "
                    f"{frame.get('detection_count', len(frame.get('detections', [])))} predictions",
                    expanded=(index == 0),
                ):
                    if frame.get("annotated_image") is not None:
                        st.image(
                            frame["annotated_image"],
                            use_container_width=True,
                        )

                    show_detection_table(frame.get("detections", []) or [])

            st.caption(
                "Video predictions are counted across sampled frames. The same "
                "person or object may appear in more than one frame."
            )

    elif uploaded_video:
        st.caption("Click Analyze video to begin analysis.")

    show_notice()


# =========================================================
# 4. ANALYTICS
# =========================================================

elif selected_page == "Analytics":

    show_hero(
        "Analytics & Insights",
        "Explore your detection activity, predicted PPE classes, model "
        "confidence, and the distribution of image and video analysis.",
        "ANALYTICS",
    )

    if not database_ready:
        st.error("Analytics are temporarily unavailable. Please try again later.")
    else:
        selected_days = st.selectbox(
            "Analysis period",
            options=[7, 30, 90, 365, None],
            format_func=lambda value: "All available history" if value is None else f"Last {value} days",
            index=1,
        )

        try:
            summary = storage.get_analytics_summary(USER_ID, days=selected_days)
            trends = storage.get_daily_detection_trends(USER_ID, days=selected_days)
            class_distribution = storage.get_class_distribution(USER_ID, days=selected_days)
            source_stats = storage.get_source_type_stats(USER_ID, days=selected_days)
            confidence_stats = storage.get_confidence_stats(USER_ID, days=selected_days)

            st.markdown("### Summary")

            a, b, c, d = st.columns(4)

            with a:
                st.metric("Total runs", summary.get("total_runs", 0))

            with b:
                st.metric("Successful runs", summary.get("successful_runs", 0))

            with c:
                st.metric("Failed runs", summary.get("failed_runs", 0))

            with d:
                st.metric("Predictions", summary.get("total_predictions", 0))

            st.markdown("### Detection trends")

            if trends:
                trend_df = pd.DataFrame(trends)
                trend_df["detection_date"] = pd.to_datetime(
                    trend_df["detection_date"]
                )
                trend_df = trend_df.set_index("detection_date")

                st.line_chart(
                    trend_df[["total_runs", "image_runs", "video_runs"]]
                )

                st.caption(
                    "Daily successful analysis runs. Prediction counts are "
                    "separate because one run can contain many predictions."
                )
            else:
                st.info("No successful detection runs are available for this period.")

            st.markdown("### Predicted class distribution")

            if class_distribution:
                class_df = pd.DataFrame(class_distribution)

                left, right = st.columns([3, 2])

                with left:
                    st.bar_chart(
                        class_df.set_index("class_name")[["prediction_count"]]
                    )

                with right:
                    display_df = class_df.rename(
                        columns={
                            "class_name": "Class",
                            "prediction_count": "Predictions",
                            "average_confidence": "Average confidence",
                        }
                    )
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True,
                    )
            else:
                st.info("No class predictions are available for this period.")

            st.markdown("### Image vs video analysis")

            if source_stats:
                source_df = pd.DataFrame(source_stats)

                source_df["source_type"] = source_df["source_type"].str.title()
                source_df = source_df.rename(
                    columns={
                        "source_type": "Source",
                        "total_runs": "Successful runs",
                        "prediction_count": "Predictions",
                    }
                )

                st.dataframe(
                    source_df,
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No image or video analysis runs are available yet.")

            st.markdown("### Model confidence")

            confidence_col1, confidence_col2, confidence_col3 = st.columns(3)

            average_confidence = confidence_stats.get("average_confidence")
            minimum_confidence = confidence_stats.get("minimum_confidence")
            maximum_confidence = confidence_stats.get("maximum_confidence")

            with confidence_col1:
                st.metric(
                    "Average confidence",
                    "—" if average_confidence is None
                    else f"{float(average_confidence) * 100:.1f}%",
                )

            with confidence_col2:
                st.metric(
                    "Minimum confidence",
                    "—" if minimum_confidence is None
                    else f"{float(minimum_confidence) * 100:.1f}%",
                )

            with confidence_col3:
                st.metric(
                    "Maximum confidence",
                    "—" if maximum_confidence is None
                    else f"{float(maximum_confidence) * 100:.1f}%",
                )

            st.caption(
                "Confidence describes the model's prediction score. It is not "
                "a measure of worker safety or model accuracy."
            )

        except Exception:
            logger.exception("Could not generate analytics")
            st.error("Could not generate analytics right now. Please try again.")


# =========================================================
# 5. SAFETY REPORTS
# =========================================================

elif selected_page == "Safety Reports":

    show_hero(
        "Safety Reports",
        "Generate downloadable PDF summaries for your image and video "
        "detection runs.",
        "REPORT CENTER",
    )

    if not database_ready:
        st.error("Reports are temporarily unavailable. Please try again later.")
    else:
        try:
            report_history = storage.get_detection_history(USER_ID, limit=500)
        except Exception:
            logger.exception("Could not load report history")
            report_history = []
            st.error("Could not load your report history. Please try again.")

        if not report_history:
            st.info(
                "No saved detection runs are available yet. Analyze an image "
                "or video first, then return here to generate its report."
            )
        else:
            report_options = {}

            for item in report_history:
                label = (
                    f"Run #{item['id']} · "
                    f"{item.get('file_name', 'Unknown file')} · "
                    f"{str(item.get('source_type', '')).title()} · "
                    f"{format_date(item.get('created_at'))}"
                )
                report_options[label] = item["id"]

            selected_report_label = st.selectbox(
                "Choose a detection run",
                list(report_options.keys()),
            )

            selected_run_id = report_options[selected_report_label]

            try:
                details = storage.get_run_details(USER_ID, selected_run_id)
            except Exception:
                logger.exception("Could not load detection run")
                details = None
                st.error("Could not load this detection run. Please try again.")

            if details:
                run = details["run"]
                predictions = details["predictions"]

                report_col1, report_col2, report_col3 = st.columns(3)

                with report_col1:
                    st.metric("Run ID", run["id"])

                with report_col2:
                    st.metric("Predictions", len(predictions))

                with report_col3:
                    st.metric("Status", str(run["status"]).title())

                st.write(f"**File:** {run['file_name']}")
                st.write(f"**Type:** {str(run['source_type']).title()}")
                st.write(f"**Date:** {format_date(run.get('created_at'))}")

                if run.get("status") != "success":
                    st.warning(
                        "This run did not complete successfully. Its report "
                        "will show the saved run information and any available predictions."
                    )

                if predictions:
                    st.markdown("#### Saved predictions")
                    show_detection_table(predictions)
                else:
                    st.info("No predictions were saved for this run.")

                summary = {}
                for prediction in predictions:
                    class_name = prediction.get("class_name", "Unknown")
                    summary[class_name] = summary.get(class_name, 0) + 1

                try:
                    pdf_bytes = generate_pdf_report(
                        detections=predictions,
                        source_name=run.get("file_name", "Uploaded file"),
                        source_type=str(run.get("source_type", "image")).title(),
                        summary=summary,
                        timestamp=run.get("created_at"),
                    )

                    safe_name = "".join(
                        character if character.isalnum() or character in "-_"
                        else "_"
                        for character in str(run.get("file_name", "report"))
                    )

                    st.download_button(
                        "Download PDF safety report",
                        data=pdf_bytes,
                        file_name=f"BuildGuard_Report_{run['id']}_{safe_name}.pdf",
                        mime="application/pdf",
                        type="primary",
                    )

                except Exception:
                    logger.exception("Could not generate PDF report")
                    st.error("Could not generate the PDF report. Please try again.")

    show_notice()


# =========================================================
# 6. DETECTION HISTORY
# =========================================================

elif selected_page == "Detection History":

    show_hero(
        "Detection History",
        "Search and review your saved image and video analysis runs, their "
        "processing status, and their individual model predictions.",
        "ACTIVITY LOG",
    )

    if not database_ready:
        st.error("History is temporarily unavailable. Please try again later.")
    else:
        search_col, type_col, status_col = st.columns([2, 1, 1])

        with search_col:
            search_text = st.text_input(
                "Search by file name",
                placeholder="Enter a file name...",
            )

        with type_col:
            type_filter = st.selectbox(
                "Source type",
                ["All", "Image", "Video"],
            )

        with status_col:
            status_filter = st.selectbox(
                "Run status",
                ["All", "Success", "Failed"],
            )

        try:
            history = storage.get_detection_history(USER_ID, limit=500)
        except Exception:
            logger.exception("Could not load detection history")
            history = []
            st.error("Could not load your detection history. Please try again.")

        filtered_history = []

        for item in history:
            if search_text and search_text.lower() not in str(
                item.get("file_name", "")
            ).lower():
                continue

            if type_filter != "All" and item.get("source_type") != type_filter.lower():
                continue

            if status_filter != "All" and item.get("status") != status_filter.lower():
                continue

            filtered_history.append(item)

        st.caption(f"{len(filtered_history)} matching run(s)")

        if filtered_history:
            history_rows = []

            for item in filtered_history:
                history_rows.append(
                    {
                        "Run ID": item["id"],
                        "Date": format_date(item.get("created_at")),
                        "File name": item.get("file_name"),
                        "Source": str(item.get("source_type", "")).title(),
                        "Status": str(item.get("status", "")).title(),
                        "Predictions": item.get("prediction_count", 0),
                        "Frames": item.get("frames_analyzed") or "—",
                    }
                )

            st.dataframe(
                pd.DataFrame(history_rows),
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("### Run details")

            run_options = {
                (
                    f"Run #{item['id']} · {item.get('file_name', 'Unknown')} · "
                    f"{str(item.get('source_type', '')).title()}"
                ): item["id"]
                for item in filtered_history
            }

            selected_run_label = st.selectbox(
                "Select a run to inspect",
                list(run_options.keys()),
            )

            try:
                details = storage.get_run_details(
                    USER_ID, run_options[selected_run_label]
                )
            except Exception:
                logger.exception("Could not load run details")
                details = None
                st.error("Could not load run details. Please try again.")

            if details:
                run = details["run"]

                st.write(f"**File:** {run.get('file_name')}")
                st.write(f"**Date:** {format_date(run.get('created_at'))}")
                st.write(f"**Status:** {str(run.get('status')).title()}")

                if run.get("status") == "failed":
                    st.error("This analysis did not complete successfully.")

                if run.get("duration_seconds") is not None:
                    st.write(
                        f"**Video duration:** "
                        f"{float(run['duration_seconds']):.1f} seconds"
                    )

                if run.get("frames_analyzed") is not None:
                    st.write(f"**Frames analyzed:** {run['frames_analyzed']}")

                show_detection_table(details["predictions"])

        else:
            st.info("No detection runs match these filters.")

    show_notice()


# =========================================================
# 7. ABOUT
# =========================================================

elif selected_page == "About":

    show_hero(
        "About BuildGuard AI",
        "Computer-vision support for construction-site PPE monitoring "
        "through image and video analysis.",
        "ABOUT",
    )

    st.markdown("### What it does")

    st.markdown(
        """
        BuildGuard AI uses an object-detection model to identify
        construction-safety-related classes in uploaded photographs and
        sampled video frames. You can review predictions, track your
        activity over time, and download PDF reports.

        Your uploads, history and reports are private to your account.
        """
    )

    st.markdown("### Important limitations")

    st.warning(
        """
        - Model predictions can be incorrect or incomplete.
        - A missing-PPE class prediction is not proof that a worker violated a rule.
        - A lack of predictions does not establish that a site is safe.
        - Video analysis samples frames; it does not continuously inspect every moment.
        - Prediction counts across video frames are not unique-person counts.
        - Model confidence is not the same as model accuracy.
        - BuildGuard AI is a decision-support tool, not a certified
          safety-inspection or compliance system.
        """
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.divider()

st.caption("BuildGuard AI · AI predictions require human review.")
