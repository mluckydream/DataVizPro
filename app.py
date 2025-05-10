import streamlit as st
import os
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="智能评估分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path(__file__).parent / "assets" / "custom_style.css"
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

# Load CSS
load_css()

# Main content
st.title("智能评估分析平台")
st.markdown("---")

# Welcome message
st.markdown("""
### 欢迎使用智能评估分析平台

这是一个强大的数据分析和可视化工具，帮助您：
- 📊 上传和管理评估数据
- 📈 查看详细的评估结果
- 🗂️ 分析历史方案
- ⚖️ 对比不同方案
- 🎨 创建高级可视化图表

### 快速开始
1. 在左侧导航栏中选择功能模块
2. 上传您的Excel数据文件
3. 开始分析和可视化

### 数据要求
- 支持.xlsx和.xls格式
- 详细的数据格式要求请参考各功能模块的说明
""")

# Footer
st.markdown("---")
st.markdown("© 2024 智能评估分析平台 | 版本 0.1.0") 