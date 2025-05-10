import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np

# Page config
st.set_page_config(
    page_title="评估结果详情",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 评估结果详情")

# Helper functions
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

# File selection
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.warning("请先在数据配置页面上传评估数据文件")
else:
    selected_file = st.selectbox(
        "选择评估方案",
        [f.name for f in existing_files],
        key="eval_file"
    )
    
    if selected_file:
        try:
            # Load data
            file_path = UPLOAD_DIR / selected_file
            df = pd.read_excel(file_path)
            
            # Calculate scores and status
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
            
            # Calculate weighted total score
            total_score = np.average(
                df['得分'].dropna(),
                weights=df.loc[df['得分'].notna(), '权重']
            )
            
            # Summary metrics
            st.header("评估摘要")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总分", f"{total_score:.1f}")
            with col2:
                st.metric(
                    "未达标指标",
                    len(df[df['状态'] == "未达标"]),
                    delta=None
                )
            with col3:
                st.metric(
                    "达标指标",
                    len(df[df['状态'].isin(["及格", "良好"])]),
                    delta=None
                )
            with col4:
                st.metric(
                    "优势指标",
                    len(df[df['状态'] == "优秀"]),
                    delta=None
                )
            
            # Detailed results
            st.header("详细评估结果")
            
            # Format the display dataframe
            display_df = df.copy()
            display_df['状态与得分'] = display_df.apply(
                lambda row: f"{row['状态']} ({row['得分']:.1f})" if pd.notna(row['得分']) else "未知",
                axis=1
            )
            display_df['评分标准'] = display_df.apply(
                lambda row: f"{row['评分标准_及格线']} / {row['评分标准_优秀线']}",
                axis=1
            )
            
            # Select columns to display
            display_columns = [
                '指标名称',
                '指标值',
                '状态与得分',
                '权重',
                '评分标准',
                '单位'
            ]
            
            # Display the dataframe
            st.dataframe(
                display_df[display_columns],
                use_container_width=True
            )
            
            # Visualization
            st.header("评估结果可视化")
            
            # Status distribution pie chart
            status_counts = df['状态'].value_counts()
            fig_pie = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="指标状态分布",
                color=status_counts.index,
                color_discrete_map={
                    "优秀": "#00FF00",
                    "良好": "#90EE90",
                    "及格": "#FFD700",
                    "未达标": "#FF0000",
                    "未知": "#808080"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Score distribution histogram
            fig_hist = px.histogram(
                df,
                x='得分',
                title="得分分布",
                nbins=20,
                color_discrete_sequence=['#00A0FF']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Top and bottom indicators
            st.subheader("关键指标分析")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("表现最好的指标")
                top_indicators = df.nlargest(3, '得分')[['指标名称', '指标值', '得分', '状态']]
                st.dataframe(top_indicators, use_container_width=True)
            
            with col2:
                st.write("需要改进的指标")
                bottom_indicators = df.nsmallest(3, '得分')[['指标名称', '指标值', '得分', '状态']]
                st.dataframe(bottom_indicators, use_container_width=True)
            
        except Exception as e:
            st.error(f"处理数据时出错: {str(e)}")
            st.error("请确保数据文件包含所需的列：指标名称、指标值、权重、评分标准_及格线、评分标准_优秀线、单位") 