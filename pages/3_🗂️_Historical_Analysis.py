import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(
    page_title="历史方案分析",
    page_icon="🗂️",
    layout="wide"
)

# Title
st.title("🗂️ 历史方案分析")

# Load data features
def load_data_features(file_name):
    """Load data features from JSON file"""
    features_file = Path(__file__).parent.parent / "data" / "features" / f"{file_name}.json"
    if features_file.exists():
        with open(features_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_excel_file(file_path):
    """Load Excel file with proper data type conversion"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"加载文件时出错: {str(e)}")
        return None

# Get uploaded files
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.warning("请先在数据配置页面上传文件")
else:
    # File selection
    selected_files = st.multiselect(
        "选择要分析的文件",
        [f.name for f in existing_files],
        default=[f.name for f in existing_files[:2]] if len(existing_files) >= 2 else [f.name for f in existing_files]
    )
    
    if len(selected_files) < 2:
        st.warning("请至少选择两个文件进行分析")
    else:
        # Load and process selected files
        dfs = {}
        features = {}
        
        for file_name in selected_files:
            file_path = UPLOAD_DIR / file_name
            df = load_excel_file(file_path)
            if df is not None:
                dfs[file_name] = df
                features[file_name] = load_data_features(file_name)
        
        if len(dfs) >= 2:
            # Create tabs for different analysis types
            tab1, tab2, tab3 = st.tabs(["时间序列分析", "对比分析", "趋势模式分析"])
            
            with tab1:
                st.header("时间序列分析")
                
                # Get common numeric columns across all files
                common_numeric_cols = set.intersection(
                    *[set(features[f]["numeric_columns"]) for f in features if features[f]]
                )
                
                if common_numeric_cols:
                    selected_col = st.selectbox(
                        "选择要分析的指标",
                        list(common_numeric_cols)
                    )
                    
                    # Create time series plot
                    fig = go.Figure()
                    
                    for file_name, df in dfs.items():
                        if selected_col in df.columns:
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=df[selected_col],
                                name=file_name,
                                mode='lines+markers'
                            ))
                    
                    fig.update_layout(
                        title=f"{selected_col} 时间序列分析",
                        xaxis_title="时间",
                        yaxis_title=selected_col,
                        showlegend=True
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Calculate and display statistics
                    st.subheader("统计指标")
                    stats_df = pd.DataFrame()
                    
                    for file_name, df in dfs.items():
                        if selected_col in df.columns:
                            stats = {
                                "文件": file_name,
                                "平均值": df[selected_col].mean(),
                                "标准差": df[selected_col].std(),
                                "最小值": df[selected_col].min(),
                                "最大值": df[selected_col].max(),
                                "中位数": df[selected_col].median()
                            }
                            stats_df = pd.concat([stats_df, pd.DataFrame([stats])], ignore_index=True)
                    
                    st.dataframe(stats_df, use_container_width=True)
                else:
                    st.warning("未找到共同的数值型列")
            
            with tab2:
                st.header("对比分析")
                
                # Get common numeric columns
                common_numeric_cols = set.intersection(
                    *[set(features[f]["numeric_columns"]) for f in features if features[f]]
                )
                
                if common_numeric_cols:
                    selected_cols = st.multiselect(
                        "选择要对比的指标",
                        list(common_numeric_cols),
                        default=list(common_numeric_cols)[:3] if len(common_numeric_cols) >= 3 else list(common_numeric_cols)
                    )
                    
                    if selected_cols:
                        # Create comparison plot
                        fig = go.Figure()
                        
                        for file_name, df in dfs.items():
                            for col in selected_cols:
                                if col in df.columns:
                                    fig.add_trace(go.Box(
                                        y=df[col],
                                        name=f"{file_name} - {col}",
                                        boxpoints='all'
                                    ))
                        
                        fig.update_layout(
                            title="指标对比分析",
                            yaxis_title="值",
                            showlegend=True,
                            boxmode='group'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Calculate and display comparison statistics
                        st.subheader("对比统计")
                        comparison_stats = []
                        
                        for file_name, df in dfs.items():
                            for col in selected_cols:
                                if col in df.columns:
                                    stats = {
                                        "文件": file_name,
                                        "指标": col,
                                        "平均值": df[col].mean(),
                                        "标准差": df[col].std(),
                                        "最小值": df[col].min(),
                                        "最大值": df[col].max(),
                                        "中位数": df[col].median()
                                    }
                                    comparison_stats.append(stats)
                        
                        comparison_df = pd.DataFrame(comparison_stats)
                        st.dataframe(comparison_df, use_container_width=True)
                else:
                    st.warning("未找到共同的数值型列")
            
            with tab3:
                st.header("趋势模式分析")
                
                # Get common numeric columns
                common_numeric_cols = set.intersection(
                    *[set(features[f]["numeric_columns"]) for f in features if features[f]]
                )
                
                if common_numeric_cols:
                    selected_col = st.selectbox(
                        "选择要分析的指标",
                        list(common_numeric_cols),
                        key="trend_col"
                    )
                    
                    # Calculate rolling statistics
                    window_size = st.slider("滚动窗口大小", 2, 10, 3)
                    
                    for file_name, df in dfs.items():
                        if selected_col in df.columns:
                            st.subheader(f"{file_name} - {selected_col} 趋势分析")
                            
                            # Calculate rolling statistics
                            rolling_mean = df[selected_col].rolling(window=window_size).mean()
                            rolling_std = df[selected_col].rolling(window=window_size).std()
                            
                            # Create trend plot
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=df[selected_col],
                                name="原始数据",
                                mode='lines+markers'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=rolling_mean,
                                name="滚动平均",
                                mode='lines'
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=rolling_mean + rolling_std,
                                name="上界",
                                mode='lines',
                                line=dict(dash='dash')
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=df.index,
                                y=rolling_mean - rolling_std,
                                name="下界",
                                mode='lines',
                                line=dict(dash='dash')
                            ))
                            
                            fig.update_layout(
                                title=f"{selected_col} 趋势分析",
                                xaxis_title="时间",
                                yaxis_title=selected_col,
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate trend statistics
                            trend_stats = {
                                "趋势方向": "上升" if df[selected_col].iloc[-1] > df[selected_col].iloc[0] else "下降",
                                "波动性": f"{df[selected_col].std():.2f}",
                                "稳定性": f"{1 - (df[selected_col].std() / df[selected_col].mean()):.2f}" if df[selected_col].mean() != 0 else "N/A"
                            }
                            
                            st.write("趋势统计")
                            st.json(trend_stats)
                else:
                    st.warning("未找到共同的数值型列") 