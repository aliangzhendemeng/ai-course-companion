"""Streamlit 应用入口。"""

import streamlit as st

st.set_page_config(page_title="AI 慕课学伴", page_icon="📚")

st.title("📚 AI 慕课学伴")
st.markdown("""
欢迎使用 AI 慕课学伴！

请从左侧选择页面：
- **课程库**：上传和管理课程
- **课程学习**：查看总结和播放视频
- **知识问答**：基于课程内容提问
""")

# 调试用：显示当前上传大小限制
with st.sidebar:
    st.caption(f"最大上传限制: {st.get_option('server.maxUploadSize')} MB")
