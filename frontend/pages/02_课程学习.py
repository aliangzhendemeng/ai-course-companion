"""Streamlit 课程学习页面。"""

import json

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="课程学习", page_icon="📝")

st.title("📝 课程学习")

# 读取 query params（兼容 streamlit 1.28.0）
query_params = st.experimental_get_query_params()
default_course_id = query_params.get("course_id", [None])[0]
default_timestamp = float(query_params.get("timestamp", ["0.0"])[0])

# 选择课程
try:
    response = requests.get(f"{API_BASE}/api/courses")
    courses = response.json() if response.status_code == 200 else []
except requests.exceptions.ConnectionError:
    st.error("无法连接到后端服务")
    courses = []

if not courses:
    st.info("还没有课程，请先去课程库上传")
    st.stop()

completed_courses = [c for c in courses if c["status"] == "completed"]
if not completed_courses:
    st.info("课程正在处理中，请稍后再来")
    st.stop()

# 默认选中从 query params 传入的课程
selected_index = 0
if default_course_id:
    for i, c in enumerate(completed_courses):
        if str(c["id"]) == str(default_course_id):
            selected_index = i
            break

selected = st.selectbox(
    "选择课程",
    options=completed_courses,
    index=selected_index,
    format_func=lambda c: c["title"],
)
course_id = selected["id"]

# 获取课程详情、总结、进度
course_resp = requests.get(f"{API_BASE}/api/courses/{course_id}")
summary_resp = requests.get(f"{API_BASE}/api/summaries/{course_id}")
progress_resp = requests.get(f"{API_BASE}/api/progress/{course_id}")

if course_resp.status_code != 200 or summary_resp.status_code != 200:
    st.error("无法加载课程信息")
    st.stop()

course = course_resp.json()
summary = summary_resp.json()
last_position = progress_resp.json().get("last_position", 0.0) if progress_resp.status_code == 200 else 0.0
start_time = default_timestamp or last_position

# 视频播放
st.header("视频播放")
video_url = course["video_url"]

# 用 Streamlit 原生播放器，从开始时间播放
st.video(video_url, start_time=int(start_time))

# 如果指定了时间戳，提示用户
if start_time > 0:
    st.info(f"从 {start_time:.1f}s 开始播放")

# 学习进度
st.caption(f"上次观看到: {last_position:.1f}s")

# 三级总结
st.header("课程总结")

tab1, tab2, tab3 = st.tabs(["大纲", "摘要", "讲义"])

with tab1:
    st.subheader("课程大纲")
    if summary.get("outline"):
        try:
            outline = json.loads(summary["outline"])
            for item in outline:
                ts = item.get("timestamp", 0)
                title = item.get("title", "")
                col1, col2 = st.columns([1, 6])
                with col1:
                    if st.button(f"⏱️ {ts:.1f}s", key=f"outline_ts_{ts}"):
                        st.experimental_set_query_params(
                            course_id=str(course_id),
                            timestamp=str(ts),
                        )
                        st.rerun()
                with col2:
                    st.markdown(f"**{title}**")
        except json.JSONDecodeError:
            st.markdown(summary["outline"])
    else:
        st.info("暂无大纲")

with tab2:
    st.subheader("内容摘要")
    if summary.get("abstract"):
        st.markdown(summary["abstract"])
    else:
        st.info("暂无摘要")

with tab3:
    st.subheader("详细讲义")
    if summary.get("lecture_notes"):
        st.markdown(summary["lecture_notes"])
    else:
        st.info("暂无讲义")
