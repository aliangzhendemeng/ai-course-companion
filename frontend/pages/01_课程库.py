"""Streamlit 课程库页面。"""

import io

import requests
import streamlit as st

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="课程库", page_icon="📁")

st.title("📁 课程库")

# 上传区域
st.header("上传新课程")
st.caption("支持最大 2GB 的视频文件，适合 45 分钟左右的慕课视频")

# 使用 form 避免页面自动 rerun 导致重复上传
with st.form("upload_form", clear_on_submit=True):
    title = st.text_input("课程标题", value="")
    uploaded_file = st.file_uploader("选择本地视频", type=["mp4", "mkv", "mov", "avi"])
    submit = st.form_submit_button("开始上传并处理")

if submit:
    if not title:
        st.error("请输入课程标题")
    elif uploaded_file is None:
        st.error("请选择视频文件")
    else:
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"title": title}
        try:
            with st.spinner("上传中，请耐心等待..."):
                response = requests.post(
                    f"{API_BASE}/api/courses/upload",
                    files=files,
                    data=data,
                    timeout=300,
                )

            if response.status_code == 200:
                course = response.json()
                st.success(f"上传成功！课程 ID: {course['id']}")
                st.rerun()
            else:
                st.error(f"上传失败: {response.text}")
        except requests.exceptions.Timeout:
            st.error("上传超时，请检查网络或视频大小后重试")
        except Exception as e:
            st.error(f"上传出错: {str(e)}")

# 课程列表
st.header("我的课程")

try:
    response = requests.get(f"{API_BASE}/api/courses")
    if response.status_code == 200:
        courses = response.json()
        if not courses:
            st.info("还没有课程，请上传一个视频")
        else:
            for course in courses:
                st.markdown("---")
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.write(f"**{course['title']}**")
                col2.write(f"状态: `{course['status']}`")
                if course.get("status_message"):
                    col2.caption(course["status_message"])

                if course["status"] == "completed":
                    if col3.button("学习", key=f"learn_{course['id']}"):
                        st.switch_page("pages/02_课程学习.py")
                elif course["status"] == "failed":
                    if col3.button("重试", key=f"retry_{course['id']}"):
                        requests.post(f"{API_BASE}/api/courses/{course['id']}/reprocess")
                        st.rerun()
                else:
                    col3.write("处理中...")
    else:
        st.error("无法获取课程列表，请确认后端服务已启动")
except requests.exceptions.ConnectionError:
    st.error("无法连接到后端服务，请确认 `uvicorn main:app --port 8000` 已启动")
