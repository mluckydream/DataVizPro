import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(
    page_title="历史方案查阅",
    page_icon="🗂️",
    layout="wide"
)

# Title
st.title("🗂️ 历史方案查阅")

# Helper functions
def load_scheme_data(file_path):
    """Load and process scheme data"""
    df = pd.read_excel(file_path)
    df['得分'] = df.apply(
        lambda row: calculate_score(
            row['指标值'],
            row['权重'],
            row['评分标准_及格线'],
            row['评分标准_优秀线']
        ),
        axis=1
    )
    df['状态'] = df['得分'].apply(get_status)
    return df

def calculate_score(value, weight, pass_threshold, excellent_threshold):
    """Calculate score based on value and thresholds"""
    if pd.isna(value) or pd.isna(pass_threshold) or pd.isna(excellent_threshold):
        return None
    
    try:
        value = float(value)
        if value >= excellent_threshold:
            return 100
        elif value >= pass_threshold:
            return 60 + (value - pass_threshold) * 40 / (excellent_threshold - pass_threshold)
        else:
            return 60 * value / pass_threshold
    except:
        return None

def get_status(score):
    """Get status based on score"""
    if pd.isna(score):
        return "未知"
    elif score >= 90:
        return "优秀"
    elif score >= 75:
        return "良好"
    elif score >= 60:
        return "及格"
    else:
        return "未达标"

# Get list of files
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.warning("请先在数据配置页面上传评估数据文件")
else:
    # Create a summary of all schemes
    schemes_summary = []
    
    for file in existing_files:
        try:
            df = load_scheme_data(file)
            total_score = np.average(
                df['得分'].dropna(),
                weights=df.loc[df['得分'].notna(), '权重']
            )
            
            schemes_summary.append({
                "方案名称": file.stem,
                "上传时间": datetime.fromtimestamp(file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "总分": total_score,
                "指标总数": len(df),
                "优秀指标数": len(df[df['状态'] == "优秀"]),
                "良好指标数": len(df[df['状态'] == "良好"]),
                "及格指标数": len(df[df['状态'] == "及格"]),
                "未达标指标数": len(df[df['状态'] == "未达标"])
            })
        except Exception as e:
            st.error(f"处理文件 {file.name} 时出错: {str(e)}")
    
    if schemes_summary:
        # Convert to DataFrame
        summary_df = pd.DataFrame(schemes_summary)
        
        # Display summary table
        st.header("方案概览")
        st.dataframe(summary_df, use_container_width=True)
        
        # Visualization
        st.header("方案对比分析")
        
        # Score comparison
        fig_scores = px.bar(
            summary_df,
            x="方案名称",
            y="总分",
            title="方案总分对比",
            color="总分",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_scores, use_container_width=True)
        
        # Status distribution
        status_cols = ["优秀指标数", "良好指标数", "及格指标数", "未达标指标数"]
        fig_status = px.bar(
            summary_df,
            x="方案名称",
            y=status_cols,
            title="方案指标状态分布",
            barmode="stack"
        )
        st.plotly_chart(fig_status, use_container_width=True)
        
        # Detailed view
        st.header("方案详情")
        selected_scheme = st.selectbox(
            "选择要查看的方案",
            summary_df["方案名称"].tolist(),
            key="scheme_select"
        )
        
        if selected_scheme:
            try:
                # Load selected scheme data
                file_path = UPLOAD_DIR / f"{selected_scheme}.xlsx"
                if not file_path.exists():
                    file_path = UPLOAD_DIR / f"{selected_scheme}.xls"
                
                df = load_scheme_data(file_path)
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总分", f"{summary_df[summary_df['方案名称'] == selected_scheme]['总分'].iloc[0]:.1f}")
                with col2:
                    st.metric("指标总数", summary_df[summary_df['方案名称'] == selected_scheme]['指标总数'].iloc[0])
                with col3:
                    st.metric("优秀指标", summary_df[summary_df['方案名称'] == selected_scheme]['优秀指标数'].iloc[0])
                with col4:
                    st.metric("未达标指标", summary_df[summary_df['方案名称'] == selected_scheme]['未达标指标数'].iloc[0])
                
                # Display detailed data
                st.subheader("指标详情")
                display_df = df.copy()
                display_df['状态与得分'] = display_df.apply(
                    lambda row: f"{row['状态']} ({row['得分']:.1f})" if pd.notna(row['得分']) else "未知",
                    axis=1
                )
                display_df['评分标准'] = display_df.apply(
                    lambda row: f"{row['评分标准_及格线']} / {row['评分标准_优秀线']}",
                    axis=1
                )
                
                st.dataframe(
                    display_df[['指标名称', '指标值', '状态与得分', '权重', '评分标准', '单位']],
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"加载方案详情时出错: {str(e)}")
    else:
        st.error("无法加载任何方案数据，请检查文件格式是否正确") 