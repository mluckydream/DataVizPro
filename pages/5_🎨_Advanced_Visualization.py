import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# Page config
st.set_page_config(
    page_title="高级数据可视化",
    page_icon="🎨",
    layout="wide"
)

# Title
st.title("🎨 高级数据可视化")

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
    # Analysis mode selection
    analysis_mode = st.radio(
        "选择分析模式",
        ["单文件分析", "多文件对比"],
        horizontal=True
    )
    
    if analysis_mode == "单文件分析":
        # Single file selection
        selected_file = st.selectbox(
            "选择要分析的文件",
            [f.name for f in existing_files],
            key="single_file"
        )
        
        if selected_file:
            try:
                # Load data
                df = load_scheme_data(UPLOAD_DIR / selected_file)
                
                # Visualization type selection
                viz_type = st.selectbox(
                    "选择可视化类型",
                    ["表格", "雷达图", "柱状图", "饼图", "热力图", "折线图"]
                )
                
                if viz_type == "表格":
                    st.dataframe(df, use_container_width=True)
                
                elif viz_type == "雷达图":
                    # Select indicators
                    selected_indicators = st.multiselect(
                        "选择要显示的指标",
                        df['指标名称'].tolist(),
                        default=df['指标名称'].tolist()[:5]
                    )
                    
                    if selected_indicators:
                        plot_df = df[df['指标名称'].isin(selected_indicators)]
                        fig = px.line_polar(
                            plot_df,
                            r='得分',
                            theta='指标名称',
                            line_close=True,
                            title="指标得分雷达图"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "柱状图":
                    # Select indicators
                    selected_indicators = st.multiselect(
                        "选择要显示的指标",
                        df['指标名称'].tolist(),
                        default=df['指标名称'].tolist()[:5]
                    )
                    
                    if selected_indicators:
                        plot_df = df[df['指标名称'].isin(selected_indicators)]
                        fig = px.bar(
                            plot_df,
                            x='指标名称',
                            y='得分',
                            color='状态',
                            title="指标得分柱状图"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "饼图":
                    # Status distribution
                    status_counts = df['状态'].value_counts()
                    fig = px.pie(
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
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "热力图":
                    # Create correlation matrix
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    corr_matrix = df[numeric_cols].corr()
                    
                    fig = go.Figure(data=go.Heatmap(
                        z=corr_matrix,
                        x=corr_matrix.columns,
                        y=corr_matrix.columns,
                        colorscale='RdBu'
                    ))
                    fig.update_layout(title="指标相关性热力图")
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "折线图":
                    # Sort by score
                    plot_df = df.sort_values('得分')
                    fig = px.line(
                        plot_df,
                        x=plot_df.index,
                        y='得分',
                        markers=True,
                        title="指标得分趋势"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"处理数据时出错: {str(e)}")
    
    else:  # Multi-file comparison
        # Multiple file selection
        selected_files = st.multiselect(
            "选择要对比的文件",
            [f.name for f in existing_files],
            default=[f.name for f in existing_files[:2]]
        )
        
        if len(selected_files) >= 2:
            try:
                # Load data for all selected files
                dfs = []
                for file in selected_files:
                    df = load_scheme_data(UPLOAD_DIR / file)
                    df['方案'] = file
                    dfs.append(df)
                
                # Combine all data
                combined_df = pd.concat(dfs)
                
                # Visualization type selection
                viz_type = st.selectbox(
                    "选择可视化类型",
                    ["表格", "雷达图", "柱状图", "饼图", "热力图", "折线图"],
                    key="multi_viz"
                )
                
                if viz_type == "表格":
                    st.dataframe(combined_df, use_container_width=True)
                
                elif viz_type == "雷达图":
                    # Select indicators
                    selected_indicators = st.multiselect(
                        "选择要显示的指标",
                        combined_df['指标名称'].unique(),
                        default=combined_df['指标名称'].unique()[:5]
                    )
                    
                    if selected_indicators:
                        plot_df = combined_df[combined_df['指标名称'].isin(selected_indicators)]
                        fig = px.line_polar(
                            plot_df,
                            r='得分',
                            theta='指标名称',
                            color='方案',
                            line_close=True,
                            title="多方案指标得分雷达图"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "柱状图":
                    # Select indicators
                    selected_indicators = st.multiselect(
                        "选择要显示的指标",
                        combined_df['指标名称'].unique(),
                        default=combined_df['指标名称'].unique()[:5]
                    )
                    
                    if selected_indicators:
                        plot_df = combined_df[combined_df['指标名称'].isin(selected_indicators)]
                        fig = px.bar(
                            plot_df,
                            x='指标名称',
                            y='得分',
                            color='方案',
                            barmode='group',
                            title="多方案指标得分对比"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "饼图":
                    # Status distribution by scheme
                    status_counts = pd.crosstab(
                        combined_df['方案'],
                        combined_df['状态']
                    )
                    fig = px.pie(
                        values=status_counts.values.flatten(),
                        names=status_counts.columns.repeat(len(status_counts)),
                        color=status_counts.columns.repeat(len(status_counts)),
                        title="多方案指标状态分布",
                        facet_col=status_counts.index
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "热力图":
                    # Create correlation matrix for each scheme
                    for scheme in selected_files:
                        scheme_df = combined_df[combined_df['方案'] == scheme]
                        numeric_cols = scheme_df.select_dtypes(include=[np.number]).columns
                        corr_matrix = scheme_df[numeric_cols].corr()
                        
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_matrix,
                            x=corr_matrix.columns,
                            y=corr_matrix.columns,
                            colorscale='RdBu'
                        ))
                        fig.update_layout(title=f"{scheme} - 指标相关性热力图")
                        st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "折线图":
                    # Score trends by scheme
                    for scheme in selected_files:
                        scheme_df = combined_df[combined_df['方案'] == scheme].sort_values('得分')
                        fig = px.line(
                            scheme_df,
                            x=scheme_df.index,
                            y='得分',
                            markers=True,
                            title=f"{scheme} - 指标得分趋势"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"处理数据时出错: {str(e)}")
        else:
            st.warning("请至少选择两个文件进行对比分析") 