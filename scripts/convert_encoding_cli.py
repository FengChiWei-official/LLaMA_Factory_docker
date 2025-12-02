#!/usr/bin/env python3
"""批量文件编码检测与转换 CLI

用法示例：
  # dry-run 只检测并打印，不修改文件
  python3 scripts/convert_encoding_cli.py --root medical_ds/samples --target utf-8 --dry-run

  # 真正执行转换并创建备份（.bak）
  python3 scripts/convert_encoding_cli.py --root medical_ds/samples --target utf-8 --backup
"""

import argparse
import os
import shutil
import sys
from typing import Optional

# Ensure project root is importable so the script can be run without setting PYTHONPATH
_here = os.path.abspath(os.path.dirname(__file__))
_project_root = os.path.abspath(os.path.join(_here, '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from utils.encoding import switch_encoding, switch_encoding_stream


def detect_encoding(path: str) -> str:
    """复制项目中 switch_encoding 的检测策略，返回检测到的编码（字符串）。"""
    with open(path, 'rb') as f:
        data = f.read()

    boms = [
        (b'\xff\xfe\x00\x00', 'utf-32-le'),
        (b'\x00\x00\xfe\xff', 'utf-32-be'),
        (b'\xff\xfe', 'utf-16-le'),
        (b'\xfe\xff', 'utf-16-be'),
        (b'\xef\xbb\xbf', 'utf-8-sig'),
    ]

    src_enc: Optional[str] = None
    for bom, enc in boms:
        if data.startswith(bom):
            src_enc = enc
            break

    if not src_enc:
        try:
            data.decode('utf-8')
            src_enc = 'utf-8'
        except Exception:
            candidates = ('utf-8', 'gb18030', 'gbk', 'big5', 'iso-8859-1', 'cp1252')
            for enc in candidates:
                try:
                    data.decode(enc)
                    src_enc = enc
                    break
                except Exception:
                    continue
            else:
                src_enc = 'latin1'

    return src_enc


def iterate_files(root: str, exts):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if exts and not fn.lower().endswith(exts):
                continue
            yield os.path.join(dirpath, fn)


def main():
    p = argparse.ArgumentParser(description='批量检测并转换文件编码')
    p.add_argument('--root', '-r', required=True, help='根目录或单个文件路径')
    p.add_argument('--target', '-t', default='utf-8', help='目标编码 (默认 utf-8)')
    p.add_argument('--dry-run', action='store_true', help='只检测并打印，不做实际修改')
    p.add_argument('--backup', action='store_true', help='在修改前创建 .bak 备份')
    p.add_argument('--stream', action='store_true', help='强制使用流式转换（适用于大文件）')
    p.add_argument('--stream-threshold-mb', type=int, default=10, help='文件大小超过此阈值(单位MB)时自动使用流式转换，默认 10MB')
    p.add_argument('--exts', default='.txt,.csv,.json,.md,.py', help='逗号分隔的扩展名，空表示全部文件')
    args = p.parse_args()

    root = args.root
    target = args.target
    dry_run = args.dry_run
    backup = args.backup
    exts = tuple(x.strip().lower() for x in args.exts.split(',')) if args.exts else None
    stream_flag = args.stream
    stream_threshold = args.stream_threshold_mb * 1024 * 1024

    paths = []
    if os.path.isfile(root):
        paths = [root]
    else:
        paths = list(iterate_files(root, exts))

    if not paths:
        print('未找到匹配文件')
        return

    for path in paths:
        try:
            src = detect_encoding(path)
        except Exception as e:
            print(f'[ERR] 无法检测 {path}: {e}')
            continue

        if src is None:
            src = 'unknown'

        if dry_run:
            print(f'[DRY] {path}: {src} -> {target}')
            continue

        # 备份
        if backup:
            bak = path + '.bak'
            try:
                shutil.copy2(path, bak)
                print(f'备份: {path} -> {bak}')
            except Exception as e:
                print(f'[WARN] 备份失败: {path}: {e}')

        # 真正转换：根据大小或用户要求选择流式或一次性转换
        try:
            use_stream = stream_flag or (os.path.getsize(path) > stream_threshold)
            if use_stream:
                src_enc, changed = switch_encoding_stream(path, target)
            else:
                src_enc, changed = switch_encoding(path, target)
            print(f'{path}: {src_enc} -> {target} (changed={changed})')
        except Exception as e:
            print(f'[ERR] 转换失败 {path}: {e}')


if __name__ == '__main__':
    main()
