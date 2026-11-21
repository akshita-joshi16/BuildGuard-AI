"""BuildGuard AI website.

This file is the Streamlit website. Image upload runs the trained YOLO
model in detection.py. Video upload is still a preview only. The dashboard
history and the SQLite database are still demo data.
"""

import streamlit as st

import detection


# Sample rows for the history table.
# These are not real site events. The table always says "Demo".
DEMO_HISTORY = [
    {
        "When": "20 Nov 2026, 09:15",
        "Location": "Site A — Foundation",
        "Upload": "Image",
        "What happened": "File received. Not analyzed.",
        "Data": "Demo",
    },
    {
        "When": "20 Nov 2026, 11:40",
        "Location": "Site B — Scaffold",
        "Upload": "Video",
        "What happened": "File received. Not analyzed.",
        "Data": "Demo",
    },
    {
        "When": "19 Nov 2026, 16:05",
        "Location": "Site A — Roof",
        "Upload": "Image",
        "What happened": "File received. Not analyzed.",
        "Data": "Demo",
    },
    {
        "When": "19 Nov 2026, 08:30",
        "Location": "Site C — Site gate",
        "Upload": "Image",
        "What happened": "File received. Not analyzed.",
        "Data": "Demo",
    },
]


def apply_design():
    """Add the navy, white, and orange look on top of Streamlit."""
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #F3F6FB;
            color: #0B1F3A;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            max-width: 1180px;
        }
        h1, h2, h3, p, label {
            color: #0B1F3A;
        }
        .hero {
            background: linear-gradient(135deg, #0B1F3A 0%, #16345C 100%);
            color: #FFFFFF;
            border-radius: 18px;
            padding: 32px 36px 28px 36px;
            border-top: 7px solid #F97316;
            margin-bottom: 8px;
        }
        .hero p,
        .hero h1,
        .eyebrow {
            color: #FFFFFF;
        }
        .hero h1 {
            font-size: 2.4rem;
            line-height: 1.15;
            margin: 8px 0 10px 0;
            font-weight: 700;
        }
        .hero .lead {
            font-size: 1.05rem;
            line-height: 1.55;
            max-width: 740px;
            margin: 0;
            color: #E7EEF8;
        }
        .eyebrow {
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-size: 0.78rem;
            font-weight: 700;
            color: #FDBA74;
            margin: 0;
        }
        .card {
            background: #FFFFFF;
            border: 1px solid #E3EAF3;
            border-radius: 14px;
            padding: 16px 18px 14px 18px;
            box-shadow: 0 8px 22px rgba(11, 31, 58, 0.05);
            min-height: 132px;
        }
        .card-label {
            color: #5C6B80;
            font-size: 0.86rem;
            font-weight: 600;
            margin: 0;
        }
        .card-value {
            color: #0B1F3A;
            font-size: 1.7rem;
            font-weight: 700;
            margin: 8px 0 6px 0;
            line-height: 1.1;
        }
        .card-note {
            color: #9A3412;
            background: #FFF4EB;
            display: inline-block;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 0.75rem;
            font-weight: 700;
            margin: 0;
        }
        .notice {
            background: #FFF7ED;
            border: 1px solid #FDBA74;
            border-left: 6px solid #F97316;
            border-radius: 12px;
            padding: 14px 16px;
            margin: 8px 0 14px 0;
        }
        .notice strong {
            color: #9A3412;
            font-size: 1.05rem;
        }
        .notice p {
            color: #7C2D12;
            margin: 6px 0 0 0;
            line-height: 1.5;
        }
        .demo-banner {
            background: #0B1F3A;
            color: #FFFFFF;
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 12px;
        }
        .demo-banner strong,
        .demo-banner span {
            color: #FFFFFF;
        }
        .history-table {
            width: 100%;
            border-collapse: collapse;
            background: #FFFFFF;
            border-radius: 12px;
            overflow: hidden;
        }
        .history-table th {
            text-align: left;
            background: #0B1F3A;
            color: #FFFFFF;
            padding: 10px 12px;
            font-size: 0.86rem;
        }
        .history-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #E8EEF5;
            color: #0B1F3A;
            font-size: 0.92rem;
        }
        .history-table tr:last-child td {
            border-bottom: none;
        }
        .tag {
            background: #FFF4EB;
            color: #C2410C;
            border-radius: 999px;
            padding: 2px 8px;
            font-weight: 700;
            font-size: 0.78rem;
        }
        .footer-note {
            color: #5C6B80;
            font-size: 0.88rem;
            margin-top: 18px;
        }
        div[data-testid="stSidebar"] {
            background-color: #0B1F3A;
        }
        div[data-testid="stSidebar"] p,
        div[data-testid="stSidebar"] span,
        div[data-testid="stSidebar"] h1,
        div[data-testid="stSidebar"] h2,
        div[data-testid="stSidebar"] h3,
        div[data-testid="stSidebar"] label {
            color: #F8FAFC;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label, value, note):
    """Draw one white statistics card."""
    st.markdown(
        f"""
        <div class="card">
            <p class="card-label">{label}</p>
            <p class="card-value">{value}</p>
            <p class="card-note">{note}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_history():
    """Draw the demo activity table. Every row is sample data."""
    rows_html = ""
    for row in DEMO_HISTORY:
        rows_html += (
            "<tr>"
            f"<td>{row['When']}</td>"
            f"<td>{row['Location']}</td>"
            f"<td>{row['Upload']}</td>"
            f"<td>{row['What happened']}</td>"
            f"<td><span class='tag'>{row['Data']}</span></td>"
            "</tr>"
        )

    st.markdown(
        f"""
        <div class="demo-banner">
            <strong>Demo data.</strong>
            <span> These rows are examples for the college project. They are not records from a real site, and no AI check was run.</span>
        </div>
        <table class="history-table">
            <thead>
                <tr>
                    <th>When</th>
                    <th>Location</th>
                    <th>Upload</th>
                    <th>What happened</th>
                    <th>Data</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def show_model_notice(model_ready):
    """Explain what the image model can and cannot decide."""
    if model_ready:
        st.markdown(
            """
            <div class="notice">
                <strong>Image detection uses the trained YOLO weights.</strong>
                <p>
                    Each box is a class the model predicted, with that class name and confidence.
                    The weights include worn-equipment classes, explicit absence classes
                    (no_helmet, no_goggle, no_gloves, no_boots, no_vest), Person, and forklift.
                    A missing helmet, vest, gloves, boots, or goggles box is not turned into a violation.
                    Video detection is not connected yet.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <div class="notice">
            <strong>The trained model file was not found.</strong>
            <p>
                Image detection looks for models/best (1).pt.
                Until that file is in place, photos can be previewed but not analyzed.
                Video detection is not connected yet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_detection_table(detections):
    """Show the class name, confidence, and box for each prediction."""
    rows = []
    for item in detections:
        rows.append(
            {
                "Class": item["class_name"],
                "Confidence": f"{item['confidence'] * 100:.1f}%",
                "x1": round(item["x1"], 1),
                "y1": round(item["y1"], 1),
                "x2": round(item["x2"], 1),
                "y2": round(item["y2"], 1),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)


def main():
    """Build the page from top to bottom."""
    # This must be the first Streamlit command.
    st.set_page_config(
        page_title="BuildGuard AI",
        page_icon="🦺",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_design()

    # A short status panel on the left. It does not run any detection.
    with st.sidebar:
        st.header("BuildGuard AI")
        st.write("Construction safety website")
        model_ready = detection.model_file_exists()
        st.write("**Model:** best (1).pt" if model_ready else "**Model:** file missing")
        st.write("**Image detection:** on" if model_ready else "**Image detection:** unavailable")
        st.write("**Video detection:** off")
        st.write("**Database:** not in use yet")
        st.divider()
        st.write(
            "Upload one or more site photos and click Detect all photos to run the trained image model. "
            "Video is still a preview. The history rows are demo data."
        )

    model_ready = detection.model_file_exists()

    # 1. Title and introduction.
    st.markdown(
        """
        <div class="hero">
            <p class="eyebrow">Construction safety monitoring</p>
            <h1>BuildGuard AI</h1>
            <p class="lead">
                A college project for construction-site safety monitoring.
                Upload one or more site photos and click Detect all photos to run the trained YOLO model.
                The page shows the predicted boxes, class names, and confidence scores.
                Video detection is not connected yet.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Dashboard cards. The counts are samples, except the model file status.
    st.subheader("Dashboard")
    st.caption("Sample numbers for the layout. They are not live site readings.")
    card_1, card_2, card_3, card_4 = st.columns(4)
    with card_1:
        if model_ready:
            stat_card("Model status", "Ready", "Image model")
        else:
            stat_card("Model status", "Missing", "Image model")
    with card_2:
        stat_card("Files checked by AI", "0", "Demo")
    with card_3:
        stat_card("Open AI alerts", "0", "Demo")
    with card_4:
        stat_card("History rows shown", "4", "Demo")

    st.write("")

    # 3 and 4. Upload boxes. Streamlit keeps the file in memory for this visit.
    # Video is preview only. Images are analyzed after Detect is clicked.
    st.subheader("Upload")
    image_column, video_column = st.columns(2)

    with image_column:
        # border=True draws a white card around this upload box.
        with st.container(border=True):
            st.markdown("**Photo upload**")
            st.write("Choose one or more site photos, then click Detect all photos.")
            image_files = st.file_uploader(
                "Site photos",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                key="image_upload",
                help="Accepted types: JPG, JPEG, PNG, WEBP. You can select multiple photos.",
            )
            detect_clicked = st.button(
                "Detect all photos",
                type="primary",
                disabled=not image_files,
                key="detect_image_button",
            )

    with video_column:
        with st.container(border=True):
            st.markdown("**Video upload**")
            st.write("Choose a short site video. It will be previewed only.")
            video_file = st.file_uploader(
                "Site video",
                type=["mp4", "mov", "avi", "webm"],
                key="video_upload",
                help="Accepted types: MP4, MOV, AVI, WEBM. No detection is run.",
            )

    # Run detection on every selected photo when the button is clicked.
    if detect_clicked and image_files:
        results = []
        for image_file in image_files:
            with st.spinner(f"Running detection on {image_file.name}..."):
                # Pass a fresh in-memory copy so each file starts at byte zero.
                from io import BytesIO
                outcome = detection.detect_image(BytesIO(image_file.getvalue()))

            results.append({
                "name": image_file.name,
                "size": image_file.size,
                "outcome": outcome,
            })

        st.session_state["image_detections"] = results

    saved_results = st.session_state.get("image_detections", [])

    # 5. Results.
    st.subheader("Detection results")
    show_model_notice(model_ready)

    if not image_files and video_file is None:
        st.write("Upload one or more photos or a video above. The preview will appear here.")

    if image_files:
        st.markdown("**Uploaded photos and results**")

        for image_file in image_files:
            matching_result = next(
                (
                    item for item in saved_results
                    if item.get("name") == image_file.name
                    and item.get("size") == image_file.size
                ),
                None,
            )

            current_image = (
                matching_result["outcome"]
                if matching_result is not None
                else None
            )

            st.divider()
            st.markdown(f"**Photo: {image_file.name}**")

            if current_image is None:
                st.image(image_file.getvalue(), use_container_width=True)
                st.caption("Click Detect all photos to run the trained model.")
            elif not current_image["ok"]:
                st.image(image_file.getvalue(), use_container_width=True)
                st.error(current_image["error"] or "Detection failed.")
            else:
                st.image(
                    current_image["annotated_image"],
                    caption=f"{image_file.name} — predicted boxes",
                    use_container_width=True,
                )
                detections = current_image["detections"]
                st.markdown("**Predicted classes**")

                if detections:
                    show_detection_table(detections)
                else:
                    st.info(
                        "The model finished and did not predict any class above "
                        "the confidence threshold of 25%. That is not a safety clearance."
                    )

                st.caption(
                    "Each row is one model prediction. These predictions are not "
                    "certified safety findings and do not by themselves establish a violation."
                )

    if video_file is not None:
        st.markdown("**Uploaded video**")
        st.video(video_file)
        st.caption(f"{video_file.name} — preview only, not analyzed.")

    # 6. History. Clearly marked as demo data.
    st.subheader("Safety activity / history")
    show_history()

    st.markdown(
        """
        <p class="footer-note">
            BuildGuard AI · image detection uses models/best (1).pt · video detection is not running · history rows are demo data.
        </p>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
