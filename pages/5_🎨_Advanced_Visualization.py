import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Page config
st.set_page_config(
    page_title="高级可视化分析",
    page_icon="🎨",
    layout="wide"
)

# Title
st.title("🎨 高级可视化分析")

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

def create_advanced_visualizations(df, features):
    """Create advanced visualizations based on data features"""
    visualizations = {}
    
    # PCA Analysis
    if len(features["numeric_columns"]) > 1:
        # Prepare data
        numeric_data = df[features["numeric_columns"]].dropna()
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(numeric_data)
        
        # Perform PCA
        pca = PCA(n_components=min(3, len(features["numeric_columns"])))
        pca_result = pca.fit_transform(scaled_data)
        
        # Create 2D PCA plot
        fig_2d = px.scatter(
            x=pca_result[:, 0],
            y=pca_result[:, 1],
            title="PCA 2D 投影",
            labels={'x': '主成分1', 'y': '主成分2'}
        )
        visualizations["pca_2d"] = fig_2d
        
        # Create 3D PCA plot if possible
        if pca_result.shape[1] > 2:
            fig_3d = px.scatter_3d(
                x=pca_result[:, 0],
                y=pca_result[:, 1],
                z=pca_result[:, 2],
                title="PCA 3D 投影",
                labels={'x': '主成分1', 'y': '主成分2', 'z': '主成分3'}
            )
            visualizations["pca_3d"] = fig_3d
        
        # Create explained variance plot
        explained_variance = pca.explained_variance_ratio_
        fig_variance = go.Figure()
        fig_variance.add_trace(go.Bar(
            x=[f"PC{i+1}" for i in range(len(explained_variance))],
            y=explained_variance,
            text=[f"{v:.1%}" for v in explained_variance],
            textposition="auto",
        ))
        fig_variance.update_layout(
            title="主成分解释方差比例",
            xaxis_title="主成分",
            yaxis_title="解释方差比例"
        )
        visualizations["pca_variance"] = fig_variance
    
    # Correlation Network
    if len(features["numeric_columns"]) > 1:
        corr_matrix = df[features["numeric_columns"]].corr()
        threshold = 0.5  # Only show correlations above threshold
        
        # Create network graph
        fig_network = go.Figure()
        
        # Add edges
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr = corr_matrix.iloc[i, j]
                if abs(corr) > threshold:
                    fig_network.add_trace(go.Scatter(
                        x=[i, j],
                        y=[0, 0],
                        mode='lines',
                        line=dict(
                            width=abs(corr) * 5,
                            color='red' if corr < 0 else 'blue'
                        ),
                        hoverinfo='text',
                        text=f"相关系数: {corr:.2f}"
                    ))
        
        # Add nodes
        fig_network.add_trace(go.Scatter(
            x=list(range(len(corr_matrix.columns))),
            y=[0] * len(corr_matrix.columns),
            mode='markers+text',
            marker=dict(size=20),
            text=corr_matrix.columns,
            textposition="top center"
        ))
        
        fig_network.update_layout(
            title="相关性网络图",
            showlegend=False,
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False)
        )
        visualizations["correlation_network"] = fig_network
    
    # Scatter Matrix
    if len(features["numeric_columns"]) > 1:
        fig_matrix = px.scatter_matrix(
            df,
            dimensions=features["numeric_columns"][:5],  # Limit to 5 dimensions for clarity
            title="散点矩阵图"
        )
        visualizations["scatter_matrix"] = fig_matrix
    
    # Parallel Coordinates
    if len(features["numeric_columns"]) > 1:
        fig_parallel = px.parallel_coordinates(
            df,
            dimensions=features["numeric_columns"][:5],  # Limit to 5 dimensions for clarity
            title="平行坐标图"
        )
        visualizations["parallel_coordinates"] = fig_parallel
    
    return visualizations

# File selection
st.header("选择要分析的文件")
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.info("请先在数据配置页面上传文件")
else:
    selected_file = st.selectbox(
        "选择文件",
        [f.name for f in existing_files]
    )
    
    if selected_file:
        try:
            # Load Excel file
            df = pd.read_excel(UPLOAD_DIR / selected_file)
            
            # Load data features
            features = load_data_features(selected_file)
            
            if features:
                # Create visualizations
                visualizations = create_advanced_visualizations(df, features)
                
                # Display visualizations
                st.header("高级可视化分析结果")
                
                # Create tabs for different visualization types
                tab1, tab2, tab3, tab4 = st.tabs(["PCA分析", "相关性网络", "散点矩阵", "平行坐标"])
                
                with tab1:
                    if "pca_2d" in visualizations:
                        st.plotly_chart(visualizations["pca_2d"], use_container_width=True)
                    if "pca_3d" in visualizations:
                        st.plotly_chart(visualizations["pca_3d"], use_container_width=True)
                    if "pca_variance" in visualizations:
                        st.plotly_chart(visualizations["pca_variance"], use_container_width=True)
                
                with tab2:
                    if "correlation_network" in visualizations:
                        st.plotly_chart(visualizations["correlation_network"], use_container_width=True)
                
                with tab3:
                    if "scatter_matrix" in visualizations:
                        st.plotly_chart(visualizations["scatter_matrix"], use_container_width=True)
                
                with tab4:
                    if "parallel_coordinates" in visualizations:
                        st.plotly_chart(visualizations["parallel_coordinates"], use_container_width=True)
            
            else:
                st.warning("未找到数据特征信息，请先在数据配置页面分析数据")
            
        except Exception as e:
            st.error(f"处理数据时出错: {str(e)}") 