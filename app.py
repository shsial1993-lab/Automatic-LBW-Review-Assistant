"""Streamlit UI for the automatic LBW Review Assistant."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from lbw_review.detector import AutomaticAnalysis, analyze_video
from lbw_review.render import annotate_frame, bgr_to_rgb
from lbw_review.video import read_frame, read_video_info


st.set_page_config(
    page_title="Automatic LBW Review Assistant",
    page_icon="🏏",
    layout="wide",
)


def _save_upload(uploaded_file) -> str:
    suffix = Path(uploaded_file.name).suffix.lower() or ".mp4"
    temporary = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temporary.write(uploaded_file.getbuffer())
    temporary.flush()
    temporary.close()
    return temporary.name


@st.cache_data(show_spinner=False)
def _cached_analysis(
    video_path: str,
    width: int,
    height: int,
    fps: float,
    frames: int,
) -> AutomaticAnalysis:
    info = read_video_info(video_path)
    return analyze_video(video_path, info)


def _status_label(value: str) -> str:
    return {"passes": "Pass", "fails": "Fail", "unknown": "Unknown"}.get(value, value)


st.title("🏏 Automatic LBW Review Assistant")
st.caption("Upload a cricket clip and automatically estimate the LBW evidence.")

with st.sidebar:
    st.header("1. Upload")
    uploaded = st.file_uploader(
        "Cricket video",
        type=["mp4", "mov", "avi", "mkv"],
        help="Short clips with a visible batter, ball, and stumps work best.",
    )
    st.divider()
    st.header("Automatic analysis")
    st.write(
        "The detector tracks the ball, estimates bounce and impact, locates the "
        "wicket corridor, and applies the LBW rules without manual condition entry."
    )
    st.warning(
        "A single camera angle may not show the front foot or bat-pad order. "
        "Those conditions remain Unknown and produce an Uncertain result when evidence is insufficient."
    )

if uploaded is None:
    st.info("Upload a cricket video from the sidebar to begin automatic analysis.")
    st.stop()

video_path = _save_upload(uploaded)
try:
    info = read_video_info(video_path)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.video(uploaded.getvalue())

meta_left, meta_mid, meta_right = st.columns(3)
meta_left.metric("Resolution", f"{info.width} × {info.height}")
meta_mid.metric("FPS", f"{info.fps:.2f}")
meta_right.metric("Duration", f"{info.duration_seconds:.2f}s")

with st.spinner("Automatically tracking the ball and evaluating LBW evidence..."):
    analysis = _cached_analysis(video_path, info.width, info.height, info.fps, info.frame_count)

impact_time = analysis.impact_frame / info.fps if info.fps > 0 else 0.0
st.info(
    f"Automatic analysis selected frame {analysis.impact_frame} ({impact_time:.2f}s) as the impact review frame. "
    f"Tracked {len(analysis.ball_observations)} ball observations."
)

st.subheader("2. Automatically detected evidence")
max_frame = max(0, info.frame_count - 1)
frame_index = st.slider(
    "Inspect frame",
    min_value=0,
    max_value=max_frame,
    value=min(max_frame, max(0, analysis.impact_frame)),
    help="This only changes the displayed evidence frame; it does not ask you to enter LBW conditions.",
)

frame = read_frame(video_path, frame_index)
if frame is not None:
    annotated = annotate_frame(
        frame,
        wicket_x=analysis.wicket_x,
        corridor_half_width=analysis.corridor_half_width,
        impact_point=analysis.impact_point,
        bounce_point=analysis.bounce_point,
        ball_path=analysis.ball_observations,
    )
    st.image(bgr_to_rgb(annotated), caption=f"Automatically annotated frame {frame_index}", use_container_width=True)
else:
    st.error("Could not decode the selected frame.")

condition_rows = [
    {
        "Condition": condition.name,
        "Automatic status": _status_label(condition.status),
        "Evidence": condition.detail,
    }
    for condition in analysis.result.conditions
]
st.table(condition_rows)

with st.expander("Automatic detector notes", expanded=False):
    for name, detail in analysis.evidence.items():
        st.write(f"**{name.replace('_', ' ').title()}:** {detail}")

st.subheader("3. Decision")
result = analysis.result.as_dict()
decision = result["decision"]
if decision == "LBW Out":
    st.error(f"### {decision}\n\n{result['summary']}")
elif decision == "Not Out":
    st.success(f"### {decision}\n\n{result['summary']}")
else:
    st.warning(f"### {decision}\n\n{result['summary']}")
st.metric("Confidence", f"{result['confidence'] * 100:.0f}%")

if analysis.conditional_result is not None and decision == "Uncertain":
    conditional = analysis.conditional_result.as_dict()
    if conditional["decision"] != "Uncertain":
        st.info(
            f"Conditional result if the delivery is confirmed legal: **{conditional['decision']}** — "
            f"{conditional['summary']}"
        )

report = {
    "project": "LBW Review Assistant",
    "review": {
        "video": uploaded.name,
        "inspected_frame": frame_index,
    },
    **analysis.as_dict(),
}
st.download_button(
    "Download automatic JSON report",
    data=json.dumps(report, indent=2),
    file_name="lbw-review-report.json",
    mime="application/json",
    use_container_width=True,
)
