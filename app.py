# Importing Required Packages
import streamlit as st
import os
import tempfile
import pandas as pd
import base64
from detection import modified_damage_detection_report

# Page Config
st.set_page_config(
    page_title="Car Damage Detection",
    layout="wide"
)

# Setting the Title and Description
st.markdown(
    """
    <h1 style='text-align: center;'>🚗 AI-Powered Car Damage Detection & Reporting System</h1>
    <p style='text-align: center; font-size:18px;'>
        Upload a car inspection video and get a damage detection report.
    </p>
    """,
    unsafe_allow_html=True
)
# Upload video section (centered & compact)
st.markdown(
    """
    <h3 style='text-align: center;'>📤 Upload a video file</h3>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 2, 1])  # middle col wider
with col2:
    uploaded_file = st.file_uploader(
        "Upload",
        type=["mp4", "avi", "mov", "mkv", "mpeg4"],
        label_visibility="collapsed"
    )

# Process uploaded video
if uploaded_file is not None:

    # Get original uploaded file name (without extension)
    original_filename = uploaded_file.name
    base_name, ext = os.path.splitext(original_filename)

    # Save to a temp file (but keep original filename for naming outputs)
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    # Centered "Run Detection" button
    col1, col2, col3 = st.columns([1, 2, 1])  # middle column wider
    with col2:
        run_detection = st.button("▶️ Run Detection", use_container_width=True)

    if run_detection:
        # Create 3 columns, use the middle one for spinner
        col1, col2, col3 = st.columns([1, 2, 1])  # middle column wider
        with col2:
            with st.spinner("Processing video... Please wait ⏳"):
                output_video, output_excel = modified_damage_detection_report(video_path, custom_base_name = original_filename)

            # --- FIX for Streamlit video rendering (convert to browser-safe MP4) ---
            output_video_display = output_video.replace(".mp4", "_fixed.mp4")
            os.system(
                  f"ffmpeg -y -i \"{output_video}\" "
                  f"-c:v libx264 -preset fast -crf 23 "
                  f"-c:a aac -b:a 128k \"{output_video_display}\"")

        st.success("✅ Detection complete!")

        # Show uploaded + processed side by side (same dimensions)
        col1, col2 = st.columns(2)

        # Uploaded video
        with col1:
            st.subheader("📼 Uploaded Video")
            video_bytes = open(video_path, "rb").read()
            video_base64 = base64.b64encode(video_bytes).decode("utf-8")
            video_html = f"""
                <video width="100%" controls>
                    <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
                </video>
            """
            st.markdown(video_html, unsafe_allow_html=True)

        # Processed video
        with col2:
            st.subheader("🎯 Processed Video")
            processed_bytes = open(output_video_display, "rb").read()
            processed_base64 = base64.b64encode(processed_bytes).decode("utf-8")
            processed_html = f"""
                <video width="100%" controls>
                    <source src="data:video/mp4;base64,{processed_base64}" type="video/mp4">
                </video>
            """
            st.markdown(processed_html, unsafe_allow_html=True)

        # Show Excel Report
        st.subheader("📊 Detection Report")
        df = pd.read_excel(output_excel)
        st.dataframe(df, use_container_width=True, height=400)

        # Download buttons
        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                label="📥 Download Excel Report",
                data=open(output_excel, "rb").read(),
                file_name=os.path.basename(output_excel),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col2:
            st.download_button(
                label="📥 Download Processed Video (MP4)",
                data=open(output_video_display, "rb").read(),
                file_name=os.path.basename(output_video_display),
                mime="video/mp4",
                use_container_width=True
            )