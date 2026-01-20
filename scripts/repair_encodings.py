#!/usr/bin/env python3
"""Normalize file encodings (default to UTF-8) across a directory tree.

Features:
  - Detects source encoding using simple BOM/heuristic checks
  - Converts files to a target encoding (UTF-8 by default)
  - Optional dry-run and backup support
  - Switches to streaming mode for large files to avoid high memory usage

Examples:
  # Dry-run under raw_dataset/csvs
  python3 scripts/repair_encodings.py --root raw_dataset/csvs --dry-run

  # Convert in-place with backups and stream for files >20MB
  python3 scripts/repair_encodings.py --root raw_dataset/csvs --backup --stream-threshold-mb 20
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

_here = os.path.abspath(os.path.dirname(__file__))
_project_root = os.path.abspath(os.path.join(_here, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.encoding import detect_encoding, switch_encoding, switch_encoding_stream


def normalize_encoding(name: Optional[str]) -> str:
    return (name or '').replace('-', '').lower()


def detect_file_encoding(path: str) -> str:
    with open(path, 'rb') as f:
        # For repair script, we can afford reading a bit more for accuracy
        # or just read the whole thing if it's not massive, but let's stick to a large buffer
        # detect_encoding already handles the truncation.
        data = f.read(1024 * 1024) # 1MB is plenty for detection
    return detect_encoding(data)


def iter_files(root: str, exts: Optional[Iterable[str]]) -> List[str]:
    if os.path.isfile(root):
        return [root]

    results: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if exts and not fn.lower().endswith(tuple(exts)):
                continue
            results.append(os.path.join(dirpath, fn))
    return sorted(results)


def convert_file(path: str, target: str, use_stream: bool, stream_threshold: int, backup: bool) -> Tuple[str, bool]:
    src_enc = detect_file_encoding(path)
    if normalize_encoding(src_enc) == normalize_encoding(target):
        return src_enc, False

    if backup:
        bak = path + '.bak'
        try:
            shutil.copy2(path, bak)
            print(f'备份: {path} -> {bak}')
        except Exception as e:
            print(f'[WARN] 无法备份 {path}: {e}')

    size = os.path.getsize(path)
    effective_stream = use_stream or size > stream_threshold
    if effective_stream:
        src_enc, changed = switch_encoding_stream(path, target)
    else:
        src_enc, changed = switch_encoding(path, target)
    return src_enc, changed


def main() -> int:
    parser = argparse.ArgumentParser(description='Repair dataset file encodings to a target encoding (UTF-8 by default).')
    parser.add_argument('--root', '-r', default=os.path.join(_project_root, 'raw_dataset', 'csvs'), help='Root directory or single file to process.')
    parser.add_argument('--target', '-t', default='utf-8', help='Target encoding (default: utf-8).')
    parser.add_argument('--dry-run', action='store_true', help='Only detect and print encodings without modifying files.')
    parser.add_argument('--backup', action='store_true', help='Create .bak backups before modifying files.')
    parser.add_argument('--stream', action='store_true', help='Force streaming conversion.')
    parser.add_argument('--stream-threshold-mb', type=int, default=20, help='File size threshold (MB) to auto-enable streaming (default: 20).')
    parser.add_argument('--exts', default='.csv,.json,.jsonl,.txt', help='Comma-separated extensions to include. Empty string = all files.')
    args = parser.parse_args()

    exts = tuple(x.strip().lower() for x in args.exts.split(',')) if args.exts else None
    stream_threshold = args.stream_threshold_mb * 1024 * 1024

    files = iter_files(args.root, exts)
    if not files:
        print('未找到匹配文件')
        return 0

    converted = 0
    for idx, path in enumerate(files, 1):
        try:
            rel = os.path.relpath(path, args.root)
        except Exception:
            rel = path

        if args.dry_run:
            src_enc = detect_file_encoding(path)
            print(f'[DRY] {rel}: {src_enc} -> {args.target}')
            continue

        try:
            src_enc, changed = convert_file(path, args.target, args.stream, stream_threshold, args.backup)
            if changed:
                converted += 1
                print(f'[{idx}/{len(files)}] {rel}: {src_enc} -> {args.target} ✓')
            else:
                print(f'[{idx}/{len(files)}] {rel}: 已是 {args.target} 编码，跳过')
        except Exception as e:
            print(f'[ERR] 处理失败 {rel}: {e}')

    print('\n完成. 总计: {}, 转换: {}, 跳过: {}'.format(len(files), converted, len(files) - converted))
    return 0


if __name__ == '__main__':
    sys.exit(main())
