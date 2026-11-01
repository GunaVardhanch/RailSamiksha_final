"""
RailSamiksha — Autonomous Aerial Railway Track Defect Inspection System
=======================================================================
Production-Grade Interactive Streamlit Application & Multi-Role Aerospace Dashboard
Powered by RT-DETR-L (Real-Time Transformer), SAHI 1:1 Scale Overlapping Patch Slicing,
ByteTrack Multi-Hit Temporal Deduplication, and RTK-GPS Asset Mapping.

Deployable to Streamlit Community Cloud, Hugging Face Spaces, Docker, and Railway.
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import cv2
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Ensure repository root is on sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Also ensure RailSamiksha_Production_App is accessible as fallback
PROD_APP_DIR = BASE_DIR / "RailSamiksha_Production_App"
if PROD_APP_DIR.exists() and str(PROD_APP_DIR) not in sys.path:
    sys.path.insert(0, str(PROD_APP_DIR))

from config import (
    DEFAULT_PYTORCH_WEIGHTS,
    DEFAULT_ONNX_WEIGHTS,
    SAMPLES_DIR,
    CLASS_NAMES,
    SEVERITY_MAPPING,
    SEVERITY_COLORS,
    DEFAULT_CONF,
    DEFAULT_SLICE_SIZE,
    DEFAULT_OVERLAP,
    DEFAULT_TEMPORAL_HITS,
    DEFAULT_VIDEO_STRIDE
)
from core.pipeline import RailSamikshaProductionPipeline

# Page configuration
st.set_page_config(
    page_title="RailSamiksha AI | AeroInspect RT-DETR",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Aerospace UI matching Indian Railways TMS & Production Aesthetic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #070b12 !important;
        color: #f1f5f9 !important;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    .header-card {
        background: linear-gradient(135deg, #0d1527 0%, #111c35 100%);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-primary { background: #0284c7; color: #ffffff; }
    .badge-success { background: #059669; color: #ffffff; }
    .badge-critical { background: #dc2626; color: #ffffff; }
    .badge-warning { background: #d97706; color: #ffffff; }
    .badge-purple { background: #7c3aed; color: #ffffff; }
    .stat-card {
        background-color: #0d1527;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .stat-label {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stat-val {
        font-size: 26px;
        font-weight: 700;
        color: #06b6d4;
        margin-top: 4px;
    }
    .sev-pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# IRPWM Standard Remedial Actions
IRPWM_ACTIONS = {
    "Rail Crack": "IRPWM Para 268: Emergency fishplate clamping & 20 kmph stop order",
    "Rail Misalignment": "IRPWM Para 224: Immediate track slew realignment & speed restriction",
    "Rail Joint Damage": "IRPWM Para 241: Re-torque fishplate bolts to 650 Nm or weld joint",
    "Missing Fastener": "IRPWM Para 257: Install standard ERC clip & rubber pad within 24h",
    "Damaged Fastener": "IRPWM Para 257: Replace Pandrol e-clip with RDSO approved MK-III",
    "Sleeper Defect": "IRPWM Para 234: Mark for spot PSC sleeper replacement in next block",
    "Foreign Objects": "IRPWM Para 219: Immediate manual track clearance of obstructions",
    "Rail Wear": "IRPWM Para 302: Lubricate rail gauge face & profile grind",
    "Ballast Defect": "IRPWM Para 228: Replenish 250mm ballast cushion & tamp"
}

# Resolve weights paths
WEIGHT_OPTIONS = {}

# 1. Primary Deployed Weights
best_candidates = [
    BASE_DIR / "weights" / "best.pt",
    PROD_APP_DIR / "weights" / "best.pt"
]
for c in best_candidates:
    if c.exists():
        WEIGHT_OPTIONS["RT-DETR-L Deployed Production Model (53.75% mAP50)"] = str(c)
        break

# 2. Sanitized 85 Epochs Checkpoint
sanitized_p = BASE_DIR / "release_weights" / "rtdetr_v3_sanitized_85_best.pt"
if sanitized_p.exists():
    WEIGHT_OPTIONS["RT-DETR-L Sanitized Checkpoint (55.3% Sleeper Precision - 85 Epochs)"] = str(sanitized_p)

# 3. Canonical 85 Epochs Checkpoint
canonical_p = BASE_DIR / "release_weights" / "rtdetr_v3_canonical_85_best.pt"
if canonical_p.exists():
    WEIGHT_OPTIONS["RT-DETR-L Canonical Checkpoint (High Sensitivity - 85 Epochs)"] = str(canonical_p)

# 4. Slimmed ONNX
onnx_candidates = [
    BASE_DIR / "weights" / "best.onnx",
    PROD_APP_DIR / "weights" / "best.onnx"
]
for c in onnx_candidates:
    if c.exists():
        WEIGHT_OPTIONS["RT-DETR-L Slimmed (ONNX FP16)"] = str(c)
        break

if not WEIGHT_OPTIONS:
    WEIGHT_OPTIONS["Default RT-DETR-L Weights"] = DEFAULT_PYTORCH_WEIGHTS


@st.cache_resource
def load_pipeline(weights_path: str, conf: float, slice_size: int, overlap: float, hits: int):
    return RailSamikshaProductionPipeline(
        weights_path=weights_path,
        conf_threshold=conf,
        slice_size=slice_size,
        overlap_ratio=overlap,
        temporal_hits=hits
    )


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Inspection Configuration")
        
        # Model selector
        chosen_label = st.selectbox(
            "Model Architecture & Checkpoint",
            list(WEIGHT_OPTIONS.keys()),
            index=0,
            help="Select fine-tuned RT-DETR-L weights for drone anomaly inference."
        )
        selected_weights = WEIGHT_OPTIONS[chosen_label]

        if not os.path.exists(selected_weights):
            st.error(f"Weights file not found at: {selected_weights}")

        conf_threshold = st.slider(
            "Confidence Threshold",
            min_value=0.10,
            max_value=0.80,
            value=0.20,
            step=0.05,
            help="Minimum confidence threshold required to register a defect detection."
        )

        st.markdown("---")
        st.markdown("#### 🔬 SAHI 1:1 Scale Tiling")
        slice_dim = st.select_slider(
            "Patch Dimension (pixels)",
            options=[512, 640, 800],
            value=DEFAULT_SLICE_SIZE,
            help="Size of sub-windows sliced across 4K drone orthophotos to prevent micro-defect feature collapse."
        )
        overlap_pct = st.slider(
            "Tile Overlap Margin (%)",
            min_value=10,
            max_value=30,
            value=int(DEFAULT_OVERLAP * 100),
            step=5
        ) / 100.0

        st.markdown("---")
        st.markdown("#### ⏱️ ByteTrack Temporal Filter")
        temporal_hits = st.slider(
            "Verification Persistence (Hits)",
            min_value=1,
            max_value=5,
            value=DEFAULT_TEMPORAL_HITS,
            step=1,
            help="Consecutive video frames a defect must persist to be confirmed in incident registry."
        )

        st.markdown("---")
        st.info("💡 **Active Checkpoint:**\n`" + Path(selected_weights).name + "`\n\n🎯 **Trained Baseline:**\n53.75% mAP@50 | 2,544 Images | 4,293 Bounding Boxes")

    # Load Pipeline
    try:
        pipeline = load_pipeline(
            weights_path=selected_weights,
            conf=conf_threshold,
            slice_size=slice_dim,
            overlap=overlap_pct,
            hits=temporal_hits
        )
        pipeline.set_confidence(conf_threshold)
        pipeline.slicer.slice_height = slice_dim
        pipeline.slicer.slice_width = slice_dim
        pipeline.slicer.overlap_height_ratio = overlap_pct
        pipeline.slicer.overlap_width_ratio = overlap_pct
        pipeline.tracker.min_hits = temporal_hits
    except Exception as e:
        st.error(f"Failed to initialize RailSamiksha Pipeline: {e}")
        return

    # Header Card
    device_name = "NVIDIA CUDA (GPU Accelerated)" if pipeline.detector.device.startswith("cuda") else "CPU Fallback"
    st.markdown(f"""
    <div class="header-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h2 style="margin: 0; color: #ffffff; font-weight: 700;">🚆 RailSamiksha AI | AeroInspect RT-DETR</h2>
                <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 14px;">
                    Autonomous Aerial Railway Track Defect Inspection & RTK-GPS Asset Mapping System
                </p>
            </div>
            <div style="margin-top: 8px;">
                <span class="badge badge-primary">{chosen_label.split('(')[0].strip()}</span>
                <span class="badge badge-success">Hardware: {device_name}</span>
                <span class="badge badge-warning">SAHI 1:1 Scale Active</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Main Navigation Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📷 Aerial Still Frame Inspection (4K SAHI)",
        "🎥 Flight Patrol Video Inspection (ByteTrack)",
        "🗺️ Georeferenced Defect Map (RTK-GPS)",
        "🌐 Integrated Full-Stack Web Platform",
        "📋 Maintenance Incident Ledger & TMS Export"
    ])

    # Find sample folders
    samples_dir = SAMPLES_DIR if SAMPLES_DIR.exists() else (PROD_APP_DIR / "samples")
    sample_images = sorted(list(samples_dir.glob("*.jpg")) + list(samples_dir.glob("*.png"))) if samples_dir.exists() else []
    sample_videos = sorted(list(samples_dir.glob("*.mp4"))) if samples_dir.exists() else []

    # =========================================================================
    # TAB 1: STILL FRAME INSPECTION
    # =========================================================================
    with tab1:
        st.markdown("#### High-Resolution Aerial Frame Defect Inspection")
        st.caption("Processes 4K / 2.7K drone orthophotos via SAHI 1:1 scale overlapping patches to preserve micro-defect features (cracks, missing Pandrol clips).")

        col_input, col_ctrl = st.columns([2, 1])

        with col_ctrl:
            img_source = st.radio("Select Image Source", ["Built-in Sample Aerial Still", "Upload Custom Drone Image"], index=0)

            if img_source == "Built-in Sample Aerial Still" and sample_images:
                chosen_sample = st.selectbox("Select Sample Asset", sample_images, format_func=lambda x: x.name)
                image_path = str(chosen_sample)
            else:
                uploaded_img = st.file_uploader("Upload Drone Orthophoto (JPG/PNG)", type=["jpg", "jpeg", "png"])
                if uploaded_img is not None:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    tfile.write(uploaded_img.read())
                    tfile.close()
                    image_path = tfile.name
                else:
                    image_path = str(sample_images[0]) if sample_images else None

            use_sahi_toggle = st.checkbox("Enable SAHI 1:1 Scale Patch Slicing", value=True, help="Prevents downscaling resolution collapse on high-res 4K images.")
            inspect_btn = st.button("🔍 Execute Track Inspection", type="primary", use_container_width=True)

        with col_input:
            if image_path and os.path.exists(image_path):
                raw_bgr = cv2.imread(image_path)
                if raw_bgr is not None:
                    h, w = raw_bgr.shape[:2]
                    st.image(cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB), caption=f"Input Orthophoto: {w} × {h} px", use_container_width=True)
                else:
                    st.error("Unable to load selected image.")

        if inspect_btn and image_path and os.path.exists(image_path):
            with st.spinner("Executing SAHI patch slicing + RT-DETR detection + Non-Maximum Merging..."):
                results = pipeline.process_still_image(raw_bgr, use_sahi=use_sahi_toggle)

            st.markdown("---")
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f"""<div class="stat-card"><div class="stat-label">Total Defects Detected</div><div class="stat-val">{len(results['detections'])}</div></div>""", unsafe_allow_html=True)
            m2.markdown(f"""<div class="stat-card"><div class="stat-label">Patches Sliced (SAHI)</div><div class="stat-val">{results['patch_count']}</div></div>""", unsafe_allow_html=True)
            m3.markdown(f"""<div class="stat-card"><div class="stat-label">Inference Latency</div><div class="stat-val">{results['latency_ms']:.1f} ms</div></div>""", unsafe_allow_html=True)
            m4.markdown(f"""<div class="stat-card"><div class="stat-label">Throughput</div><div class="stat-val">{results['fps']:.1f} FPS</div></div>""", unsafe_allow_html=True)

            st.markdown("#### Annotated Inspection Output")
            st.image(cv2.cvtColor(results["annotated_image"], cv2.COLOR_BGR2RGB), caption="Identified Railway Track Anomalies with Severity Tags", use_container_width=True)

            # Defect Breakdown
            if results["detections"]:
                st.markdown("#### 📋 Detected Defect Inventory")
                table_rows = []
                for idx, det in enumerate(results["detections"]):
                    box = [round(c, 1) for c in det["box"]]
                    action_code = IRPWM_ACTIONS.get(det["class_name"], "IRPWM General Standard: Inspect section")
                    table_rows.append({
                        "ID": f"DEF-{idx + 1:03d}",
                        "Defect Category": det["class_name"],
                        "Severity": det["severity"],
                        "Confidence Score": f"{det['score']:.1%}",
                        "Bounding Box (x1, y1, x2, y2)": str(box),
                        "IRPWM Remedial Action": action_code
                    })
                df_stills = pd.DataFrame(table_rows)
                st.dataframe(df_stills, use_container_width=True)

                # Defect Crop Inspection Gallery
                st.markdown("#### 🔬 High-Resolution Defect Crop Gallery")
                gallery_cols = st.columns(min(4, len(results["detections"])))
                for idx, det in enumerate(results["detections"][:8]):
                    x1, y1, x2, y2 = [int(round(c)) for c in det["box"]]
                    x1, y1 = max(0, x1 - 20), max(0, y1 - 20)
                    x2, y2 = min(w, x2 + 20), min(h, y2 + 20)
                    crop = raw_bgr[y1:y2, x1:x2]
                    if crop.size > 0:
                        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                        with gallery_cols[idx % len(gallery_cols)]:
                            st.image(crop_rgb, caption=f"#{idx+1} {det['class_name']} ({det['score']:.0%})", use_container_width=True)
            else:
                st.success("✅ No defects identified. Track section is in standard compliance.")

    # =========================================================================
    # TAB 2: FLIGHT PATROL VIDEO INSPECTION
    # =========================================================================
    with tab2:
        st.markdown("#### Aerial Patrol Video Stream Processing with ByteTrack Persistence")
        st.caption("Simulates live drone aerial inspection with synchronized RTK-GPS telemetry, spatial tracking, and temporal verification filtering.")

        v_col1, v_col2 = st.columns([1, 2])
        with v_col1:
            vid_source = st.radio("Select Video Input Source", ["Built-in Drone Flight Asset", "Upload Custom Drone Patrol Video (.mp4)"])

            if vid_source == "Built-in Drone Flight Asset" and sample_videos:
                chosen_vid = st.selectbox("Select Sample Flight Clip", sample_videos, format_func=lambda x: x.name)
                video_file_path = str(chosen_vid)
            else:
                uploaded_vid = st.file_uploader("Upload Drone Patrol (.mp4, .mov)", type=["mp4", "mov", "avi"])
                if uploaded_vid is not None:
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(uploaded_vid.read())
                    tfile.close()
                    video_file_path = tfile.name
                else:
                    video_file_path = str(sample_videos[0]) if sample_videos else None

            stride_val = st.slider("Frame Stride (Skip Factor)", min_value=1, max_value=5, value=DEFAULT_VIDEO_STRIDE, help="Process every N-th frame for higher throughput.")
            start_vid_btn = st.button("▶️ Launch Patrol Video Inspection", type="primary", use_container_width=True)

        with v_col2:
            video_placeholder = st.empty()
            hud_placeholder = st.empty()
            table_placeholder = st.empty()

            if not start_vid_btn and video_file_path and os.path.exists(video_file_path):
                video_placeholder.info("Click 'Launch Patrol Video Inspection' to begin autonomous stream processing.")

        if start_vid_btn and video_file_path and os.path.exists(video_file_path):
            pipeline.reset_tracker()
            cap = cv2.VideoCapture(video_file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            frame_idx = 0
            stop_btn = st.button("⏹️ Stop Stream Processing")
            progress_bar = st.progress(0)

            while cap.isOpened():
                if stop_btn:
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % stride_val != 0:
                    continue

                # Process Frame
                res = pipeline.process_video_frame(frame, frame_idx)

                # Render video frame
                frame_rgb = cv2.cvtColor(res["annotated_frame"], cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, caption=f"Patrol Video Stream | Frame {frame_idx}/{total_frames}", use_container_width=True)

                # Update HUD
                tele = res["telemetry"]
                hud_placeholder.markdown(f"""
                <div style="background: #0d1527; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 16px; margin-top: 8px; display: flex; justify-content: space-around; font-size: 13px;">
                    <div>⏱️ <b>Time:</b> {tele['flight_time_sec']:.1f}s</div>
                    <div>⚡ <b>Speed:</b> {tele['drone_speed_kmh']:.1f} km/h</div>
                    <div>📍 <b>GPS:</b> {tele['latitude']:.5f}°N, {tele['longitude']:.5f}°E</div>
                    <div>🎯 <b>Live Defects:</b> {len(res['detections'])}</div>
                    <div>📋 <b>Verified Incidents:</b> {len(res['verified_incidents'])}</div>
                </div>
                """, unsafe_allow_html=True)

                # Update incident table
                if res["verified_incidents"]:
                    df_v = pd.DataFrame(res["verified_incidents"])
                    table_placeholder.dataframe(df_v, use_container_width=True)

                if total_frames > 0:
                    progress_bar.progress(min(1.0, frame_idx / total_frames))

            cap.release()
            st.success(f"Inspection Complete! Processed {frame_idx} frames. Total verified maintenance incidents: {len(pipeline.tracker.get_verified_incidents())}")

    # =========================================================================
    # TAB 3: GEOREFERENCED DEFECT MAP
    # =========================================================================
    with tab3:
        st.markdown("#### RTK-GPS Asset Mapping & Defect Corridor Visualization")
        st.caption("Visualizes georeferenced defect locations along the surveyed railway line.")

        incidents = pipeline.tracker.get_verified_incidents()

        if incidents:
            df_map = pd.DataFrame(incidents)
            st.markdown(f"**Identified Verified Defect Locations ({len(df_map)} Sites):**")
            df_map_view = df_map.rename(columns={"Latitude": "latitude", "Longitude": "longitude"})
            st.map(df_map_view[["latitude", "longitude"]], zoom=15)
            st.dataframe(df_map, use_container_width=True)
        else:
            st.info("No video inspection run yet in this session. Showing simulated baseline railway track corridor (New Delhi - Agra Section):")
            sim_pts = []
            base_lat, base_lon = 28.6139, 77.2090
            for i in range(15):
                sim_pts.append({
                    "Track Chainage": f"KM {120 + i*0.2:.1f}",
                    "latitude": base_lat + (i * 0.0015),
                    "longitude": base_lon + (i * 0.0008),
                    "Defect": CLASS_NAMES[i % 9],
                    "Severity": SEVERITY_MAPPING[CLASS_NAMES[i % 9]]
                })
            df_sim = pd.DataFrame(sim_pts)
            st.map(df_sim[["latitude", "longitude"]], zoom=14)
            st.dataframe(df_sim, use_container_width=True)

    # =========================================================================
    # TAB 4: INTEGRATED FULL-STACK WEB PLATFORM
    # =========================================================================
    with tab4:
        st.markdown("#### 🌐 RailSamiksha Multi-Role Web Application")
        st.caption("The full-stack web application is served alongside Streamlit via the unified Starlette/Uvicorn backend engine.")

        col_w1, col_w2 = st.columns([1, 1])
        with col_w1:
            st.markdown("""
            ### Multi-Role Operations Suite:
            1. **Drone Pilot / Operator Workspace:**
               - 4K SAHI Orthophoto inspection with interactive zoom & pan.
               - Real-time AI defect verification & rejection punchlist.
               - Video patrol telemetry feed with ByteTrack active tracking.
            2. **Field Maintenance P-Way Gang Workspace:**
               - Interactive defect clearance punch-list.
               - Real-time repair sign-off with IRPWM para standard compliance.
               - Safety clearance certificate generation.
            3. **Divisional Headquarters DRM Portal:**
               - High-level KPIs: Total surveys, active flights, divisional clearance ratio.
               - Corridor defect density heatmaps & category breakdown.
               - Downloadable Indian Railways TMS CSV reports with SHA-256 integrity.
            """)
            st.link_button("🚀 Open Standalone Web App (Port 8000)", "http://localhost:8000", type="primary")

        with col_w2:
            st.markdown("""
            ### Backend REST API Endpoints:
            - `GET /api/status` — Hardware telemetry, active weights, GPU status.
            - `POST /api/infer/image` — 4K SAHI + RT-DETR-L image inference.
            - `POST /api/infer/video` — ByteTrack patrol stream tracking.
            - `POST /api/auth/login` — Database-backed RBAC authentication.
            - `GET /api/reports/csv` — TMS-compliant CSV export with SHA-256.
            - `GET /api/db/export-schema` — Indian Railways SQL DDL schema download.
            """)

        # Embed live preview iframe if web server is active
        st.markdown("---")
        st.markdown("##### Live Web Application Preview:")
        try:
            components.iframe("http://localhost:8000", height=650, scrolling=True)
        except Exception:
            st.info("Start the backend server via `launch_full_app.bat` to see the embedded web app here.")

    # =========================================================================
    # TAB 5: INCIDENT LEDGER & EXPORT
    # =========================================================================
    with tab5:
        st.markdown("#### P-Way Maintenance Incident Registry & Official Export")
        st.caption("Standardized defect ledger formatted for Indian Railways Permanent Way (P-Way) maintenance dispatch.")

        all_incidents = pipeline.tracker.get_verified_incidents()

        if all_incidents:
            df_incidents = pd.DataFrame(all_incidents)
            
            c1, c2, c3, c4 = st.columns(4)
            n_crit = len(df_incidents[df_incidents["Severity"] == "CRITICAL"])
            n_high = len(df_incidents[df_incidents["Severity"] == "HIGH"])
            n_med = len(df_incidents[df_incidents["Severity"] == "MEDIUM"])
            n_low = len(df_incidents[df_incidents["Severity"] == "LOW"])

            c1.markdown(f"""<div class="stat-card" style="border-left: 4px solid #ef4444;"><div class="stat-label">Critical Defects</div><div class="stat-val" style="color: #ef4444;">{n_crit}</div></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="stat-card" style="border-left: 4px solid #f97316;"><div class="stat-label">High Severity</div><div class="stat-val" style="color: #f97316;">{n_high}</div></div>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="stat-card" style="border-left: 4px solid #eab308;"><div class="stat-label">Medium Severity</div><div class="stat-val" style="color: #eab308;">{n_med}</div></div>""", unsafe_allow_html=True)
            c4.markdown(f"""<div class="stat-card" style="border-left: 4px solid #06b6d4;"><div class="stat-label">Low Severity</div><div class="stat-val" style="color: #06b6d4;">{n_low}</div></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.dataframe(df_incidents, use_container_width=True)

            csv_data = df_incidents.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Official P-Way Incident Report (CSV)",
                data=csv_data,
                file_name=f"RailSamiksha_Maintenance_Report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("Incident registry is currently empty. Run an inspection on Tab 1 or Tab 2 to populate verified maintenance incidents.")


if __name__ == "__main__":
    main()
