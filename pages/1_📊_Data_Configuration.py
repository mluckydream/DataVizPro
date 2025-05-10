import streamlit as st
import pandas as pd
import os
from pathlib import Path
import shutil

# Page config
st.set_page_config(
    page_title="数据配置与管理",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 数据配置与管理")

# Create upload directory if it doesn't exist
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# File upload section
st.header("上传新文件")
uploaded_file = st.file_uploader(
    "选择Excel文件上传",
    type=['xlsx', 'xls'],
    help="支持.xlsx和.xls格式的文件"
)

if uploaded_file is not None:
    # Save the uploaded file
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"文件 {uploaded_file.name} 上传成功！")

# Display existing files
st.header("已上传文件")
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.info("暂无上传的文件")
else:
    # Create a dataframe to display files
    files_df = pd.DataFrame({
        "文件名": [f.name for f in existing_files],
        "大小": [f"{f.stat().st_size / 1024:.1f} KB" for f in existing_files],
        "上传时间": [pd.Timestamp(f.stat().st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S') for f in existing_files]
    })
    
    # Display files in a table
    st.dataframe(files_df, use_container_width=True)
    
    # File management options
    st.subheader("文件管理")
    file_to_delete = st.selectbox(
        "选择要删除的文件",
        [f.name for f in existing_files],
        key="delete_file"
    )
    
    if st.button("删除选中文件"):
        try:
            os.remove(UPLOAD_DIR / file_to_delete)
            st.success(f"文件 {file_to_delete} 已删除")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"删除文件时出错: {str(e)}")

# File preview section
st.header("文件预览")
if existing_files:
    selected_file = st.selectbox(
        "选择要预览的文件",
        [f.name for f in existing_files],
        key="preview_file"
    )
    
    if selected_file:
        try:
            file_path = UPLOAD_DIR / selected_file
            # First read the Excel file to get sheet names
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Sheet selection
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox(
                    "选择工作表",
                    sheet_names,
                    key="sheet_select"
                )
                df = pd.read_excel(file_path, sheet_name=selected_sheet)
            else:
                df = pd.read_excel(file_path)
            
            # Display preview
            st.subheader("数据预览")
            st.dataframe(df.head(), use_container_width=True)
            
            # Display basic info
            st.subheader("数据信息")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("行数", len(df))
            with col2:
                st.metric("列数", len(df.columns))
            
            # Column information
            st.subheader("列信息")
            columns_info = pd.DataFrame({
                "列名": df.columns,
                "数据类型": df.dtypes.astype(str),
                "非空值数量": df.count(),
                "空值数量": df.isnull().sum()
            })
            st.dataframe(columns_info, use_container_width=True)
            
        except Exception as e:
            st.error(f"读取文件时出错: {str(e)}")
else:
    st.info("请先上传文件以预览数据") 