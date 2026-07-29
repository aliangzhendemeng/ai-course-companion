"""Streamlit 知识问答页面。"""

import json

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="知识问答", page_icon="🤖")

st.title("🤖 知识问答")

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

selected = st.selectbox(
    "选择课程",
    options=completed_courses,
    format_func=lambda c: c["title"],
)
course_id = selected["id"]

# 搜索范围选择
scope = st.radio(
    "搜索范围",
    options=["course", "all"],
    format_func=lambda x: "当前课程" if x == "course" else "全部课程",
    horizontal=True,
)

# 提问
st.header("提问")
question = st.text_area("输入你的问题", placeholder="例如：请解释视频中提到的神经网络结构")

if st.button("发送") and question:
    with st.spinner("思考中..."):
        response = requests.post(
            f"{API_BASE}/api/chat/{course_id}",
            json={"question": question, "scope": scope},
        )

    if response.status_code == 200:
        result = response.json()
        st.markdown("### 回答")
        st.markdown(result["answer"])

        if result.get("sources"):
            st.markdown("### 参考来源")
            for source in result["sources"]:
                timestamp = source.get("timestamp", 0)
                source_type = source.get("type", "")
                text = source.get("text", "")
                source_course_id = source.get("course_id")
                source_course_title = source.get("course_title") or selected["title"]

                col1, col2 = st.columns([1, 4])
                with col1:
                    target_course_id = source_course_id or course_id
                    btn_label = f"⏱️ {timestamp:.1f}s"
                    if scope == "all" and source_course_id and source_course_id != course_id:
                        btn_label = f"📚 {source_course_title}\n{btn_label}"
                    if st.button(btn_label, key=f"ts_{timestamp}_{source_type}_{source_course_id or 0}"):
                        st.experimental_set_query_params(
                            course_id=str(target_course_id),
                            timestamp=str(timestamp),
                        )
                        st.switch_page("pages/02_课程学习.py")
                with col2:
                    st.caption(f"{source_type}: {text}")
    else:
        st.error(f"请求失败: {response.text}")

# 历史问答
st.header("历史问答")
try:
    history_resp = requests.get(f"{API_BASE}/api/chat/{course_id}/history")
    if history_resp.status_code == 200:
        history = history_resp.json()
        for msg in history:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])
except Exception:
    pass
