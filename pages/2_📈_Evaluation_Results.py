import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import numpy as np
import graphviz

# Page config
st.set_page_config(
    page_title="评估结果详情",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 评估结果详情")

# Load data features
FEATURES_DIR = Path(__file__).parent.parent / "data" / "features"
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"

def load_data_features(file_name):
    """Load data features from JSON file"""
    features_file = FEATURES_DIR / f"{file_name}.json"
    if features_file.exists():
        with open(features_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def create_mermaid_chart(df, features):
    """Create a Mermaid flowchart for data relationships"""
    mermaid_code = "graph TD\n"
    
    # Add nodes for numeric columns
    for col in features["numeric_columns"]:
        stats = features["column_stats"][col]
        mermaid_code += f"    {col}[{col}<br/>均值: {stats['mean']:.2f}<br/>标准差: {stats['std']:.2f}]\n"
    
    # Add nodes for categorical columns
    for col in features["categorical_columns"]:
        stats = features["column_stats"][col]
        mermaid_code += f"    {col}[{col}<br/>唯一值: {stats['unique_values']}]\n"
    
    # Add relationships based on correlations
    if len(features["numeric_columns"]) > 1:
        numeric_df = df[features["numeric_columns"]]
        corr_matrix = numeric_df.corr()
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i,j]) > 0.3:
                    mermaid_code += f"    {corr_matrix.columns[i]} --> {corr_matrix.columns[j]}\n"
    
    return mermaid_code

def analyze_data(df, features):
    """Analyze data and return analysis results"""
    analysis = {
        "numeric_analysis": {},
        "categorical_analysis": {},
        "correlations": {},
        "trends": {},
        "visualizations": {}
    }
    
    # Analyze numeric columns
    for col in features["numeric_columns"]:
        stats = features["column_stats"][col]
        analysis["numeric_analysis"][col] = {
            "summary": {
                "min": stats["min"],
                "max": stats["max"],
                "mean": stats["mean"],
                "std": stats["std"]
            },
            "distribution": df[col].value_counts().sort_index().to_dict()
        }
        
        # Create bar chart
        fig_bar = px.bar(
            df,
            x=df.index,
            y=col,
            title=f"{col}柱状图"
        )
        analysis["visualizations"][f"{col}_bar"] = fig_bar
        
        # Create line chart
        fig_line = px.line(
            df,
            x=df.index,
            y=col,
            title=f"{col}趋势图"
        )
        analysis["visualizations"][f"{col}_line"] = fig_line
    
    # Analyze categorical columns
    for col in features["categorical_columns"]:
        stats = features["column_stats"][col]
        analysis["categorical_analysis"][col] = {
            "unique_values": stats["unique_values"],
            "most_common": stats["most_common"],
            "distribution": df[col].value_counts().to_dict()
        }
        
        # Create pie chart
        fig_pie = px.pie(
            df,
            names=col,
            title=f"{col}分布"
        )
        analysis["visualizations"][f"{col}_pie"] = fig_pie
    
    # Calculate correlations between numeric columns
    if len(features["numeric_columns"]) > 1:
        numeric_df = df[features["numeric_columns"]]
        corr_matrix = numeric_df.corr()
        analysis["correlations"] = corr_matrix.to_dict()
        
        # Create correlation heatmap
        fig_heatmap = px.imshow(
            corr_matrix,
            title="相关性热力图",
            color_continuous_scale="RdBu"
        )
        analysis["visualizations"]["correlation_heatmap"] = fig_heatmap
        
        # Create radar chart for top correlated features
        top_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                if abs(corr_matrix.iloc[i,j]) > 0.3:
                    top_correlations.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_matrix.iloc[i,j]
                    ))
        
        if top_correlations:
            fig_radar = go.Figure()
            for col1, col2, corr in top_correlations:
                fig_radar.add_trace(go.Scatterpolar(
                    r=[df[col1].mean(), df[col2].mean()],
                    theta=[col1, col2],
                    fill='toself',
                    name=f"{col1}-{col2}"
                ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(df[col].mean() for col in features["numeric_columns"]) * 1.2]
                    )
                ),
                title="相关性雷达图"
            )
            analysis["visualizations"]["correlation_radar"] = fig_radar
    
    # Analyze trends if there are date columns
    if features["date_columns"]:
        for date_col in features["date_columns"]:
            for num_col in features["numeric_columns"]:
                trend = df.groupby(date_col)[num_col].mean()
                analysis["trends"][f"{date_col}_{num_col}"] = trend.to_dict()
                
                # Create trend line chart
                fig_trend = px.line(
                    x=trend.index,
                    y=trend.values,
                    title=f"{num_col}随时间变化趋势"
                )
                analysis["visualizations"][f"{date_col}_{num_col}_trend"] = fig_trend
    
    return analysis

# File selection
st.header("选择评估方案")
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.info("请先在数据配置页面上传文件")
else:
    selected_file = st.selectbox(
        "选择要分析的文件",
        [f.name for f in existing_files]
    )
    
    if selected_file:
        try:
            # Load the Excel file
            file_path = UPLOAD_DIR / selected_file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Sheet selection
            if len(sheet_names) > 1:
                selected_sheet = st.selectbox(
                    "选择工作表",
                    sheet_names
                )
                df = pd.read_excel(file_path, sheet_name=selected_sheet)
            else:
                df = pd.read_excel(file_path)
            
            # Load and analyze data features
            features = load_data_features(selected_file)
            if features:
                analysis = analyze_data(df, features)
                
                # Display analysis results
                st.header("数据分析结果")
                
                # Create tabs for different visualization types
                tab1, tab2, tab3, tab4 = st.tabs(["基础分析", "柱状图", "雷达图", "趋势图"])
                
                with tab1:
                    # Numeric columns analysis
                    if analysis["numeric_analysis"]:
                        st.subheader("数值型指标分析")
                        for col, data in analysis["numeric_analysis"].items():
                            st.write(f"### {col}")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("最小值", f"{data['summary']['min']:.2f}")
                            with col2:
                                st.metric("最大值", f"{data['summary']['max']:.2f}")
                            with col3:
                                st.metric("平均值", f"{data['summary']['mean']:.2f}")
                            with col4:
                                st.metric("标准差", f"{data['summary']['std']:.2f}")
                    
                    # Categorical columns analysis
                    if analysis["categorical_analysis"]:
                        st.subheader("类别型指标分析")
                        for col, data in analysis["categorical_analysis"].items():
                            st.write(f"### {col}")
                            st.write(f"唯一值数量: {data['unique_values']}")
                            st.write("最常见值:")
                            for value, count in data["most_common"].items():
                                st.write(f"- {value}: {count}次")
                    
                    # Display Mermaid chart
                    st.subheader("数据关系图")
                    mermaid_code = create_mermaid_chart(df, features)
                    st.graphviz_chart(mermaid_code)
                
                with tab2:
                    # Display bar charts
                    if analysis["visualizations"]:
                        st.subheader("柱状图分析")
                        for viz_name, fig in analysis["visualizations"].items():
                            if viz_name.endswith("_bar"):
                                st.plotly_chart(fig, use_container_width=True)
                
                with tab3:
                    # Display radar charts
                    if "correlation_radar" in analysis["visualizations"]:
                        st.subheader("雷达图分析")
                        st.plotly_chart(analysis["visualizations"]["correlation_radar"], use_container_width=True)
                    
                    # Display correlation heatmap
                    if "correlation_heatmap" in analysis["visualizations"]:
                        st.subheader("相关性热力图")
                        st.plotly_chart(analysis["visualizations"]["correlation_heatmap"], use_container_width=True)
                
                with tab4:
                    # Display trend charts
                    if analysis["visualizations"]:
                        st.subheader("趋势分析")
                        for viz_name, fig in analysis["visualizations"].items():
                            if viz_name.endswith("_trend"):
                                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("未找到数据特征信息，请先在数据配置页面分析数据")
                
        except Exception as e:
            st.error(f"处理数据时出错: {str(e)}") 