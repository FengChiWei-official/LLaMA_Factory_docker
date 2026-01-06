#!/usr/bin/env python3
"""Build dataset JSON from CSV files with UTF-8 validation and optional merges."""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


# Ensure project root is importable
_here = os.path.abspath(os.path.dirname(__file__))
_project_root = os.path.abspath(os.path.join(_here, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


UTF8_ALIASES = {
    'utf-8',
    'utf8',
    'utf-8-sig',
    'utf8sig',
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Convert CSV datasets to JSON with encoding checks and optional merges.')
    parser.add_argument('--input-dir', default=os.path.join(_project_root, 'raw_dataset', 'csvs', 'medical_ds'), help='CSV root directory to scan recursively.')
    parser.add_argument('--template', default=os.path.join(_project_root, 'raw_dataset', 'templates', 'medical_ds_template.json'), help='Template JSON file for field mapping.')
    parser.add_argument('--output', default=os.path.join(_project_root, 'data', 'medical_ds_cleaned.json'), help='Path for the generated JSON dataset.')
    parser.add_argument('--log-file', default=os.path.join(_project_root, 'data', 'processing_log.txt'), help='Log file to write progress.')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (default: ,).')
    parser.add_argument('--extra-json', nargs='*', default=[], help='Optional extra JSON/JSONL files to append. Use name:path to override dataset name.')
    parser.add_argument('--dataset-name', default='medical_ds_cleaned', help='Name to register for the generated dataset.')
    parser.add_argument('--write-dataset-info', action='store_true', help='Write a dataset_info file (default path data/dataset_info.generated.json).')
    parser.add_argument('--dataset-info-path', default=os.path.join(_project_root, 'data', 'dataset_info.generated.json'), help='Destination for generated dataset_info (will not overwrite unless --overwrite-dataset-info is set).')
    parser.add_argument('--overwrite-dataset-info', action='store_true', help='Allow overwriting the dataset_info destination.')
    parser.add_argument('--allow-non-utf8', action='store_true', help='Disable UTF-8 enforcement (not recommended).')
    return parser.parse_args()


def normalize_encoding(name: str) -> str:
    return (name or '').replace('-', '').lower()


def load_template(template_path: str) -> str:
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f'Template not found: {template_path}')
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def detect_file_encoding(file_path: str) -> str:
    with open(file_path, 'rb') as f:
        raw_data = f.read(10240)

    for enc in ['utf-8', 'gbk', 'gb18030', 'big5', 'iso-8859-1']:
        try:
            raw_data.decode(enc)
            return enc
        except Exception:
            continue
    return 'utf-8'


def ensure_utf8_file(path: str, repair_hint: str) -> str:
    detected = detect_file_encoding(path)
    if normalize_encoding(detected) not in UTF8_ALIASES:
        raise ValueError(f'{path} is {detected}, expected UTF-8. Please run {repair_hint} --root {os.path.dirname(path)}')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
    except UnicodeDecodeError as e:
        raise ValueError(f'{path} is not valid UTF-8: {e}. Please run {repair_hint} --root {os.path.dirname(path)}')
    return detected


def csv_to_json_objects(
    csv_path: str,
    template_str: str,
    delimiter: str = ',',
    encoding_hint: str = None,
    enforce_utf8: bool = True,
    repair_hint: str = 'scripts/repair_encodings.py',
):
    objects: List[Dict] = []
    errors = 0
    encoding_errors = []

    try:
        template_obj = json.loads(template_str)
    except json.JSONDecodeError as e:
        raise ValueError(f'Template is not valid JSON: {e}')

    if enforce_utf8:
        encodings_to_try = ['utf-8']
    else:
        candidates = [encoding_hint] if encoding_hint else []
        candidates.extend(['utf-8', 'gbk', 'gb18030', 'big5', 'iso-8859-1'])
        encodings_to_try = [e for e in candidates if e]

    file_opened = False
    used_encoding = None

    for enc in encodings_to_try:
        try:
            f = open(csv_path, 'r', encoding=enc, errors='strict' if enforce_utf8 else 'replace')
            reader = csv.DictReader(f, delimiter=delimiter)
            if reader.fieldnames is None:
                f.close()
                continue

            used_encoding = enc
            for row_idx, row in enumerate(reader, start=1):
                try:
                    output_obj = {}
                    for key, value_template in template_obj.items():
                        if isinstance(value_template, str):
                            output_obj[key] = value_template.format(**row)
                        else:
                            output_obj[key] = value_template
                    objects.append(output_obj)
                except KeyError as e:
                    print(f'[WARN] {csv_path} row {row_idx}: missing column {e}', file=sys.stderr)
                    errors += 1
                except Exception as e:
                    print(f'[WARN] {csv_path} row {row_idx}: {e}', file=sys.stderr)
                    errors += 1

            f.close()
            file_opened = True
            break
        except Exception as e:
            encoding_errors.append((enc, str(e)))
            continue

    if not file_opened:
        error_msg = f'Cannot decode file: {csv_path}\n'
        for enc, err in encoding_errors:
            error_msg += f'  [{enc}]: {err}\n'
        if enforce_utf8:
            error_msg += f'Please run {repair_hint} --root {os.path.dirname(csv_path)} to normalize encoding.'
        raise IOError(error_msg)

    if enforce_utf8 and used_encoding != 'utf-8':
        raise ValueError(f'{csv_path} is not UTF-8 after validation (used {used_encoding}). Please run {repair_hint} --root {os.path.dirname(csv_path)}')

    return objects, errors


def find_csv_files(input_dir: str) -> List[str]:
    if not os.path.isdir(input_dir):
        raise NotADirectoryError(f'Input directory does not exist: {input_dir}')

    csv_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    return sorted(csv_files)


def load_json_or_jsonl(path: str, enforce_utf8: bool, repair_hint: str) -> List[Dict]:
    if enforce_utf8:
        ensure_utf8_file(path, repair_hint)

    def _load_json_file() -> Tuple[bool, List[Dict]]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return True, data
        except json.JSONDecodeError:
            return False, []

    loaded_ok, data = _load_json_file()
    if loaded_ok:
        if not isinstance(data, list):
            raise ValueError(f'{path} is JSON but not a list of records')
        return data

    records = []
    with open(path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception as e:
                raise ValueError(f'{path} line {line_no} is not valid JSON: {e}')

    return records


def parse_extra_dataset_args(extra_args: Sequence[str]) -> List[Tuple[str, str]]:
    parsed: List[Tuple[str, str]] = []
    for item in extra_args:
        if ':' in item:
            name, path = item.split(':', 1)
        else:
            path = item
            name = Path(path).stem
        parsed.append((name, path))
    return parsed


def build_dataset_info(main_name: str, output_path: str, extra_entries: List[Tuple[str, str]]) -> Dict[str, Dict]:
    dataset_info = {
        main_name: {
            'file_name': os.path.basename(output_path),
            'columns': {
                'prompt': 'instruction',
                'query': 'input',
                'response': 'output',
            },
        }
    }

    for name, path in extra_entries:
        dataset_info[name] = {
            'file_name': os.path.basename(path),
            'columns': {
                'prompt': 'instruction',
                'query': 'input',
                'response': 'output',
            },
        }
    return dataset_info


def main() -> int:
    args = parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.log_file), exist_ok=True)

    log_f = open(args.log_file, 'w', encoding='utf-8')

    def log_message(msg: str, to_stderr: bool = False):
        print(msg)
        log_f.write(msg + '\n')
        log_f.flush()
        if to_stderr:
            print(msg, file=sys.stderr)

    log_message(f'输入目录: {args.input_dir}')
    log_message(f'输出文件: {args.output}')
    log_message(f'模板文件: {args.template}')
    log_message(f'日志文件: {args.log_file}')
    log_message('')

    if not os.path.isdir(args.input_dir):
        log_message(f'[ERR] 输入目录不存在: {args.input_dir}', to_stderr=True)
        log_f.close()
        return 1

    try:
        template = load_template(args.template)
        log_message('✓ 模板已加载')
    except FileNotFoundError as e:
        log_message(f'[ERR] {e}', to_stderr=True)
        log_f.close()
        return 2

    try:
        csv_files = find_csv_files(args.input_dir)
    except Exception as e:
        log_message(f'[ERR] {e}', to_stderr=True)
        log_f.close()
        return 3

    if not csv_files:
        log_message(f'[ERR] 未在 {args.input_dir} 中找到 CSV 文件', to_stderr=True)
        log_f.close()
        return 3

    log_message(f'✓ 找到 {len(csv_files)} 个 CSV 文件')
    for csv_file in csv_files:
        log_message(f'  - {os.path.relpath(csv_file, args.input_dir)}')
    log_message('')

    repair_hint = os.path.relpath(os.path.join(_project_root, 'scripts', 'repair_encodings.py'), _project_root)
    enforce_utf8 = not args.allow_non_utf8

    total_records = 0
    total_errors = 0
    file_stats = []
    all_data: List[Dict] = []

    for csv_file in csv_files:
        try:
            rel_path = os.path.relpath(csv_file, args.input_dir)
            encoding = detect_file_encoding(csv_file)
            if enforce_utf8:
                encoding = ensure_utf8_file(csv_file, repair_hint)
            log_message(f'处理: {rel_path} [{encoding}]')

            objects, errors = csv_to_json_objects(
                csv_file,
                template,
                delimiter=args.delimiter,
                encoding_hint=encoding,
                enforce_utf8=enforce_utf8,
                repair_hint=repair_hint,
            )

            all_data.extend(objects)
            total_records += len(objects)
            total_errors += errors
            file_stats.append({'file': rel_path, 'encoding': encoding, 'records': len(objects), 'errors': errors})
            log_message(f'  ✓ 成功转换 {len(objects)} 条记录' + (f', {errors} 条错误' if errors > 0 else ''))
        except Exception as e:
            log_message(f'  [ERR] 处理失败: {e}', to_stderr=True)
            total_errors += 1
            log_f.write(f'    详细错误: {repr(e)}\n')
            log_f.flush()

    extra_entries = parse_extra_dataset_args(args.extra_json)
    if extra_entries:
        log_message('')
        log_message('附加数据集 (用于防止遗忘推理能力):')
        for name, path in extra_entries:
            try:
                records = load_json_or_jsonl(path, enforce_utf8=enforce_utf8, repair_hint=repair_hint)
                all_data.extend(records)
                log_message(f'  ✓ {name}: {len(records)} 条记录 ({os.path.relpath(path, _project_root)})')
                file_stats.append({'file': os.path.relpath(path, _project_root), 'encoding': 'utf-8', 'records': len(records), 'errors': 0})
                total_records += len(records)
            except Exception as e:
                log_message(f'  [ERR] 无法加载附加数据集 {name}: {e}', to_stderr=True)
                total_errors += 1

    log_message('')
    log_message('正在写入 JSON 文件...')
    try:
        with open(args.output, 'w', encoding='utf-8') as out_f:
            json.dump(all_data, out_f, ensure_ascii=False, indent=2)
        log_message(f'✓ JSON 文件已生成: {args.output}')
    except Exception as e:
        log_message(f'[ERR] 写入 JSON 文件失败: {e}', to_stderr=True)
        log_f.close()
        return 4

    if args.write_dataset_info:
        dataset_info_path = args.dataset_info_path
        if os.path.exists(dataset_info_path) and not args.overwrite_dataset_info:
            log_message(f'[ERR] dataset_info 已存在且未允许覆盖: {dataset_info_path}', to_stderr=True)
            log_f.close()
            return 5

        dataset_info = build_dataset_info(args.dataset_name, args.output, extra_entries)
        try:
            with open(dataset_info_path, 'w', encoding='utf-8') as f:
                json.dump(dataset_info, f, ensure_ascii=False, indent=2)
            log_message(f'✓ 已生成 dataset_info: {dataset_info_path}')
        except Exception as e:
            log_message(f'[ERR] 写入 dataset_info 失败: {e}', to_stderr=True)
            log_f.close()
            return 6

    log_message('')
    log_message('=' * 50)
    log_message('处理完成！')
    log_message(f'  总输入文件数: {len(csv_files)}')
    log_message(f'  总成功记录数: {total_records}')
    log_message(f'  总错误记录数: {total_errors}')
    log_message(f'  输出文件: {args.output}')
    log_message('=' * 50)

    log_message('')
    log_message('详细统计:')
    for stat in file_stats:
        log_message(f"  {stat['file']:<50} [{stat['encoding']:<12}] {stat['records']:>8} 条" + (f" ({stat['errors']} 错)" if stat['errors'] > 0 else ''))

    log_f.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
