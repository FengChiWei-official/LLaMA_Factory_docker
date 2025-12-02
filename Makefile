# Makefile：方便调用编码转换脚本

.PHONY: convert-dry convert-run

# 可通过环境变量/命令行变量覆盖默认值，例如：
# make convert-dry ROOT=medical_ds TARGET=utf-8
ROOT ?= medical_ds/samples
TARGET ?= utf-8

convert-dry:
	python3 scripts/convert_encoding_cli.py --root $(ROOT) --target $(TARGET) --dry-run

convert-run:
	python3 scripts/convert_encoding_cli.py --root $(ROOT) --target $(TARGET) --backup
