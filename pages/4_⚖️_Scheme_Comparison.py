import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import numpy as np

# Page config
st.set_page_config(
    page_title="方案对比分析",
    page_icon="⚖️",
    layout="wide"
)

# Title
st.title("⚖️ 方案对比分析")

def load_data_features(file_name):
    """Load data features from JSON file"""
    # Remove .xlsx extension if present
    file_stem = Path(file_name).stem
    
    # Check if this is a cleaned file
    if "_cleaned_" in file_stem:
        # Extract original file name
        original_name = file_stem.split("_cleaned_")[0]
        features_file = Path(__file__).parent.parent / "data" / "features" / f"{original_name}.json"
    else:
        features_file = Path(__file__).parent.parent / "data" / "features" / f"{file_stem}.json"
    
    if features_file.exists():
        with open(features_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    st.error(f"无法加载特征配置文件: {features_file.name}")
    return None

def load_excel_file(file_path):
    """Load Excel file with proper data type conversion"""
    try:
        df = pd.read_excel(file_path)
        return df
    except Exception as e:
        st.error(f"加载文件时出错: {str(e)}")
        return None

def compare_schemes(df1, df2, features1, features2):
    """Compare two schemes and return comparison results"""
    comparison = {
        "numeric_comparison": {},
        "categorical_comparison": {},
        "correlation_comparison": {}
    }
    
    # Get common numeric columns
    common_numeric_cols = set.intersection(
        set(features1["numeric_columns"]),
        set(features2["numeric_columns"])
    )
    
    # Get common categorical columns
    common_categorical_cols = set.intersection(
        set(features1["categorical_columns"]),
        set(features2["categorical_columns"])
    )
    
    # Numeric comparison
    for col in common_numeric_cols:
        comparison["numeric_comparison"][col] = {
            "scheme1": {
                "mean": df1[col].mean(),
                "std": df1[col].std(),
                "min": df1[col].min(),
                "max": df1[col].max(),
                "median": df1[col].median()
            },
            "scheme2": {
                "mean": df2[col].mean(),
                "std": df2[col].std(),
                "min": df2[col].min(),
                "max": df2[col].max(),
                "median": df2[col].median()
            },
            "difference": {
                "mean_diff": df2[col].mean() - df1[col].mean(),
                "std_diff": df2[col].std() - df1[col].std(),
                "min_diff": df2[col].min() - df1[col].min(),
                "max_diff": df2[col].max() - df1[col].max(),
                "median_diff": df2[col].median() - df1[col].median()
            }
        }
    
    # Categorical comparison
    for col in common_categorical_cols:
        comparison["categorical_comparison"][col] = {
            "scheme1": df1[col].value_counts().to_dict(),
            "scheme2": df2[col].value_counts().to_dict()
        }
    
    # Correlation comparison
    numeric_cols1 = features1["numeric_columns"]
    numeric_cols2 = features2["numeric_columns"]
    
    if numeric_cols1 and numeric_cols2:
        corr1 = df1[numeric_cols1].corr()
        corr2 = df2[numeric_cols2].corr()
        
        # Get common columns for correlation comparison
        common_cols = list(set(numeric_cols1) & set(numeric_cols2))
        if common_cols:
            corr1 = corr1.loc[common_cols, common_cols]
            corr2 = corr2.loc[common_cols, common_cols]
            comparison["correlation_comparison"] = {
                "corr1": corr1.to_dict(),
                "corr2": corr2.to_dict(),
                "corr_diff": (corr2 - corr1).to_dict()
            }
    
    return comparison

# Get uploaded files
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploaded_excel"
existing_files = list(UPLOAD_DIR.glob("*.xlsx")) + list(UPLOAD_DIR.glob("*.xls"))

if not existing_files:
    st.warning("请先在数据配置页面上传文件")
else:
    # File selection
    col1, col2 = st.columns(2)
    
    with col1:
        scheme1 = st.selectbox(
            "选择方案A",
            [f.name for f in existing_files],
            key="scheme1"
        )
    
    with col2:
        scheme2 = st.selectbox(
            "选择方案B",
            [f.name for f in existing_files if f.name != scheme1],
            key="scheme2"
        )
    
    if scheme1 and scheme2:
        # Load files and features
        df1 = load_excel_file(UPLOAD_DIR / scheme1)
        df2 = load_excel_file(UPLOAD_DIR / scheme2)
        
        if df1 is not None and df2 is not None:
            features1 = load_data_features(scheme1)
            features2 = load_data_features(scheme2)
            
            if features1 and features2:
                # Compare schemes
                comparison = compare_schemes(df1, df2, features1, features2)
                
                # Create tabs for different comparison types
                tab1, tab2, tab3 = st.tabs(["数值对比", "类别对比", "相关性对比"])
                
                with tab1:
                    st.header("数值指标对比")
                    
                    if comparison["numeric_comparison"]:
                        # Select metrics to compare
                        selected_metrics = st.multiselect(
                            "选择要对比的指标",
                            list(comparison["numeric_comparison"].keys()),
                            default=list(comparison["numeric_comparison"].keys())[:3] if len(comparison["numeric_comparison"]) >= 3 else list(comparison["numeric_comparison"].keys())
                        )
                        
                        if selected_metrics:
                            # Create comparison plot
                            fig = go.Figure()
                            
                            for metric in selected_metrics:
                                comp = comparison["numeric_comparison"][metric]
                                
                                # Add bars for scheme1
                                fig.add_trace(go.Bar(
                                    name=f"{Path(scheme1).stem} - {metric}",
                                    x=[metric],
                                    y=[comp["scheme1"]["mean"]],
                                    error_y=dict(
                                        type='data',
                                        array=[comp["scheme1"]["std"]],
                                        visible=True
                                    )
                                ))
                                
                                # Add bars for scheme2
                                fig.add_trace(go.Bar(
                                    name=f"{Path(scheme2).stem} - {metric}",
                                    x=[metric],
                                    y=[comp["scheme2"]["mean"]],
                                    error_y=dict(
                                        type='data',
                                        array=[comp["scheme2"]["std"]],
                                        visible=True
                                    )
                                ))
                            
                            fig.update_layout(
                                title="指标均值对比",
                                barmode='group',
                                showlegend=True
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Display detailed comparison
                            st.subheader("详细对比")
                            comparison_data = []
                            
                            for metric in selected_metrics:
                                comp = comparison["numeric_comparison"][metric]
                                comparison_data.append({
                                    "指标": metric,
                                    f"{Path(scheme1).stem}均值": f"{comp['scheme1']['mean']:.2f}",
                                    f"{Path(scheme1).stem}标准差": f"{comp['scheme1']['std']:.2f}",
                                    f"{Path(scheme2).stem}均值": f"{comp['scheme2']['mean']:.2f}",
                                    f"{Path(scheme2).stem}标准差": f"{comp['scheme2']['std']:.2f}",
                                    "均值差异": f"{comp['difference']['mean_diff']:.2f}",
                                    "标准差差异": f"{comp['difference']['std_diff']:.2f}"
                                })
                            
                            st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                    else:
                        st.warning("未找到可对比的数值型指标")
                
                with tab2:
                    st.header("类别指标对比")
                    
                    if comparison["categorical_comparison"]:
                        # Select categorical columns to compare
                        selected_cats = st.multiselect(
                            "选择要对比的类别指标",
                            list(comparison["categorical_comparison"].keys()),
                            default=list(comparison["categorical_comparison"].keys())[:2] if len(comparison["categorical_comparison"]) >= 2 else list(comparison["categorical_comparison"].keys())
                        )
                        
                        if selected_cats:
                            for cat in selected_cats:
                                st.subheader(f"{cat} 分布对比")
                                
                                # Create comparison plot
                                fig = go.Figure()
                                
                                # Get all unique categories
                                all_cats = set(comparison["categorical_comparison"][cat]["scheme1"].keys()) | set(comparison["categorical_comparison"][cat]["scheme2"].keys())
                                
                                # Add bars for scheme1
                                fig.add_trace(go.Bar(
                                    name=Path(scheme1).stem,
                                    x=list(all_cats),
                                    y=[comparison["categorical_comparison"][cat]["scheme1"].get(c, 0) for c in all_cats]
                                ))
                                
                                # Add bars for scheme2
                                fig.add_trace(go.Bar(
                                    name=Path(scheme2).stem,
                                    x=list(all_cats),
                                    y=[comparison["categorical_comparison"][cat]["scheme2"].get(c, 0) for c in all_cats]
                                ))
                                
                                fig.update_layout(
                                    title=f"{cat} 分布对比",
                                    barmode='group',
                                    showlegend=True
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Display detailed comparison
                                st.subheader("详细对比")
                                comparison_data = []
                                
                                for cat_value in all_cats:
                                    count1 = comparison["categorical_comparison"][cat]["scheme1"].get(cat_value, 0)
                                    count2 = comparison["categorical_comparison"][cat]["scheme2"].get(cat_value, 0)
                                    comparison_data.append({
                                        "类别": cat_value,
                                        f"{Path(scheme1).stem}数量": count1,
                                        f"{Path(scheme2).stem}数量": count2,
                                        "数量差异": count2 - count1
                                    })
                                
                                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                    else:
                        st.warning("未找到可对比的类别型指标")
                
                with tab3:
                    st.header("相关性对比")
                    
                    if comparison["correlation_comparison"]:
                        # Select metrics for correlation comparison
                        corr1 = pd.DataFrame(comparison["correlation_comparison"]["corr1"])
                        corr2 = pd.DataFrame(comparison["correlation_comparison"]["corr2"])
                        corr_diff = pd.DataFrame(comparison["correlation_comparison"]["corr_diff"])
                        
                        # Create heatmap for correlation difference
                        fig = go.Figure(data=go.Heatmap(
                            z=corr_diff.values,
                            x=corr_diff.columns,
                            y=corr_diff.index,
                            colorscale='RdBu',
                            zmid=0
                        ))
                        
                        fig.update_layout(
                            title="相关性差异热力图",
                            xaxis_title="指标",
                            yaxis_title="指标"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Display detailed correlation comparison
                        st.subheader("详细相关性对比")
                        st.dataframe(corr_diff, use_container_width=True)
                    else:
                        st.warning("未找到可对比的相关性数据")
            else:
                st.error("无法加载数据特征配置，请确保特征配置文件存在且格式正确")
        else:
            st.error("无法加载文件，请确保文件存在且格式正确") 