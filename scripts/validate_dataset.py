#!/usr/bin/env python3
"""验证 LLaMA Factory 数据集配置的正确性

功能：
  - 验证 dataset_info.json 的格式
  - 验证 JSONL 数据文件的有效性
  - 计算数据集统计信息
  - 显示数据样本
"""

import json
import os
import sys
from pathlib import Path

# 确保项目路径可用
_here = os.path.abspath(os.path.dirname(__file__))
_project_root = os.path.abspath(os.path.join(_here, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def validate_dataset_info(config_path: str) -> bool:
    """验证 dataset_info.json 格式"""
    print(f'验证 dataset_info.json 格式...')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查必需字段
        for dataset_name, dataset_config in config.items():
            required_fields = ['file_name', 'formatting', 'columns']
            for field in required_fields:
                if field not in dataset_config:
                    print(f'✗ 缺少字段: {field}')
                    return False
            
            # 检查 columns 结构
            if not isinstance(dataset_config['columns'], dict):
                print(f'✗ columns 应该是字典')
                return False
            
            # 必需字段：prompt 和 response。query 是可选的。
            required_columns = ['prompt', 'response']
            for col in required_columns:
                if col not in dataset_config['columns']:
                    print(f'✗ columns 中缺少字段: {col}')
                    return False
        
        print(f'✓ dataset_info.json 格式正确')
        return True
        
    except Exception as e:
        print(f'✗ 验证失败: {e}')
        return False


def validate_data_file(file_path: str, dataset_name: str, column_mapping: dict, sample_size: int = 5) -> tuple:
    """
    验证数据文件（支持 JSON 数组和 JSONL 格式）
    
    返回: (valid, total_records, valid_records, sample_records)
    """
    print(f'\n验证 {dataset_name} 数据文件...')
    
    try:
        total_records = 0
        valid_records = 0
        sample_records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
            if content.startswith('['):
                # 处理标准 JSON 数组
                try:
                    data = json.loads(content)
                    if not isinstance(data, list):
                        print(f'✗ JSON 格式错误: 根节点不是数组')
                        return False, 0, 0, []
                    
                    total_records = len(data)
                    # 只有在 mapping 中定义的列才视为必需
                    source_cols = [v for k, v in column_mapping.items() if v]
                    
                    for idx, record in enumerate(data):
                        if all(col in record for col in source_cols):
                            valid_records += 1
                            if len(sample_records) < sample_size:
                                sample_records.append(record)
                        else:
                            if valid_records < 3: # 减少大文件的报错输出
                                missing = [col for col in source_cols if col not in record]
                                print(f'  记录 {idx}: 缺少字段 {missing}')
                except json.JSONDecodeError as e:
                    print(f'✗ JSON 解析失败: {e}')
                    return False, 0, 0, []
            else:
                # 处理 JSONL
                f.seek(0)
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    total_records += 1
                    try:
                        record = json.loads(line)
                        # 只有在 mapping 中定义的列才视为必需
                        source_cols = [v for k, v in column_mapping.items() if v]
                        if all(col in record for col in source_cols):
                            valid_records += 1
                            if len(sample_records) < sample_size:
                                sample_records.append(record)
                        else:
                            if valid_records < 3:
                                missing = [col for col in source_cols if col not in record]
                                print(f'  行 {line_num}: 缺少字段 {missing}')
                    except json.JSONDecodeError as e:
                        print(f'  行 {line_num}: JSON 格式错误 - {e}')
        
        if total_records == 0:
            print(f'✗ 文件为空或无有效记录')
            return False, 0, 0, []
        
        valid_ratio = valid_records / total_records * 100
        print(f'✓ 验证完成: {valid_records:,}/{total_records:,} 条有效记录 ({valid_ratio:.1f}%)')
        return valid_records > 0, total_records, valid_records, sample_records
        
    except Exception as e:
        print(f'✗ 验证失败: {e}')
        return False, 0, 0, []


def show_sample_data(samples: list, column_mapping: dict):
    """显示数据样本"""
    if not samples:
        return
    
    print(f'\n数据样本 (前 {len(samples)} 条):')
    print('=' * 80)
    
    for i, sample in enumerate(samples, 1):
        print(f'\n【样本 {i}】')
        # 使用 .get 处理可能缺失的映射键
        prompt_key = column_mapping.get("prompt")
        query_key = column_mapping.get("query")
        response_key = column_mapping.get("response")
        
        print(f'指令: {sample.get(prompt_key, "N/A")[:100] if prompt_key else "N/A"}...')
        print(f'输入: {sample.get(query_key, "N/A")[:100] if query_key else "N/A"}...')
        print(f'输出: {sample.get(response_key, "N/A")[:100] if response_key else "N/A"}...')
    
    print('\n' + '=' * 80)


def main():
    """主函数"""
    data_dir = os.path.join(_project_root, 'data')
    config_path = os.path.join(data_dir, 'dataset_info.json')
    
    print(f'LLaMA Factory 数据集验证工具')
    print(f'数据目录: {data_dir}\n')
    
    # 验证配置文件
    if not validate_dataset_info(config_path):
        return 1
    
    # 读取配置
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 验证每个数据集文件
    for dataset_name, dataset_config in config.items():
        file_name = dataset_config['file_name']
        jsonl_path = os.path.join(data_dir, file_name)
        
        if not os.path.exists(jsonl_path):
            print(f'\n✗ 文件不存在: {jsonl_path}')
            continue
        
        # 验证文件格式
        valid, total, valid_records, samples = validate_data_file(
            jsonl_path,
            dataset_name,
            dataset_config['columns'],
            sample_size=3
        )
        
        if not valid:
            print(f'✗ {dataset_name} 验证失败')
            return 1
        
        # 显示样本
        show_sample_data(samples, dataset_config['columns'])
        
        # 显示统计信息
        print(f'\n数据集统计:')
        print(f'  文件: {file_name}')
        print(f'  格式: {dataset_config["formatting"]}')
        print(f'  总记录数: {total:,}')
        print(f'  有效记录: {valid_records:,}')
        print(f'  标签: {", ".join(dataset_config.get("tags", []))}')
    
    print(f'\n{"="*80}')
    print(f'✓ 所有验证通过！数据集已准备好在 LLaMA Factory 中使用')
    print(f'{"="*80}')
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
