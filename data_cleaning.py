import pandas as pd
import numpy as np
from pathlib import Path
import json
import argparse
from datetime import datetime

def load_data_features(file_name):
    """Load data features from JSON file"""
    features_file = Path(__file__).parent / "data" / "features" / f"{file_name}.json"
    if features_file.exists():
        with open(features_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_sample_data(features, num_rows=100):
    """
    根据特征配置生成示例数据
    
    Args:
        features (dict): 数据特征配置
        num_rows (int): 生成的行数
    
    Returns:
        pd.DataFrame: 生成的示例数据
    """
    data = {}
    
    # 生成数值列数据
    for col in features.get("numeric_columns", []):
        data[col] = np.random.normal(100, 20, num_rows)
    
    # 生成类别列数据
    for col in features.get("categorical_columns", []):
        categories = features.get("special_categories", {}).get(col, {}).get("values", ["A", "B", "C"])
        data[col] = np.random.choice(categories, num_rows)
    
    return pd.DataFrame(data)

def clean_and_simulate_data(input_file, output_file, features=None, generate_new=False):
    """
    清洗和模拟数据
    
    Args:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径
        features (dict, optional): 数据特征配置
        generate_new (bool): 是否生成新数据
    """
    try:
        if generate_new:
            if features is None:
                raise ValueError("生成新数据需要特征配置")
            df = generate_sample_data(features)
        else:
            # 读取Excel文件
            df = pd.read_excel(input_file)
            
            # 如果没有提供特征配置，尝试从文件名加载
            if features is None:
                file_name = Path(input_file).stem
                features = load_data_features(file_name)
            
            if features is None:
                raise ValueError("无法加载数据特征配置")
        
        # 获取数值列和类别列
        numeric_columns = features.get("numeric_columns", [])
        categorical_columns = features.get("categorical_columns", [])
        
        # 清洗规则1：处理缺失值
        # 对数值列用0填充
        df[numeric_columns] = df[numeric_columns].fillna(0)
        # 对类别列用"未知"填充
        df[categorical_columns] = df[categorical_columns].fillna("未知")
        
        # 清洗规则2：去除重复记录
        df = df.drop_duplicates()
        
        # 数据模拟规则1：对数值列添加随机扰动（±5%）
        np.random.seed(42)  # 保证可重复性
        for col in numeric_columns:
            df[col] = df[col].apply(
                lambda x: x * np.random.uniform(0.95, 1.05) if x != 0 else 0
            )
        
        # 数据模拟规则2：对特定类别添加额外波动
        special_categories = features.get("special_categories", {})
        for category, columns in special_categories.items():
            if category in categorical_columns:
                mask = df[category].isin(columns.get("values", []))
                for col in numeric_columns:
                    df.loc[mask, col] = df.loc[mask, col].apply(
                        lambda x: x * np.random.uniform(0.9, 1.1) if x != 0 else 0
                    )
        
        # 清洗规则3：确保数据类型
        # 数值列转换为float64
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float64')
        
        # 类别列转换为string
        for col in categorical_columns:
            df[col] = df[col].astype('string')
        
        # 清洗规则4：处理异常值
        # 对数值列进行异常值处理（超过3个标准差的值视为异常值）
        for col in numeric_columns:
            mean = df[col].mean()
            std = df[col].std()
            df.loc[df[col] > mean + 3*std, col] = mean + 3*std
            df.loc[df[col] < mean - 3*std, col] = mean - 3*std
        
        # 保存清洗后的数据
        df.to_excel(output_file, index=False)
        print(f"数据{'生成并' if generate_new else '清洗'}完成，已保存到 {output_file}")
        
        # 返回清洗后的数据框
        return df
        
    except Exception as e:
        print(f"数据处理过程中出错: {str(e)}")
        return None

def process_specific_file(input_file, output_file=None, generate_new=False):
    """
    处理指定的Excel文件
    
    Args:
        input_file (str): 要处理的文件名（不需要包含路径）
        output_file (str, optional): 输出文件名，如果不指定则自动生成
        generate_new (bool): 是否生成新数据
    """
    # 获取上传文件目录
    upload_dir = Path(__file__).parent / "data" / "uploaded_excel"
    output_dir = Path(__file__).parent / "data" / "cleaned_excel"
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 构建完整的输入文件路径
    input_path = upload_dir / input_file
    
    if not generate_new and not input_path.exists():
        print(f"错误：文件 {input_file} 不存在于 {upload_dir} 目录中")
        return
    
    # 如果没有指定输出文件名，则生成一个带时间戳的文件名
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = Path(input_file).stem
        output_file = f"{file_stem}_cleaned_{timestamp}.xlsx"
    
    # 构建完整的输出文件路径
    output_path = output_dir / output_file
    
    # 加载数据特征
    features = load_data_features(input_path.stem)
    
    # 清洗数据
    clean_and_simulate_data(str(input_path), str(output_path), features, generate_new)

def list_available_files():
    """列出所有可用的Excel文件"""
    upload_dir = Path(__file__).parent / "data" / "uploaded_excel"
    excel_files = list(upload_dir.glob("*.xlsx")) + list(upload_dir.glob("*.xls"))
    
    if not excel_files:
        print("没有找到可用的Excel文件")
        return
    
    print("\n可用的Excel文件：")
    for i, file in enumerate(excel_files, 1):
        print(f"{i}. {file.name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据清洗和模拟工具')
    parser.add_argument('--file', type=str, help='指定要处理的文件名')
    parser.add_argument('--output', type=str, help='指定输出文件名（可选）')
    parser.add_argument('--list', action='store_true', help='列出所有可用的文件')
    parser.add_argument('--generate', action='store_true', help='生成新的示例数据')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_files()
    elif args.file:
        process_specific_file(args.file, args.output, args.generate)
    else:
        print("请指定操作：")
        print("  --list     列出所有可用的文件")
        print("  --file     指定要处理的文件名")
        print("  --output   指定输出文件名（可选）")
        print("  --generate 生成新的示例数据") 