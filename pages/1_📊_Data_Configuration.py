import streamlit as st
import pandas as pd
import os
from pathlib import Path
import shutil
import json
import numpy as np
import plotly.express as px

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

# Create data features directory
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
FEATURES_DIR.mkdir(parents=True, exist_ok=True)

def analyze_data_features(df):
    """Analyze data features and return feature information"""
    features = {
        "numeric_columns": [],
        "categorical_columns": [],
        "date_columns": [],
        "text_columns": [],
        "column_stats": {}
    }
    
    for col in df.columns:
        col_type = df[col].dtype
        non_null_count = df[col].count()
        null_count = df[col].isnull().sum()
        
        # Basic statistics
        stats = {
            "non_null_count": non_null_count,
            "null_count": null_count,
            "null_percentage": (null_count / len(df)) * 100 if len(df) > 0 else 0
        }
        
        # Numeric columns
        if pd.api.types.is_numeric_dtype(col_type):
            features["numeric_columns"].append(col)
            stats.update({
                "min": df[col].min(),
                "max": df[col].max(),
                "mean": df[col].mean(),
                "std": df[col].std()
            })
        
        # Categorical columns
        elif df[col].nunique() < len(df) * 0.5:  # If unique values are less than 50% of total rows
            features["categorical_columns"].append(col)
            stats.update({
                "unique_values": df[col].nunique(),
                "most_common": df[col].value_counts().head(3).to_dict()
            })
        
        # Date columns
        elif pd.api.types.is_datetime64_dtype(col_type):
            features["date_columns"].append(col)
            stats.update({
                "min_date": df[col].min(),
                "max_date": df[col].max()
            })
        
        # Text columns
        else:
            features["text_columns"].append(col)
            stats.update({
                "avg_length": df[col].astype(str).str.len().mean(),
                "max_length": df[col].astype(str).str.len().max()
            })
        
        features["column_stats"][col] = stats
    
    return features

def save_data_features(file_name, features):
    """Save data features to JSON file"""
    features_file = FEATURES_DIR / f"{file_name}.json"
    with open(features_file, 'w', encoding='utf-8') as f:
        json.dump(features, f, ensure_ascii=False, indent=2, default=str)

def load_excel_file(file_path):
    """Load Excel file with proper data type conversion"""
    try:
        # Read Excel file with specific data types
        df = pd.read_excel(
            file_path,
            dtype={
                '指标名称': str,
                '指标值': float,
                '权重': float,
                '评分标准_及格线': float,
                '评分标准_优秀线': float,
                '单位': str
            }
        )
        
        # Convert numeric columns to float
        numeric_columns = ['指标值', '权重', '评分标准_及格线', '评分标准_优秀线']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"加载文件时出错: {str(e)}")
        return None

# File upload section
st.header("上传新文件")
uploaded_file = st.file_uploader(
    "选择Excel文件上传",
    type=['xlsx', 'xls'],
    help="支持.xlsx和.xls格式的文件"
)

if uploaded_file is not None:
    try:
        # Save the uploaded file
        file_path = UPLOAD_DIR / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Load and process the file
        df = load_excel_file(file_path)
        if df is not None:
            # Continue with the rest of the processing...
            # Analyze data features
            features = analyze_data_features(df)
            save_data_features(uploaded_file.name, features)
            
            # Display data preview
            st.subheader("数据预览")
            st.dataframe(df.head(), use_container_width=True)
            
            # Display basic info
            st.subheader("数据信息")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("行数", len(df))
            with col2:
                st.metric("列数", len(df.columns))
            
            # Display column information
            st.subheader("列信息")
            columns_info = []
            for col in df.columns:
                stats = features["column_stats"][col]
                info = {
                    "列名": col,
                    "数据类型": str(df[col].dtype),
                    "非空值数量": stats["non_null_count"],
                    "空值数量": stats["null_count"],
                    "空值比例": f"{stats['null_percentage']:.1f}%"
                }
                
                if col in features["numeric_columns"]:
                    info.update({
                        "最小值": f"{stats['min']:.2f}",
                        "最大值": f"{stats['max']:.2f}",
                        "平均值": f"{stats['mean']:.2f}",
                        "标准差": f"{stats['std']:.2f}"
                    })
                elif col in features["categorical_columns"]:
                    info.update({
                        "唯一值数量": stats["unique_values"],
                        "最常见值": ", ".join([f"{k}({v})" for k, v in stats["most_common"].items()])
                    })
                
                columns_info.append(info)
            
            st.dataframe(pd.DataFrame(columns_info), use_container_width=True)
            
            # Display data features
            st.subheader("数据特征")
            
            # Numeric columns analysis
            if features["numeric_columns"]:
                st.write("数值型列分析")
                numeric_df = df[features["numeric_columns"]]
                st.line_chart(numeric_df)
                
                # Correlation matrix
                st.write("相关性分析")
                corr_matrix = numeric_df.corr()
                fig = px.imshow(
                    corr_matrix,
                    title="相关性热力图",
                    color_continuous_scale="RdBu",
                    aspect="auto"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Categorical columns analysis
            if features["categorical_columns"]:
                st.write("类别型列分析")
                for col in features["categorical_columns"]:
                    value_counts = df[col].value_counts()
                    st.bar_chart(value_counts)
    except Exception as e:
        st.error(f"处理文件时出错: {str(e)}")

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
            # Also remove the features file if it exists
            features_file = FEATURES_DIR / f"{file_to_delete}.json"
            if features_file.exists():
                os.remove(features_file)
            st.success(f"文件 {file_to_delete} 已删除")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"删除文件时出错: {str(e)}")

# File preview and analysis section
st.header("文件预览与数据分析")
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
            
            # Analyze data features
            features = analyze_data_features(df)
            save_data_features(selected_file, features)
            
            # Display data preview
            st.subheader("数据预览")
            st.dataframe(df.head(), use_container_width=True)
            
            # Display basic info
            st.subheader("数据信息")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("行数", len(df))
            with col2:
                st.metric("列数", len(df.columns))
            
            # Display column information
            st.subheader("列信息")
            columns_info = []
            for col in df.columns:
                stats = features["column_stats"][col]
                info = {
                    "列名": col,
                    "数据类型": str(df[col].dtype),
                    "非空值数量": stats["non_null_count"],
                    "空值数量": stats["null_count"],
                    "空值比例": f"{stats['null_percentage']:.1f}%"
                }
                
                if col in features["numeric_columns"]:
                    info.update({
                        "最小值": f"{stats['min']:.2f}",
                        "最大值": f"{stats['max']:.2f}",
                        "平均值": f"{stats['mean']:.2f}",
                        "标准差": f"{stats['std']:.2f}"
                    })
                elif col in features["categorical_columns"]:
                    info.update({
                        "唯一值数量": stats["unique_values"],
                        "最常见值": ", ".join([f"{k}({v})" for k, v in stats["most_common"].items()])
                    })
                
                columns_info.append(info)
            
            st.dataframe(pd.DataFrame(columns_info), use_container_width=True)
            
            # Display data features
            st.subheader("数据特征")
            
            # Numeric columns analysis
            if features["numeric_columns"]:
                st.write("数值型列分析")
                numeric_df = df[features["numeric_columns"]]
                st.line_chart(numeric_df)
                
                # Correlation matrix
                st.write("相关性分析")
                corr_matrix = numeric_df.corr()
                fig = px.imshow(
                    corr_matrix,
                    title="相关性热力图",
                    color_continuous_scale="RdBu",
                    aspect="auto"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Categorical columns analysis
            if features["categorical_columns"]:
                st.write("类别型列分析")
                for col in features["categorical_columns"]:
                    value_counts = df[col].value_counts()
                    st.bar_chart(value_counts)
            
        except Exception as e:
            st.error(f"读取文件时出错: {str(e)}")
else:
    st.info("请先上传文件以预览数据") 