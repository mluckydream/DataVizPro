import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import numpy as np

# Page config
st.set_page_config(
    page_title="方案对比分析",
    page_icon="⚖️",
    layout="wide"
)

# Title
st.title("⚖️ 方案对比分析")

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
        try:
            # Load data
            df1 = load_scheme_data(UPLOAD_DIR / scheme1)
            df2 = load_scheme_data(UPLOAD_DIR / scheme2)
            
            # Calculate total scores
            total_score1 = np.average(
                df1['得分'].dropna(),
                weights=df1.loc[df1['得分'].notna(), '权重']
            )
            total_score2 = np.average(
                df2['得分'].dropna(),
                weights=df2.loc[df2['得分'].notna(), '权重']
            )
            
            # Summary metrics
            st.header("方案对比摘要")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    f"{scheme1} 总分",
                    f"{total_score1:.1f}",
                    f"{total_score1 - total_score2:.1f}"
                )
            with col2:
                st.metric(
                    f"{scheme2} 总分",
                    f"{total_score2:.1f}",
                    f"{total_score2 - total_score1:.1f}"
                )
            with col3:
                st.metric(
                    "总分差异",
                    f"{abs(total_score1 - total_score2):.1f}",
                    "↑" if total_score1 > total_score2 else "↓"
                )
            
            # Merge data for comparison
            df1['方案'] = scheme1
            df2['方案'] = scheme2
            merged_df = pd.concat([df1, df2])
            
            # Status comparison
            st.header("指标状态对比")
            status_counts = pd.crosstab(
                merged_df['方案'],
                merged_df['状态']
            )
            fig_status = px.bar(
                status_counts,
                title="方案指标状态分布对比",
                barmode="group"
            )
            st.plotly_chart(fig_status, use_container_width=True)
            
            # Detailed comparison
            st.header("详细指标对比")
            
            # Create comparison dataframe
            comparison_data = []
            all_indicators = set(df1['指标名称'].unique()) | set(df2['指标名称'].unique())
            
            for indicator in all_indicators:
                row1 = df1[df1['指标名称'] == indicator].iloc[0] if indicator in df1['指标名称'].values else None
                row2 = df2[df2['指标名称'] == indicator].iloc[0] if indicator in df2['指标名称'].values else None
                
                comparison_data.append({
                    '指标名称': indicator,
                    f'{scheme1}_指标值': row1['指标值'] if row1 is not None else None,
                    f'{scheme1}_得分': row1['得分'] if row1 is not None else None,
                    f'{scheme1}_状态': row1['状态'] if row1 is not None else None,
                    f'{scheme2}_指标值': row2['指标值'] if row2 is not None else None,
                    f'{scheme2}_得分': row2['得分'] if row2 is not None else None,
                    f'{scheme2}_状态': row2['状态'] if row2 is not None else None,
                    '得分差异': (row1['得分'] if row1 is not None else 0) - (row2['得分'] if row2 is not None else 0)
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.dataframe(comparison_df, use_container_width=True)
            
            # Score comparison visualization
            st.header("得分对比可视化")
            
            # Select indicators to compare
            selected_indicators = st.multiselect(
                "选择要对比的指标",
                comparison_df['指标名称'].tolist(),
                default=comparison_df['指标名称'].tolist()[:5]
            )
            
            if selected_indicators:
                # Filter data for selected indicators
                plot_df = comparison_df[comparison_df['指标名称'].isin(selected_indicators)]
                
                # Create comparison bar chart
                fig_comparison = px.bar(
                    plot_df,
                    x='指标名称',
                    y=[f'{scheme1}_得分', f'{scheme2}_得分'],
                    title="指标得分对比",
                    barmode="group"
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # Create radar chart
                radar_data = []
                for indicator in selected_indicators:
                    row = comparison_df[comparison_df['指标名称'] == indicator].iloc[0]
                    radar_data.extend([
                        {'指标': indicator, '方案': scheme1, '得分': row[f'{scheme1}_得分']},
                        {'指标': indicator, '方案': scheme2, '得分': row[f'{scheme2}_得分']}
                    ])
                
                radar_df = pd.DataFrame(radar_data)
                fig_radar = px.line_polar(
                    radar_df,
                    r='得分',
                    theta='指标',
                    color='方案',
                    line_close=True,
                    title="指标雷达图对比"
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            
        except Exception as e:
            st.error(f"处理数据时出错: {str(e)}")
            st.error("请确保数据文件包含所需的列：指标名称、指标值、权重、评分标准_及格线、评分标准_优秀线、单位") 